"""定时任务 — 超时订单自动取消 + 物流状态自动推进。

超时取消（每 5 分钟）：
  - 扫描超时未支付订单，逐条 FOR UPDATE + 取消 + 回滚库存 + 分布式锁

物流推进（每 30 秒）：
  - 扫描未完成的物流记录，每 1 分钟推进一个节点
  - 5 分钟完成完整配送流程：已揽件 → 运输中 → 运输中 → 派送中 → 已签收
"""

import json
from datetime import datetime, timedelta

from shop_shared.common.logger import get_logger
from shop_shared.infrastructure.database import get_connection, release_connection
from shop_shared.infrastructure.redis_client import get_redis
from psycopg2 import extras

logger = get_logger("scheduler")

LOCK_KEY = "scheduler:cancel_timeout_orders"
LOCK_TIMEOUT = 300

# ── 物流节点定义（按分钟推进） ──

LOGISTICS_NODES = [
    (0, "picked_up", "深圳仓库"),
    (1, "in_transit", "深圳集散中心"),
    (2, "in_transit", "广州中转"),
    (3, "out_for_delivery", "派送中"),
    (5, "delivered", "您的手中"),
]

# 英文状态 → 中文（timeline 节点用中文）
LOGISTICS_NODES_CN = {
    "picked_up": "已揽件",
    "in_transit": "运输中",
    "out_for_delivery": "派送中",
    "delivered": "已签收",
}


def advance_logistics():
    """物流状态推进：每 30s 调度，每分钟推进一个节点，5 分钟送达。

    查找所有未完成的物流记录，根据创建时间计算应处的节点并更新。
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        # 查找所有未送达的物流记录
        cur.execute("""
            SELECT id, order_id, status, current_location, created_at, timeline
            FROM shop.logistics_records
            WHERE status != 'delivered'
        """)
        records = cur.fetchall()
        if not records:
            return

        for rec in records:
            now = datetime.now()
            created = rec["created_at"].replace(tzinfo=None) if rec["created_at"] else now
            elapsed_minutes = (now - created).total_seconds() / 60.0

            # 确定应处的节点索引
            target_idx = -1
            for idx, (minute, status, location) in enumerate(LOGISTICS_NODES):
                if elapsed_minutes >= minute and (idx == len(LOGISTICS_NODES) - 1 or elapsed_minutes < LOGISTICS_NODES[idx + 1][0]):
                    target_idx = idx
                    break
            if target_idx < 0:
                continue

            _, target_status, target_location = LOGISTICS_NODES[target_idx]

            # 只有状态或位置变化时才更新
            if rec["status"] != target_status or rec["current_location"] != target_location:
                # 解析已有 timeline
                existing_timeline = []
                if rec.get("timeline"):
                    raw = rec["timeline"]
                    if isinstance(raw, str):
                        existing_timeline = json.loads(raw)
                    elif isinstance(raw, list):
                        existing_timeline = raw

                # 判断是否为旧格式（已预置全部5个节点）→ 不追加，只更新状态
                is_old_format = len(existing_timeline) >= 5

                if not is_old_format:
                    new_node = {
                        "time": now.strftime('%H:%M'),
                        "status": LOGISTICS_NODES_CN.get(target_status, target_status),
                        "location": target_location,
                    }
                    existing_timeline.append(new_node)
                    updated_timeline_json = json.dumps(existing_timeline, ensure_ascii=False)
                else:
                    updated_timeline_json = json.dumps(existing_timeline, ensure_ascii=False)

                cur.execute("""
                    UPDATE shop.logistics_records
                    SET status = %s, current_location = %s, timeline = %s, updated_at = NOW()
                    WHERE id = %s
                """, (target_status, target_location, updated_timeline_json, rec["id"]))
                logger.info(f"[物流推进] 订单 {rec['order_id']} → {LOGISTICS_NODES_CN.get(target_status,target_status)} @ {target_location}")

        conn.commit()
    except Exception as e:
        logger.error(f"[物流推进] 出错: {e}")
    finally:
        release_connection(conn)


def cancel_timeout_orders():
    """扫描并取消超时未支付订单（APScheduler 每 5 分钟调用）。"""
    # 1. 获取分布式锁（防止多实例重复执行）
    redis_client = get_redis()
    if redis_client:
        try:
            acquired = redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TIMEOUT)
            if not acquired:
                logger.info("[Scheduler] 未获取到分布式锁，跳过本次执行")
                return
        except Exception as e:
            logger.warning("[Scheduler] Redis 获取锁失败: %s，继续执行", e)

    try:
        logger.info("[Scheduler] 开始扫描超时订单...")

        # 2. 查询超时的 pending 订单
        conn = get_connection()
        try:
            cur = conn.cursor(cursor_factory=extras.RealDictCursor)
            cur.execute("""
                SELECT id 
                FROM shop.orders 
                WHERE status = 'pending' 
                  AND created_at < NOW() - INTERVAL '5 minutes'
            """)
            timeout_orders = cur.fetchall()
            cur.close()
        finally:
            release_connection(conn)

        if not timeout_orders:
            logger.info("[Scheduler] 本轮未发现超时订单")
            return

        logger.info(f"[Scheduler] 发现 {len(timeout_orders)} 个超时订单，开始处理...")

        # 3. 逐条处理（每条独立事务）
        success_count = 0
        fail_count = 0

        for order in timeout_orders:
            order_id = order["id"]
            try:
                _cancel_single_order(order_id)
                success_count += 1
                logger.info(f"[Scheduler] 订单 {order_id} 已自动取消")
            except Exception as e:
                fail_count += 1
                logger.error(f"[Scheduler] 订单 {order_id} 取消失败: {e}")

        logger.info(f"[Scheduler] 本轮处理完成：成功 {success_count}，失败 {fail_count}")

    finally:
        # 4. 释放分布式锁
        if redis_client:
            try:
                redis_client.delete(LOCK_KEY)
                logger.info("[Scheduler] 分布式锁已释放")
            except Exception as e:
                logger.warning("[Scheduler] Redis 释放锁失败: %s", e)


def _cancel_single_order(order_id: int):
    """取消单个订单（独立事务）：FOR UPDATE → 校验 → 更新 → 回滚库存。"""
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # a. FOR UPDATE 锁定订单
        cur.execute("""
            SELECT id, status 
            FROM shop.orders 
            WHERE id = %s 
            FOR UPDATE
        """, (order_id,))
        order = cur.fetchone()

        if not order:
            logger.warning(f"[Scheduler] 订单 {order_id} 不存在")
            conn.rollback()
            return

        # b. 二次校验 status 仍为 pending
        if order["status"] != "pending":
            logger.info(f"[Scheduler] 订单 {order_id} 状态已变更为 {order['status']}，跳过")
            conn.rollback()
            return

        # c. 查询订单明细（用于回滚库存）
        cur.execute("""
            SELECT product_id, quantity 
            FROM shop.order_items 
            WHERE order_id = %s
        """, (order_id,))
        items = cur.fetchall()

        # d. 回滚库存
        for item in items:
            cur.execute("""
                UPDATE shop.products 
                SET stock = stock + %s 
                WHERE id = %s
            """, (item["quantity"], item["product_id"]))
            logger.info(f"[Scheduler] 订单 {order_id} 回滚库存: 商品 {item['product_id']} +{item['quantity']}")

        # e. 更新订单状态为 cancelled
        cur.execute("""
            UPDATE shop.orders 
            SET status = 'cancelled', 
                cancelled_at = NOW() 
            WHERE id = %s
        """, (order_id,))

        conn.commit()
        logger.info(f"[Scheduler] 订单 {order_id} 已取消并回滚库存")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)

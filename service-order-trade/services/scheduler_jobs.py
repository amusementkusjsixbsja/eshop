"""定时任务 — 超时订单自动取消。

★ 小C：实现此函数，替换 print 为真实的数据库操作。

流程（对照需求文档 §8.5）：
  1. SELECT id FROM shop.orders WHERE status='pending' AND created_at < NOW() - INTERVAL '30 min'
  2. 逐条执行（每条独立事务）：
     a. FOR UPDATE 锁定订单
     b. 二次校验 status 仍为 pending
     c. UPDATE status = cancelled
     d. 回滚库存：UPDATE shop.products SET stock = stock + quantity
     e. COMMIT
  3. 记录取消日志

调度配置（在 main.py 中）：每 5 分钟触发
"""

from shop_shared.common.logger import get_logger
from shop_shared.infrastructure.database import get_connection, release_connection
from shop_shared.infrastructure.redis_client import get_redis
from psycopg2 import extras

logger = get_logger("scheduler")

LOCK_KEY = "scheduler:cancel_timeout_orders"
LOCK_TIMEOUT = 300  # 5 分钟（与调度周期一致）


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

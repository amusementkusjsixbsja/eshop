"""订单业务逻辑层。"""

import json
import random
from typing import Optional
from datetime import datetime, timedelta

from psycopg2 import extras

from shop_shared.infrastructure.database import get_connection, release_connection, get_cursor
from shop_shared.common.exceptions import BusinessError, NotFoundError

# 支付配置常量
PAYMENT_METHODS = {"wechat", "alipay", "card", "balance", "mock"}


def generate_transaction_no() -> str:
    """生成支付流水号：TXN + 时间戳 + 4位随机数"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = f"{random.randint(0, 9999):04d}"
    return f"TXN{ts}{rand}"


def create_order(user_id: int, address: str) -> dict:
    """创建订单（核心事务：锁库存→扣减→创订单→清购物车→快照）。"""
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("""
            SELECT ci.product_id, ci.quantity, p.price, p.stock, p.name
            FROM shop.cart_items ci
            JOIN shop.products p ON ci.product_id = p.id
            WHERE ci.user_id = %s
        """, (user_id,))
        cart_items = cur.fetchall()

        if not cart_items:
            raise BusinessError("购物车为空")

        product_ids = [item["product_id"] for item in cart_items]

        cur.execute("SELECT id, stock FROM shop.products WHERE id = ANY(%s) FOR UPDATE", (product_ids,))
        stocks = {row["id"]: row["stock"] for row in cur.fetchall()}

        total_amount = 0
        order_items_snapshot = []
        for item in cart_items:
            if item["quantity"] > stocks[item["product_id"]]:
                raise BusinessError(f"商品 [{item['name']}] 库存不足")
            total_amount += item["price"] * item["quantity"]
            order_items_snapshot.append({
                "product_id": item["product_id"],
                "product_name": item["name"],
                "price": item["price"],
                "quantity": item["quantity"],
            })

        for item in cart_items:
            cur.execute(
                "UPDATE shop.products SET stock = stock - %s WHERE id = %s AND stock >= %s",
                (item["quantity"], item["product_id"], item["quantity"])
            )

        cur.execute("""
            INSERT INTO shop.orders (user_id, total_amount, address)
            VALUES (%s, %s, %s) RETURNING id, created_at
        """, (user_id, total_amount, address))
        order_row = cur.fetchone()
        order_id = order_row["id"]
        created_at = order_row["created_at"]

        for item in order_items_snapshot:
            cur.execute("""
                INSERT INTO shop.order_items (order_id, product_id, product_name, price, quantity)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, item["product_id"], item["product_name"], item["price"], item["quantity"]))

        cur.execute("DELETE FROM shop.cart_items WHERE user_id = %s", (user_id,))

        conn.commit()
        return {
            "id": order_id,
            "total_amount": total_amount,
            "status": "pending",
            "created_at": created_at,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)


def get_user_orders(user_id: int, status: Optional[str] = None, page: int = 1, size: int = 20) -> tuple:
    """获取用户订单列表（支持状态筛选、分页）。"""
    with get_cursor() as cur:
        offset = (page - 1) * size
        if status:
            cur.execute("""
                SELECT id, total_amount, status, address, created_at, paid_at, cancelled_at
                FROM shop.orders
                WHERE user_id = %s AND status = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, status, size, offset))
        else:
            cur.execute("""
                SELECT id, total_amount, status, address, created_at, paid_at, cancelled_at
                FROM shop.orders
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, size, offset))
        orders = cur.fetchall()

        cur.execute("SELECT COUNT(*) as total FROM shop.orders WHERE user_id = %s AND (%s = '' OR status = %s)",
                    (user_id, status if status else "", status if status else None))
        total = cur.fetchone()["total"]
        return orders, total


def get_order_detail(order_id: int, user_id: int) -> dict:
    """获取订单详情（含订单明细）。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, user_id, total_amount, status, address, created_at, paid_at, cancelled_at
            FROM shop.orders
            WHERE id = %s AND user_id = %s
        """, (order_id, user_id))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")

        cur.execute("""
            SELECT id, product_id, product_name, price, quantity
            FROM shop.order_items
            WHERE order_id = %s
        """, (order_id,))
        items = cur.fetchall()
        order["items"] = items
        return order


def initiate_payment(order_id: int, user_id: int, payment_method: str = "mock") -> dict:
    """发起支付：加锁校验 → 创建 payment_record(status='processing') → 返回流水号。"""
    if payment_method not in PAYMENT_METHODS:
        raise BusinessError(f"不支持的支付方式：{payment_method}")

    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("""
            SELECT id, status, total_amount FROM shop.orders WHERE id = %s AND user_id = %s FOR UPDATE
        """, (order_id, user_id))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["status"] == "paid":
            raise BusinessError("订单已支付")
        if order["status"] == "cancelled":
            raise BusinessError("订单已取消")

        transaction_no = generate_transaction_no()

        cur.execute("""
            INSERT INTO shop.payment_records (order_id, amount, method, status, transaction_no)
            VALUES (%s, %s, %s, 'processing', %s)
            RETURNING id, created_at
        """, (order_id, order["total_amount"], payment_method, transaction_no))
        record = cur.fetchone()

        conn.commit()
        return {
            "payment_id": record["id"],
            "order_id": order_id,
            "status": "processing",
            "transaction_no": transaction_no,
            "created_at": record["created_at"],
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)


def complete_payment(payment_id: int, success: bool, error_message: Optional[str] = None) -> dict:
    """完成支付：加锁 → 更新状态为 success/failed → 更新 order.status → 成功时创建物流。"""
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        cur.execute("""
            SELECT id, order_id, status, amount FROM shop.payment_records WHERE id = %s FOR UPDATE
        """, (payment_id,))
        record = cur.fetchone()
        if not record:
            raise NotFoundError("支付记录不存在")
        if record["status"] != "processing":
            raise BusinessError(f"支付状态已变更，无法完成，当前状态：{record['status']}")

        order_id = record["order_id"]
        new_status = "success" if success else "failed"

        cur.execute("""
            UPDATE shop.payment_records
            SET status = %s, finished_at = NOW(), error_message = %s
            WHERE id = %s
        """, (new_status, error_message, payment_id))

        if success:
            cur.execute("""
                UPDATE shop.orders SET status = 'paid', paid_at = NOW() WHERE id = %s
            """, (order_id,))

            tracking_number = f"SF{order_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"
            estimated_delivery = datetime.now() + timedelta(minutes=5)
            timeline = [
                {"time": datetime.now().strftime('%H:%M'), "status": "已揽件", "location": "深圳仓库"},
            ]
            cur.execute("""
                INSERT INTO shop.logistics_records
                (order_id, tracking_number, carrier, status, current_location, estimated_delivery, timeline)
                VALUES (%s, %s, 'SF-Express', 'picked_up', '深圳仓库', %s, %s)
            """, (order_id, tracking_number, estimated_delivery, json.dumps(timeline)))

        conn.commit()
        return {"payment_id": payment_id, "order_id": order_id, "status": new_status}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)


def get_payment_status(order_id: int, user_id: int) -> dict:
    """查询最新支付记录状态。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT o.id as order_id, o.status as order_status
            FROM shop.orders o WHERE o.id = %s AND o.user_id = %s
        """, (order_id, user_id))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")

        cur.execute("""
            SELECT id, method, status, transaction_no, created_at, finished_at, error_message
            FROM shop.payment_records
            WHERE order_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (order_id,))
        record = cur.fetchone()
        if not record:
            raise NotFoundError("该订单不存在支付记录")

        result = {
            "order_id": order_id,
            "order_status": order["order_status"],
            "payment_id": record["id"],
            "method": record["method"],
            "status": record["status"],
            "transaction_no": record["transaction_no"],
            "created_at": record["created_at"],
        }
        if record["finished_at"]:
            result["finished_at"] = record["finished_at"]
        if record["error_message"]:
            result["error_message"] = record["error_message"]
        return result


def pay_order(order_id: int, user_id: int) -> dict:
    """支付订单（兼容旧接口，内部调用 initiate_payment）。"""
    return initiate_payment(order_id, user_id, "mock")


def cancel_order(order_id: int, user_id: int) -> dict:
    """取消订单（FOR UPDATE + 回滚库存）。"""
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("""
            SELECT id, status FROM shop.orders WHERE id = %s AND user_id = %s FOR UPDATE
        """, (order_id, user_id))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["status"] != "pending":
            raise BusinessError(f"当前状态（{order['status']}）不允许取消")

        cur.execute("""
            SELECT product_id, quantity FROM shop.order_items WHERE order_id = %s
        """, (order_id,))
        order_items = cur.fetchall()

        for item in order_items:
            cur.execute("""
                UPDATE shop.products SET stock = stock + %s WHERE id = %s
            """, (item["quantity"], item["product_id"]))

        cur.execute("""
            UPDATE shop.orders SET status = 'cancelled', cancelled_at = NOW()
            WHERE id = %s RETURNING cancelled_at
        """, (order_id,))
        cancelled_at = cur.fetchone()["cancelled_at"]

        conn.commit()
        return {"id": order_id, "status": "cancelled", "cancelled_at": cancelled_at}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)


def create_order_direct(user_id: int, items: list, address: str) -> dict:
    """AI 对话下单用：items = [{"product_id": 1, "quantity": 2}, ...]"""
    conn = get_connection()
    conn.autocommit = False
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # 校验用户存在
        cur.execute("SELECT id FROM shop.users WHERE id = %s", (user_id,))
        if not cur.fetchone():
            raise NotFoundError("用户不存在")

        # 锁定商品行
        product_ids = [item["product_id"] for item in items]
        cur.execute("SELECT id, price, stock, name FROM shop.products WHERE id = ANY(%s) FOR UPDATE",
                    (product_ids,))
        products = {row["id"]: row for row in cur.fetchall()}

        # 校验库存并构建订单明细
        total_amount = 0
        order_items_snapshot = []
        for item in items:
            product = products.get(item["product_id"])
            if not product:
                raise BusinessError(f"商品 ID {item['product_id']} 不存在")
            if item["quantity"] > product["stock"]:
                raise BusinessError(f"商品 [{product['name']}] 库存不足，无法创建订单")
            total_amount += product["price"] * item["quantity"]
            order_items_snapshot.append({
                "product_id": item["product_id"],
                "product_name": product["name"],
                "price": product["price"],
                "quantity": item["quantity"],
            })

        # 扣减库存
        for item in items:
            cur.execute(
                "UPDATE shop.products SET stock = stock - %s WHERE id = %s",
                (item["quantity"], item["product_id"])
            )

        # 创建订单
        cur.execute("""
            INSERT INTO shop.orders (user_id, total_amount, address)
            VALUES (%s, %s, %s) RETURNING id, created_at
        """, (user_id, total_amount, address))
        order_row = cur.fetchone()
        order_id = order_row["id"]
        created_at = order_row["created_at"]

        # 创建订单明细
        for item in order_items_snapshot:
            cur.execute("""
                INSERT INTO shop.order_items (order_id, product_id, product_name, price, quantity)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, item["product_id"], item["product_name"], item["price"], item["quantity"]))

        conn.commit()
        return {
            "id": order_id,
            "total_amount": total_amount,
            "status": "pending",
            "created_at": created_at,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)

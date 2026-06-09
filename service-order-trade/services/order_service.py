"""订单业务逻辑层。"""

import json
from typing import Optional
from datetime import datetime, timedelta

from psycopg2 import extras

from shop_shared.infrastructure.database import get_connection, release_connection, get_cursor
from shop_shared.common.exceptions import BusinessError, NotFoundError


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


def pay_order(order_id: int, user_id: int) -> dict:
    """支付订单（FOR UPDATE 幂等校验）。"""
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

        cur.execute("""
            UPDATE shop.orders SET status = 'paid', paid_at = NOW() WHERE id = %s RETURNING paid_at
        """, (order_id,))
        paid_at = cur.fetchone()["paid_at"]

        cur.execute("""
            INSERT INTO shop.payment_records (order_id, amount, method)
            VALUES (%s, %s, 'mock')
        """, (order_id, order["total_amount"]))

        tracking_number = f"SF{order_id}{datetime.now().strftime('%Y%m%d%H%M%S')}"
        estimated_delivery = datetime.now() + timedelta(days=3)
        timeline = [
            {"time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status": "picked_up", "location": "深圳仓库"},
            {"time": (datetime.now() + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'), "status": "in_transit", "location": "深圳集散中心"},
            {"time": (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'), "status": "in_transit", "location": "广州中转"},
            {"time": (datetime.now() + timedelta(hours=36)).strftime('%Y-%m-%d %H:%M:%S'), "status": "out_for_delivery", "location": "派送中"},
        ]

        cur.execute("""
            INSERT INTO shop.logistics_records 
            (order_id, tracking_number, carrier, status, current_location, estimated_delivery, timeline)
            VALUES (%s, %s, 'SF-Express', 'picked_up', '深圳仓库', %s, %s)
        """, (order_id, tracking_number, estimated_delivery, json.dumps(timeline)))

        conn.commit()
        return {"id": order_id, "status": "paid", "paid_at": paid_at}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        cur.close()
        release_connection(conn)


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

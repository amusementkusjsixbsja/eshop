"""购物车业务逻辑层。"""

from shop_shared.infrastructure.database import get_cursor
from shop_shared.common.exceptions import BusinessError


def get_cart_items(user_id: int) -> list:
    """获取用户购物车列表。"""
    with get_cursor() as cur:
        cur.execute("""
            SELECT ci.id, ci.product_id, ci.quantity, p.name, p.price, p.stock
            FROM shop.cart_items ci
            JOIN shop.products p ON ci.product_id = p.id
            WHERE ci.user_id = %s
            ORDER BY ci.created_at DESC
        """, (user_id,))
        return cur.fetchall()


def add_to_cart(user_id: int, product_id: int, quantity: int) -> dict:
    """添加商品到购物车（UPSERT，同商品自动叠加数量）。"""
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO shop.cart_items (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, product_id) DO UPDATE
            SET quantity = shop.cart_items.quantity + EXCLUDED.quantity
            RETURNING id, product_id, quantity
        """, (user_id, product_id, quantity))
        return cur.fetchone()


def update_cart_quantity(user_id: int, product_id: int, quantity: int) -> dict:
    """修改购物车商品数量。"""
    with get_cursor() as cur:
        cur.execute("""
            UPDATE shop.cart_items
            SET quantity = %s
            WHERE user_id = %s AND product_id = %s
            RETURNING id, product_id, quantity
        """, (quantity, user_id, product_id))
        result = cur.fetchone()
        if not result:
            raise BusinessError("购物车项不存在")
        return result


def delete_cart_item(user_id: int, product_id: int) -> None:
    """删除购物车商品。"""
    with get_cursor() as cur:
        cur.execute("""
            DELETE FROM shop.cart_items
            WHERE user_id = %s AND product_id = %s
        """, (user_id, product_id))
        if cur.rowcount == 0:
            raise BusinessError("购物车项不存在")

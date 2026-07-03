"""★ 小D：售后管理业务逻辑（管理后台）。

接口说明：
  - list_all_after_sales(page, size, status) — 查看全部售后申请
  - approve_after_sale(after_sale_id) — 审核通过
  - reject_after_sale(after_sale_id)   — 审核拒绝
"""

from shop_shared.infrastructure.database import get_cursor
from shop_shared.common.exceptions import NotFoundError, BusinessError


def list_all_after_sales(page: int = 1, size: int = 20, status: str = None) -> dict:
    """查看全部售后申请（可按状态筛选）。"""
    offset = (page - 1) * size
    with get_cursor() as cur:
        # 统计总数
        if status:
            cur.execute("SELECT COUNT(*) as total FROM shop.after_sale_requests WHERE status = %s", (status,))
        else:
            cur.execute("SELECT COUNT(*) as total FROM shop.after_sale_requests")
        total = cur.fetchone()["total"]

        # 查询列表
        sql = """
            SELECT a.id, a.user_id, a.order_id, a.type, a.reason, a.status,
                   a.created_at, a.updated_at
            FROM shop.after_sale_requests a
        """
        params = []
        if status:
            sql += " WHERE a.status = %s"
            params.append(status)
        sql += " ORDER BY a.created_at DESC LIMIT %s OFFSET %s"
        params.extend([size, offset])
        cur.execute(sql, params)
        items = cur.fetchall()

    return {
        "items": [dict(r) for r in items],
        "total": total,
        "page": page,
        "size": size,
    }


def approve_after_sale(after_sale_id: int) -> dict:
    """审核通过售后申请。"""
    with get_cursor() as cur:
        cur.execute("""
            UPDATE shop.after_sale_requests
            SET status = 'approved', updated_at = NOW()
            WHERE id = %s AND status = 'pending'
            RETURNING id, status, updated_at
        """, (after_sale_id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError("售后申请不存在或已处理")
        return dict(row)


def reject_after_sale(after_sale_id: int) -> dict:
    """审核拒绝售后申请。"""
    with get_cursor() as cur:
        cur.execute("""
            UPDATE shop.after_sale_requests
            SET status = 'rejected', updated_at = NOW()
            WHERE id = %s AND status = 'pending'
            RETURNING id, status, updated_at
        """, (after_sale_id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError("售后申请不存在或已处理")
        return dict(row)

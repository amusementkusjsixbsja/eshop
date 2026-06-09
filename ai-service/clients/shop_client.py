"""ShopInternalClient — 调用 shop-service 内部接口的客户端。

内部接口路由：
  - user-product:8001 — 用户、商品（/internal/users/*, /internal/products/*）
  - order-trade:8002 — 订单、物流、售后（/internal/orders/*, /internal/logistics/*, /internal/after-sales/*）
"""

import os

import httpx

USER_INTERNAL_URL = os.getenv("USER_INTERNAL_URL", "http://user-product:8001/internal")
ORDER_INTERNAL_URL = os.getenv("ORDER_INTERNAL_URL", "http://order-trade:8002/internal")
INTERNAL_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-internal-token")


class ShopInternalClient:
    """shop-service 内部接口同步客户端。"""

    def __init__(self, timeout=5.0):
        self.mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
        if not self.mock_mode:
            self._client = httpx.Client(timeout=timeout)
            self._headers = {"X-Internal-Token": INTERNAL_TOKEN}

    # ─── 订单（order-trade）───

    def get_orders(self, user_id: int, page: int = 1, size: int = 20) -> dict:
        if self.mock_mode:
            return self._mock_orders(user_id)
        return self._get(ORDER_INTERNAL_URL, "/orders", {"user_id": user_id, "page": page, "size": size})

    def get_order_detail(self, order_id: int, user_id: int = None) -> dict:
        if self.mock_mode:
            return {"code": 0, "data": {"id": order_id, "user_id": 1, "total_amount": 1798.00, "status": "paid",
                "address": "广东省深圳市南山区", "created_at": "2026-06-01T10:00:00",
                "paid_at": "2026-06-01T10:05:00", "cancelled_at": None,
                "items": [
                    {"id": 1, "product_id": 1, "product_name": "智能门锁 X1", "price": 1299.00, "quantity": 1},
                    {"id": 2, "product_id": 2, "product_name": "无线耳机 Pro", "price": 499.00, "quantity": 1},
                ]}, "message": "success"}
        return self._get(ORDER_INTERNAL_URL, f"/orders/{order_id}")

    def _mock_orders(self, user_id: int) -> dict:
        return {"code": 0, "data": {"items": [
            {"id": 1001, "user_id": 1, "total_amount": 1798.00, "status": "paid",
             "address": "广东省深圳市南山区", "created_at": "2026-06-01T10:00:00",
             "paid_at": "2026-06-01T10:05:00", "cancelled_at": None,
             "items": [{"id": 1, "product_id": 1, "product_name": "智能门锁 X1", "price": 1299.00, "quantity": 1},
                       {"id": 2, "product_id": 2, "product_name": "无线耳机 Pro", "price": 499.00, "quantity": 1}]},
            {"id": 1002, "user_id": 1, "total_amount": 299.00, "status": "pending",
             "address": "广东省深圳市南山区", "created_at": "2026-06-01T11:00:00",
             "paid_at": None, "cancelled_at": None,
             "items": [{"id": 3, "product_id": 4, "product_name": "智能音箱", "price": 299.00, "quantity": 1}]},
        ], "total": 2, "page": 1, "size": 20}, "message": "success"}

    # ─── 物流（order-trade）───

    def get_logistics(self, user_id: int) -> dict:
        if self.mock_mode:
            return {"code": 0, "data": {"items": [
                {"id": 1, "order_id": 1001, "tracking_number": "SF20260601001",
                 "carrier": "顺丰速运", "status": "in_transit",
                 "current_location": "广州中转中心", "estimated_delivery": "2026-06-04",
                 "timeline": [
                     {"time": "2026-06-01 10:30:00", "status": "已揽件", "location": "深圳仓库"},
                     {"time": "2026-06-01 16:00:00", "status": "运输中", "location": "深圳集散中心"},
                 ]},
            ]}, "message": "success"}
        return self._get(ORDER_INTERNAL_URL, "/logistics", {"user_id": user_id})

    # ─── 售后（order-trade）───

    def get_after_sales(self, user_id: int) -> dict:
        if self.mock_mode:
            return {"code": 0, "data": {"items": []}, "message": "success"}
        return self._get(ORDER_INTERNAL_URL, "/after-sales", {"user_id": user_id})

    # ─── 商品（user-product）───

    def search_products(self, keyword: str, page: int = 1, size: int = 20, user_id: int = None, min_price: float = None, max_price: float = None) -> dict:
        params = {"keyword": keyword, "page": page, "size": size}
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        return self._get(USER_INTERNAL_URL, "/products/search", params)

    def get_product(self, product_id: int) -> dict:
        return self._get(USER_INTERNAL_URL, f"/products/{product_id}")

    # ─── 用户（user-product）───

    def get_user(self, user_id: int) -> dict:
        return self._get(USER_INTERNAL_URL, f"/users/{user_id}")

    # ─── 内部方法 ───

    def _get(self, base_url: str, path: str, params: dict = None) -> dict:
        try:
            url = f"{base_url}{path}"
            r = self._client.get(url, params=params, headers=self._headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"code": -1, "data": {}, "message": f"电商服务不可用: {e}"}

    def close(self):
        self._client.close()

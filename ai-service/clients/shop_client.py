"""ShopInternalClient — 调用 shop-service 内部接口的客户端。

★ 小A：在 AI 服务中通过此客户端获取实时业务数据。

参考：AI服务对接开发指南
"""

import os

import httpx

# 从环境变量读取配置
SHOP_INTERNAL_URL = os.getenv("SHOP_INTERNAL_URL", "http://user-product:8001/internal")
INTERNAL_TOKEN = os.getenv("INTERNAL_API_TOKEN", "dev-internal-token")


class ShopInternalClient:
    """shop-service 内部接口同步客户端。"""

    def __init__(self, timeout: float = 5.0):
        self._client = httpx.Client(timeout=timeout)
        self._headers = {"X-Internal-Token": INTERNAL_TOKEN}

    # ─── 订单 ───

    def get_orders(self, user_id: int, page: int = 1, size: int = 20) -> dict:
        return self._get("/orders", {"user_id": user_id, "page": page, "size": size})

    def get_order_detail(self, order_id: int) -> dict:
        return self._get(f"/orders/{order_id}")

    # ─── 物流 ───

    def get_logistics(self, user_id: int) -> dict:
        return self._get("/logistics", {"user_id": user_id})

    # ─── 售后 ───

    def get_after_sales(self, user_id: int) -> dict:
        return self._get("/after-sales", {"user_id": user_id})

    # ─── 商品 ───

    def search_products(self, keyword: str, page: int = 1, size: int = 20) -> dict:
        return self._get("/products/search", {"keyword": keyword, "page": page, "size": size})

    def get_product(self, product_id: int) -> dict:
        return self._get(f"/products/{product_id}")

    # ─── 用户 ───

    def get_user(self, user_id: int) -> dict:
        return self._get(f"/users/{user_id}")

    # ─── 内部方法 ───

    def _get(self, path: str, params: dict = None) -> dict:
        try:
            url = f"{SHOP_INTERNAL_URL}{path}"
            r = self._client.get(url, params=params, headers=self._headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"code": -1, "data": {}, "message": f"电商服务不可用: {e}"}

    def close(self):
        self._client.close()

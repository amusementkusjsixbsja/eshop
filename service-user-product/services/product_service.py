"""商品业务逻辑层（含缓存操作）。

★ 小B：将 routers/product_router.py 中的逻辑迁移至此。

参考：
  - shop_shared.infrastructure.database.get_cursor() — 数据库查询
  - shop_shared.infrastructure.redis_client.get_cache() / set_cache() — 缓存
"""

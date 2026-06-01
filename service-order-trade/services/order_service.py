"""订单业务逻辑层（待填充）。

★ 小C：将 routers/order_router.py 中的核心事务逻辑迁移至此。

关键方法（需要实现）：
  - create_order(user_id, address) → order  # 事务锁库存 + 扣减 + 创订单 + 清购物车
  - pay_order(order_id, user_id) → order     # 幂等支付
  - cancel_order(order_id, user_id) → order   # 回滚库存
  - get_user_orders(user_id, status) → list
  - get_order_detail(order_id, user_id) → dict
  - cancel_timeout_orders() → int            # 超时订单自动取消

事务管理策略（对照技术方案 §3.3）：
  - 下单/支付/取消：手动事务，conn.autocommit = False
  - 普通查询：get_cursor() 自动事务
  - 定时任务：每单独立事务
"""

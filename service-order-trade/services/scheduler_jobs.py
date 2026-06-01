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

logger = get_logger("scheduler")


def cancel_timeout_orders():
    """扫描并取消超时未支付订单（APScheduler 每 5 分钟调用）。"""
    # TODO: 小C — 替换为真实实现
    logger.info("[Scheduler] 扫描超时订单...")
    # 1. SELECT id FROM shop.orders WHERE status = 'pending' AND created_at < NOW() - INTERVAL '30 minutes'
    # 2. 无结果 → return
    # 3. 有结果 → 逐条 FOR UPDATE + 校验 + 更新 + 回滚库存 + COMMIT
    # 每条独立事务，一单失败不影响其他
    logger.info("[Scheduler] 本轮未发现超时订单")

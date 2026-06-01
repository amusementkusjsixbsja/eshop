# 小C 开发指南 — 购物车与交易服务

## 你的文件夹

```
service-order-trade/  ← 你的专属文件夹（只改这里）
├── main.py                     # FastAPI 入口（已有，一般不用改）
├── requirements.txt            # 依赖
├── Dockerfile                  # 已有
├── routers/
│   ├── cart_router.py          # ★ 需要你实现：购物车 CRUD
│   ├── order_router.py         # ★ 需要你实现：下单/支付/取消（核心业务！）
│   ├── logistics_router.py     # ★ 需要你实现：物流查询
│   ├── after_sale_router.py    # ★ 需要你实现：售后申请/查询
│   └── internal_router.py      # ★ 需要你实现：订单/物流/售后内部接口
└── services/
    ├── cart_service.py         # 业务逻辑放这里
    ├── order_service.py        # 业务逻辑放这里（核心）
    ├── logistics_service.py    # 业务逻辑放这里
    ├── after_sale_service.py   # 业务逻辑放这里
    └── scheduler_jobs.py       # ★ 需要你实现：超时订单自动取消
```

## 你的数据表

| 表 | 权限 | 说明 |
|-----|------|------|
| `shop.cart_items` | **你写** | 购物车 |
| `shop.orders` | **你写** | 订单 |
| `shop.order_items` | **你写** | 订单明细（快照） |
| `shop.payment_records` | **你写** | 支付记录 |
| `shop.logistics_records` | **你读** | 物流数据（init.sql 预置演示数据） |
| `shop.after_sale_requests` | **你写** | 售后申请 |
| `shop.products` | **你读** | 商品库存/价格 |

## 你的接口

| 方法 | 路径 | 说明 | 关键规则 |
|------|------|------|---------|
| GET | `/c-endpoint/cart` | 查看购物车 | JOIN products 获取名称价格 |
| POST | `/c-endpoint/cart` | 添加购物车 | UPSERT 幂等叠加 |
| PUT | `/c-endpoint/cart/{product_id}` | 修改数量 | 不可超库存 |
| DELETE | `/c-endpoint/cart/{product_id}` | 删除 | — |
| POST | `/c-endpoint/orders` | **创建订单** | **事务锁库存 → 扣减 → 创订单 → 清购物车** |
| GET | `/c-endpoint/orders` | 订单列表 | 按状态筛选 + 时间倒序 |
| GET | `/c-endpoint/orders/{id}` | 订单详情 | 含 order_items 明细 |
| POST | `/c-endpoint/orders/{id}/pay` | **支付** | **FOR UPDATE 幂等校验** |
| POST | `/c-endpoint/orders/{id}/cancel` | **取消** | **FOR UPDATE + 回滚库存** |
| GET | `/c-endpoint/logistics/{order_id}` | 查物流 | 预置演示数据 |
| POST | `/c-endpoint/after-sales` | 申请售后 | 仅 paid 订单可申请 |
| GET | `/c-endpoint/after-sales` | 售后列表 | — |

### 内部接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/internal/orders` | 查用户订单 |
| GET | `/internal/orders/{id}` | 订单详情 |
| GET | `/internal/logistics` | 查物流 |
| GET | `/internal/after-sales` | 查售后 |

## 核心业务：下单事务（最重要的代码）

```python
# 这是整个项目最核心的逻辑，必须保证原子性
conn = get_connection()
conn.autocommit = False
try:
    # 1. 获取购物车商品 + 当前价格
    cur.execute("""
        SELECT ci.product_id, ci.quantity, p.price, p.stock, p.name
        FROM shop.cart_items ci
        JOIN shop.products p ON ci.product_id = p.id
        WHERE ci.user_id = %s
    """, (user_id,))
    cart_items = cur.fetchall()

    # 2. FOR UPDATE 锁定商品行（防超卖）
    cur.execute("SELECT id, stock FROM shop.products WHERE id = ANY(%s) FOR UPDATE", (product_ids,))

    # 3. 逐条校验库存
    for item in cart_items:
        if item["quantity"] > item["stock"]:
            raise BusinessError(f"商品 [{item['name']}] 库存不足")

    # 4. 扣减库存
    for item in cart_items:
        cur.execute("UPDATE shop.products SET stock = stock - %s WHERE id = %s AND stock >= %s", ...)

    # 5. 创建订单
    cur.execute("INSERT INTO shop.orders (user_id, total_amount, address) VALUES (%s, %s, %s) RETURNING id", ...)
    order_id = cur.fetchone()["id"]

    # 6. 写入订单明细（快照）
    for item in cart_items:
        cur.execute("INSERT INTO shop.order_items (order_id, product_id, product_name, price, quantity) VALUES (%s, %s, %s, %s, %s)", ...)

    # 7. 清空购物车
    cur.execute("DELETE FROM shop.cart_items WHERE user_id = %s", (user_id,))

    # 8. 提交
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.autocommit = True
    cur.close()
    release_connection(conn)
```

## 订单状态机（必须遵守）

```
pending → paid   (支付)
pending → cancelled (手动取消 / 超时取消)
paid → cancelled  ❌ 禁止
cancelled → pending ❌ 禁止
```

## 定时任务：超时订单自动取消

在 `services/scheduler_jobs.py` 中实现，Scheduler 已注册每 5 分钟执行。
逻辑：
1. `SELECT id FROM shop.orders WHERE status='pending' AND created_at < NOW() - INTERVAL '30 minutes'`
2. 逐条独立事务：FOR UPDATE → 校验 → 取消 → 回滚库存 → COMMIT

## 开发方式

```bash
# 启动你的服务 + 基础设施
docker compose -f docker/docker-compose.yml up -d postgres redis order-trade

# 验证
curl http://localhost:8002/health
```

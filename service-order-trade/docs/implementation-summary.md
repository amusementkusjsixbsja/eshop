# 购物车与交易服务 - 实现总结

## 项目概述

本服务负责电商平台的购物车、订单、支付、物流和售后业务，是整个系统的核心交易模块。

## 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL
- **认证**: JWT
- **定时任务**: APScheduler

## 已完成的基础设施

### 1. 数据库连接池

- 文件: `shared/shop_shared/infrastructure/database.py`
- 提供 `get_cursor()` 自动事务上下文管理器
- 提供 `get_connection()` / `release_connection()` 手动事务管理

### 2. 认证中间件

- 文件: `shared/shop_shared/middleware/auth.py`
- `get_current_user()`: 从 JWT 解析用户信息 `{"user_id", "email", "role"}`
- `verify_internal_token()`: 内部接口 Token 校验

### 3. 统一异常处理

- 文件: `shared/shop_shared/common/exceptions.py`
- `BusinessError`: 业务规则冲突（库存不足、状态不允许等）
- `NotFoundError`: 资源不存在
- `AuthenticationError`: 认证失败

## 待实现功能清单

### 1. 购物车 CRUD (`routers/cart_router.py`)

| 接口                              | 方法     | 状态   | 说明                   |
| ------------------------------- | ------ | ---- | -------------------- |
| `/c-endpoint/cart`              | GET    | TODO | 查看购物车（JOIN products） |
| `/c-endpoint/cart`              | POST   | TODO | 添加购物车（UPSERT 幂等叠加）   |
| `/c-endpoint/cart/{product_id}` | PUT    | TODO | 修改数量（不可超库存）          |
| `/c-endpoint/cart/{product_id}` | DELETE | TODO | 删除购物车项               |

### 2. 订单管理 (`routers/order_router.py`) - 核心业务

| 接口                               | 方法   | 状态   | 说明                           |
| -------------------------------- | ---- | ---- | ---------------------------- |
| `/c-endpoint/orders`             | POST | TODO | **创建订单（事务：锁库存→扣减→创订单→清购物车）** |
| `/c-endpoint/orders`             | GET  | TODO | 订单列表（状态筛选 + 分页）              |
| `/c-endpoint/orders/{id}`        | GET  | TODO | 订单详情（含 order\_items）         |
| `/c-endpoint/orders/{id}/pay`    | POST | TODO | **支付（FOR UPDATE 幂等校验）**      |
| `/c-endpoint/orders/{id}/cancel` | POST | TODO | **取消（FOR UPDATE + 回滚库存）**    |

### 3. 物流查询 (`routers/logistics_router.py`)

| 接口                                 | 方法  | 状态   | 说明                      |
| ---------------------------------- | --- | ---- | ----------------------- |
| `/c-endpoint/logistics/{order_id}` | GET | TODO | 查询物流状态（init.sql 预置演示数据） |

### 4. 售后申请 (`routers/after_sale_router.py`)

| 接口                        | 方法   | 状态   | 说明              |
| ------------------------- | ---- | ---- | --------------- |
| `/c-endpoint/after-sales` | POST | TODO | 申请售后（仅 paid 订单） |
| `/c-endpoint/after-sales` | GET  | TODO | 查询售后列表          |

### 5. 内部接口 (`routers/internal_router.py`)

| 接口                      | 方法  | 状态   | 说明     |
| ----------------------- | --- | ---- | ------ |
| `/internal/orders`      | GET | TODO | 查询用户订单 |
| `/internal/orders/{id}` | GET | TODO | 查询订单详情 |
| `/internal/logistics`   | GET | TODO | 查询物流   |
| `/internal/after-sales` | GET | TODO | 查询售后   |

### 6. 定时任务 (`services/scheduler_jobs.py`)

| 任务                      | 调度   | 状态   | 说明                |
| ----------------------- | ---- | ---- | ----------------- |
| `cancel_timeout_orders` | 每5分钟 | TODO | 超时订单自动取消（30分钟未支付） |

## 核心业务流程图

### 下单事务（最重要）

```
START TRANSACTION
    ├─ 1. 获取购物车商品 + 当前价格
    ├─ 2. FOR UPDATE 锁定商品行（防超卖）
    ├─ 3. 校验库存 >= 购买数量
    ├─ 4. 扣减库存
    ├─ 5. 创建订单（INSERT orders）
    ├─ 6. 写入订单明细快照（INSERT order_items）
    ├─ 7. 清空购物车（DELETE cart_items）
    └─ 8. COMMIT / ROLLBACK(失败时)
```

### 订单状态机

```
pending → paid       (支付成功)
pending → cancelled  (手动取消 / 超时自动取消)
paid → cancelled     ❌ 禁止（本期不支持退款）
```

## 数据库表结构

### 已定义的表

| 表名                         | 权限 | 说明         |
| -------------------------- | -- | ---------- |
| `shop.cart_items`          | 读写 | 购物车表       |
| `shop.orders`              | 读写 | 订单表        |
| `shop.order_items`         | 读写 | 订单明细快照     |
| `shop.payment_records`     | 读写 | 支付记录表      |
| `shop.logistics_records`   | 只读 | 物流数据（预置演示） |
| `shop.after_sale_requests` | 读写 | 售后申请表      |
| `shop.products`            | 只读 | 商品库存/价格    |

### orders 表关键字段

- `status`: pending / paid / cancelled
- `total_amount`: numeric(10,2)
- `paid_at`: 支付时间（支付后填充）
- `cancelled_at`: 取消时间（取消后填充）

## 开发与验证

```bash
# 启动服务
docker compose -f docker/docker-compose.yml up -d postgres redis order-trade

# 健康检查
curl http://localhost:8002/health

# 日志查看
docker compose -f docker/docker-compose.yml logs -f order-trade
```

## 实现优先级建议

1. **高优先级**：购物车 CRUD、订单创建（事务）、支付、取消
2. **中优先级**：订单列表/详情、物流查询、售后申请
3. **低优先级**：内部接口、定时任务


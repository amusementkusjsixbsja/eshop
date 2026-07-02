# 小C — 模拟支付 + 对话下单（service-order-trade）

## 模块概述

负责 `service-order-trade` 服务的支付状态机重构和 AI 内部下单接口开发。

---

## 一、核心改动

### 1.1 支付状态机重构

**文件：** `services/order_service.py`

将原有的 `pay_order()` 拆分为三个函数：

| 函数名 | 职责 |
|--------|------|
| `initiate_payment(order_id, user_id, payment_method)` | 加锁校验 → 创建 `payment_record(status='processing')` + 生成 `transaction_no` → 返回 |
| `complete_payment(payment_id, success, error_message)` | 加锁 → 更新状态为 `success`/`failed` → 更新 `order.status` → 成功时创建物流 |
| `get_payment_status(order_id, user_id)` | 查询最新支付记录状态 |

**支付配置常量：**
```python
PAYMENT_METHODS = {"wechat", "alipay", "card", "balance", "mock"}
```

- 不在集合内的 `payment_method` 返回 400 错误
- 失败时订单 status 保持 `'pending'`，用户可重新发起支付

**`transaction_no` 格式：** `TXN` + 年月日时分秒 + 4位随机数（如 `TXN20260621143025A7B2`）

---

### 1.2 AI 内部下单接口

**文件：** `routers/internal_router.py`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/internal/orders/create` | POST | 接受 `{user_id, items, address}`，调用 `create_order_direct()` |

**文件：** `services/order_service.py`

```python
def create_order_direct(user_id: int, items: list, address: str) -> dict
```

- `items = [{"product_id": 1, "quantity": 2}, ...]`
- 事务处理：锁定商品 → 校验库存 → 扣减 → 创建订单+明细
- 订单 status 为 `'pending'`
- 库存不足返回 `code=400`，提示"库存不足，无法创建订单"
- 无 JWT 鉴权，只需校验 `user_id` 有效

---

### 1.3 支付轮询接口

**文件：** `routers/order_router.py`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/orders/{id}/payment` | GET | 调用 `get_payment_status`，供前端轮询支付结果 |

- 无支付记录时返回 404

---

### 1.4 支付模拟定时任务

**文件：** `services/scheduler_jobs.py`

```python
PAYMENT_DELAY_MIN_SECONDS = 1
PAYMENT_DELAY_MAX_SECONDS = 3
PAYMENT_FAILURE_RATE = 0.05

def process_payments():
    """扫描 status='processing' 的支付记录，模拟处理"""
```

- 每 3 秒执行一次
- 根据 `created_at` 判断是否超过模拟延迟（1-3秒随机）
- 95% 标记为 `success`，5% 标记为 `failed`
- 成功时：更新 `order.status='paid'` + 调用 `logistics_service.create_logistics(order_id)` 创建物流

**文件：** `main.py`

在 `_register_scheduler_jobs()` 中注册 `process_payments`，interval=3秒

---

## 二、接口响应格式

### POST /c-endpoint/orders/{id}/pay

**Request:**
```json
{"payment_method": "wechat"}
```

**Response (processing):**
```json
{"code": 0, "data": {"payment_id": 1, "status": "processing", "transaction_no": "TXN20260621..."}}
```

### GET /c-endpoint/orders/{id}/payment

**Response:**
```json
{"code": 0, "data": {"status": "success", "method": "wechat", "finished_at": "..."}}
```

### POST /internal/orders/create

**Request:**
```json
{"user_id": 1, "items": [{"product_id": 1, "quantity": 2}], "address": "深圳市南山区科技园"}
```

**Response:**
```json
{"code": 0, "data": {"id": 1024, "total_amount": 2598.00, "status": "pending"}}
```

---

## 三、数据库依赖

`payment_records` 表需新增字段（由小B在 init.sql 处理）：

```sql
ALTER TABLE shop.payment_records ADD COLUMN IF NOT EXISTS transaction_no VARCHAR(100);
ALTER TABLE shop.payment_records ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;
ALTER TABLE shop.payment_records ADD COLUMN IF NOT EXISTS error_message TEXT;
```

---

## 四、验收标准

| 场景 | 预期结果 |
|------|----------|
| 选择支付方式 | 微信/支付宝/银行卡/余额均可发起，显示 processing |
| 支付状态查询 | 3秒内变为 success/failed |
| 支付成功 | 订单变为 paid，物流记录创建 |
| AI 下单 | `/internal/orders/create` 创建 pending 订单 |
| 支付失败 | 订单保持 pending，可重新发起 |

---

## 五、文件改动清单

| 文件 | 操作 |
|------|------|
| `services/order_service.py` | 修改：拆分支付函数 + 新增 `create_order_direct` |
| `routers/order_router.py` | 修改：pay 接口支持 payment_method + 新增 payment 查询接口 |
| `routers/internal_router.py` | 修改：新增 `/internal/orders/create` |
| `services/scheduler_jobs.py` | 修改：新增 `process_payments()` |
| `main.py` | 修改：注册定时任务 |

---

## 六、待确认/依赖项

1. `payment_records` 表字段变更由小B在 init.sql 中处理
2. `create_order_direct` 依赖库存锁定逻辑，可参考现有 `order_service.py` 中的实现

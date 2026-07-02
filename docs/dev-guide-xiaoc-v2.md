# ©️ 小C — 第二轮开发指南：模拟支付 + 对话下单支撑

> **分支：** `feat/xiaoc-payment-order`
> **服务：** `service-order-trade`（端口 8002）
> **依赖：** 无（独立开发）
> **预计工作量：** 5 个文件
> **风险等级：** 🔴 最高（涉及订单核心流程重构）

---

## 一、任务总览

| 序号 | 文件 | 操作 | 说明 |
|:----:|------|:----:|------|
| 1 | `service-order-trade/services/order_service.py` | 修改 | `pay_order()` 拆分为 `initiate_payment()` + `complete_payment()`；新增 `create_order_direct()` |
| 2 | `service-order-trade/routers/order_router.py` | 修改 | 支付接口接受 `payment_method`；新增支付状态查询端点 |
| 3 | `service-order-trade/routers/internal_router.py` | 修改 | 新增 `POST /internal/orders/create` |
| 4 | `service-order-trade/services/scheduler_jobs.py` | 修改 | 新增 `process_payments()` 定时任务 |
| 5 | `service-order-trade/main.py` | 修改 | 注册 `process_payments` 调度任务 |

---

## 二、核心概念

### 支付状态机

```
用户发起支付
    │
    ▼
initiate_payment()
    │
    ├─ 校验订单（未支付、未取消）
    ├─ 行级锁 FOR UPDATE
    ├─ 创建 payment_record (status=processing)
    ├─ 生成 transaction_no
    └─ 返回 {payment_id, status="processing", transaction_no}
        │
        ▼
  ┌─ process_payments() 定时任务（每 3 秒执行）
  │   │
  │   ├─ 扫描 status=processing 的记录
  │   ├─ 判断是否达到模拟延迟（1-3 秒随机）
  │   ├─ 95% → 调用 complete_payment(success=true)
  │   └─  5% → 调用 complete_payment(success=false)
  │
  ▼
complete_payment()
    │
    ├─ 行级锁 FOR UPDATE
    ├─ 更新 payment_record (status=success/failed)
    ├─ 成功时：order.status='paid', paid_at=NOW, 创建物流记录
    ├─ 失败时：order.status 不变，记录 error_message
    └─ 返回结果
```

### 对话下单流程

```
AI 服务调用 POST /internal/orders/create
    │
    ▼
create_order_direct(user_id, items, address)
    │
    ├─ 事务：FOR UPDATE 锁定商品
    ├─ 校验库存充足
    ├─ 扣减库存
    ├─ 创建订单 + 订单明细
    ├─ 返回 {id, total_amount, status, items}
    └─ （不操作购物车）
```

---

## 三、详细实现步骤

### Step 1：重构 `services/order_service.py`

#### 1a. 新增支付配置常量（文件顶部）

```python
# ── 支付配置（v2.0） ──
PAYMENT_METHODS = {"wechat", "alipay", "card", "balance", "mock"}
PAYMENT_DELAY_MIN_SECONDS = 1
PAYMENT_DELAY_MAX_SECONDS = 3
PAYMENT_FAILURE_RATE = 0.05    # 5% 模拟失败率
```

#### 1b. 新增 `initiate_payment()`

```python
def initiate_payment(order_id: int, user_id: int, payment_method: str = "mock") -> dict:
    """发起支付：校验 → 加锁 → 创建 processing 记录。

    Returns:
        {"payment_id": int, "transaction_no": str, "status": "processing"}
    """
    if payment_method not in PAYMENT_METHODS:
        raise BusinessError(f"不支持的支付方式: {payment_method}")

    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # 1. FOR UPDATE 锁定订单
        cur.execute("""
            SELECT id, user_id, total_amount, status
            FROM shop.orders WHERE id = %s FOR UPDATE
        """, (order_id,))
        order = cur.fetchone()
        if not order:
            raise NotFoundError("订单不存在")
        if order["user_id"] != user_id:
            raise BusinessError("无权操作该订单")
        if order["status"] != "pending":
            raise BusinessError(f"订单状态异常: {order['status']}，仅 pending 可支付")

        # 2. 生成交易流水号
        transaction_no = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{order_id}"

        # 3. 创建支付记录 (status=processing)
        cur.execute("""
            INSERT INTO shop.payment_records (order_id, amount, method, status, transaction_no)
            VALUES (%s, %s, %s, 'processing', %s)
            RETURNING id, order_id, amount, method, status, transaction_no, created_at
        """, (order_id, order["total_amount"], payment_method, transaction_no))
        payment = dict(cur.fetchone())

        conn.commit()
        return payment
    except (NotFoundError, BusinessError):
        conn.rollback()
        raise
    finally:
        release_connection(conn)
```

#### 1c. 新增 `complete_payment()`

```python
def complete_payment(payment_id: int, success: bool, error_message: str = None) -> dict:
    """完成支付：更新状态 → 成功时更新订单 + 创建物流。

    被 scheduler 的 process_payments() 调用。
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        # 1. FOR UPDATE 锁定支付记录
        cur.execute("""
            SELECT id, order_id, status FROM shop.payment_records WHERE id = %s FOR UPDATE
        """, (payment_id,))
        payment = cur.fetchone()
        if not payment:
            raise NotFoundError("支付记录不存在")
        if payment["status"] != "processing":
            raise BusinessError(f"支付记录状态异常: {payment['status']}")

        if success:
            # 2a. 支付成功：更新 payment_record + order
            cur.execute("""
                UPDATE shop.payment_records
                SET status = 'success', finished_at = NOW()
                WHERE id = %s
            """, (payment_id,))

            cur.execute("""
                UPDATE shop.orders
                SET status = 'paid', paid_at = NOW()
                WHERE id = %s
            """, (payment["order_id"],))

            # 3a. 创建物流记录
            tracking_no = f"SF{datetime.now().strftime('%Y%m%d')}{payment['order_id']:06d}"
            cur.execute("""
                INSERT INTO shop.logistics_records
                    (order_id, tracking_number, carrier, status, current_location, estimated_delivery)
                VALUES (%s, %s, '顺丰速运', 'picked_up', '深圳仓库',
                        NOW() + INTERVAL '3 days')
            """, (payment["order_id"], tracking_no))
        else:
            # 2b. 支付失败
            cur.execute("""
                UPDATE shop.payment_records
                SET status = 'failed', finished_at = NOW(), error_message = %s
                WHERE id = %s
            """, (error_message or "支付失败", payment_id))

        conn.commit()
        return {"payment_id": payment_id, "status": "success" if success else "failed"}
    except (NotFoundError, BusinessError):
        conn.rollback()
        raise
    finally:
        release_connection(conn)
```

#### 1d. 新增 `get_payment_status()`

```python
def get_payment_status(order_id: int, user_id: int) -> dict:
    """查询订单的最新支付记录状态（供前端轮询）。"""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute("""
            SELECT id, amount, method, status, transaction_no, finished_at, error_message, created_at
            FROM shop.payment_records
            WHERE order_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (order_id,))
        record = cur.fetchone()
        if not record:
            return {"status": "none"}
        return dict(record)
    finally:
        release_connection(conn)
```

#### 1e. 新增 `create_order_direct()`

```python
def create_order_direct(user_id: int, items: list, address: str) -> dict:
    """AI 对话下单：直接创建订单（跳过购物车）。

    items = [{"product_id": 1, "quantity": 2}, ...]
    """
    if not items:
        raise BusinessError("商品列表不能为空")
    if not address or not address.strip():
        raise BusinessError("收货地址不能为空")

    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        total_amount = 0

        # 1. 锁定商品 + 校验库存
        order_items_data = []
        for item in items:
            cur.execute("""
                SELECT id, name, price, stock FROM shop.products WHERE id = %s FOR UPDATE
            """, (item["product_id"],))
            product = cur.fetchone()
            if not product:
                raise NotFoundError(f"商品 {item['product_id']} 不存在")
            if product["stock"] < item["quantity"]:
                raise BusinessError(f"商品「{product['name']}」库存不足（需求{item['quantity']}，剩余{product['stock']}）")

            # 2. 扣减库存
            cur.execute("""
                UPDATE shop.products SET stock = stock - %s WHERE id = %s
            """, (item["quantity"], item["product_id"]))

            subtotal = float(product["price"]) * item["quantity"]
            total_amount += subtotal
            order_items_data.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "price": float(product["price"]),
                "quantity": item["quantity"],
            })

        # 3. 创建订单
        cur.execute("""
            INSERT INTO shop.orders (user_id, total_amount, address, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING id, total_amount, status, created_at
        """, (user_id, total_amount, address.strip()))
        order = dict(cur.fetchone())

        # 4. 创建订单明细
        for oi in order_items_data:
            cur.execute("""
                INSERT INTO shop.order_items (order_id, product_id, product_name, price, quantity)
                VALUES (%s, %s, %s, %s, %s)
            """, (order["id"], oi["product_id"], oi["product_name"], oi["price"], oi["quantity"]))

        # 5. 查询完整明细
        cur.execute("""
            SELECT id, product_id, product_name, price, quantity
            FROM shop.order_items WHERE order_id = %s
        """, (order["id"],))
        order["items"] = [dict(row) for row in cur.fetchall()]

        conn.commit()
        return order
    except (NotFoundError, BusinessError):
        conn.rollback()
        raise
    finally:
        release_connection(conn)
```

#### 1f. 保留旧 `pay_order()` 兼容（可选）

旧 `pay_order()` 函数可以暂时保留作为兼容，但建议直接删除或标记为 `@deprecated`，因为前端和 AI 都会改为调用新流程。

---

### Step 2：修改 `routers/order_router.py`

#### 2a. 新增 Pydantic 模型

```python
class PayOrderRequest(BaseModel):
    payment_method: str = Field(default="mock", description="支付方式")

class CreateOrderDirectRequest(BaseModel):
    items: list[dict] = Field(..., description="商品列表")
    address: str = Field(..., description="收货地址")
```

#### 2b. 修改 `pay_order_handler`

```python
@router.post("/orders/{order_id}/pay")
def pay_order_handler(
    order_id: int,
    req: PayOrderRequest = Body(...),
    user=Depends(get_current_user),
):
    """支付订单（异步：创建 processing 记录，后台处理）。"""
    payment = initiate_payment(order_id, user["id"], req.payment_method)
    return success_response(payment)
```

#### 2c. 新增支付状态查询端点

```python
@router.get("/orders/{order_id}/payment")
def get_payment_handler(
    order_id: int,
    user=Depends(get_current_user),
):
    """查询订单支付状态（供前端轮询）。"""
    status = get_payment_status(order_id, user["id"])
    return success_response(status)
```

---

### Step 3：修改 `routers/internal_router.py`

新增直接下单内部端点：

```python
from pydantic import BaseModel, Field

class DirectCreateOrderRequest(BaseModel):
    user_id: int = Field(..., description="用户 ID")
    items: list[dict] = Field(..., description="商品列表 [{'product_id': 1, 'quantity': 2}]")
    address: str = Field(..., description="收货地址")


@router.post("/orders/create")
def internal_create_order(req: DirectCreateOrderRequest):
    """内部接口：AI 对话下单直接创建订单。"""
    order = create_order_direct(user_id=req.user_id, items=req.items, address=req.address)
    return success_response(order)
```

---

### Step 4：修改 `services/scheduler_jobs.py`

新增 `process_payments()` 函数：

```python
def process_payments():
    """扫描 processing 支付记录，模拟处理。

    配置：
    - 模拟延迟 1-3 秒（从 created_at 计算）
    - 5% 概率模拟支付失败
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)

        cur.execute("""
            SELECT id, order_id, created_at
            FROM shop.payment_records
            WHERE status = 'processing'
            ORDER BY created_at ASC
        """)
        records = cur.fetchall()
        if not records:
            return

        now = datetime.now()
        for rec in records:
            elapsed = (now - rec["created_at"].replace(tzinfo=None)).total_seconds()
            # 判断是否达到最小模拟延迟
            if elapsed < PAYMENT_DELAY_MIN_SECONDS:
                continue
            # 超时判断（超过最大延迟 + 5 秒兜底）
            if elapsed > PAYMENT_DELAY_MAX_SECONDS + 5:
                # 超时标记为失败
                complete_payment(rec["id"], success=False, error_message="支付超时")
                continue
            # 随机成功/失败（不超过最大延迟才处理）
            if elapsed >= PAYMENT_DELAY_MIN_SECONDS:
                import random
                success = random.random() > PAYMENT_FAILURE_RATE
                complete_payment(rec["id"], success=success,
                                 error_message=None if success else "模拟支付失败")
    except Exception as e:
        logger.error(f"[支付处理] 出错: {e}")
    finally:
        release_connection(conn)
```

---

### Step 5：修改 `main.py`

在 `_register_scheduler_jobs()` 中注册新任务：

```python
def _register_scheduler_jobs():
    # ... 现有任务 ...
    scheduler.add_job(
        cancel_timeout_orders,
        "interval",
        seconds=300,
        id="cancel_timeout_orders",
        replace_existing=True,
    )
    scheduler.add_job(
        advance_logistics,
        "interval",
        seconds=30,
        id="advance_logistics",
        replace_existing=True,
    )
    # ✅ 新增：支付处理任务（每 3 秒）
    scheduler.add_job(
        process_payments,
        "interval",
        seconds=3,
        id="process_payments",
        replace_existing=True,
    )
```

并导入 `process_payments`：

```python
from services.scheduler_jobs import (
    cancel_timeout_orders,
    advance_logistics,
    process_payments,    # ✅ 新增
)
```

---

## 四、接口契约

### 与前端接口

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/api/shop/c-endpoint/orders/{id}/pay` | `{"payment_method": "wechat"}` | `{"payment_id":1, "status":"processing", "transaction_no":"TXN..."}` |
| GET | `/api/shop/c-endpoint/orders/{id}/payment` | — | `{"status":"success", "method":"wechat", "finished_at":"..."}` |

### 内部接口（供 AI 服务）

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/internal/orders/create` | `{"user_id":1, "items":[...], "address":"..."}` | `{"id":1024, "total_amount":2598, "status":"pending"}` |

---

## 五、自测清单

| # | 测试项 | 预期 |
|:-:|--------|------|
| 1 | 发起支付，payment_method 传递正确 | 返回 processing 状态 |
| 2 | 等待 1-3 秒后支付自动完成 | `get_payment_status` 返回 success |
| 3 | 重复发起支付（同一订单） | 校验订单已支付，拒绝 |
| 4 | 无效支付方式 | 返回业务错误 |
| 5 | 已取消订单发起支付 | 拒绝 |
| 6 | create_order_direct 库存扣减正确 | 库存减少，订单创建成功 |
| 7 | create_order_direct 库存不足 | 返回业务错误 |
| 8 | 支付成功后自动创建物流 | logistics_records 有对应记录 |

---

## 六、依赖关系

- ➡️ **小A 依赖你**的 `POST /internal/orders/create` 和支付端点
- ➡️ **前端依赖你**的支付接口变更（`payment_method` 参数）
- ✅ **无上游依赖**：可独立开发测试

---

## 七、注意事项

1. **⚠️ 返回值格式变化**：`POST /pay` 以前直接返回 success，现在返回 processing。需通知小A 和前端做相应调整
2. **行级锁顺序**：先锁订单 → 再锁支付记录，保持全局一致，避免死锁
3. **事务粒度**：`initiate_payment` 和 `complete_payment` 是独立事务，重入安全
4. **随机失败率**：`PAYMENT_FAILURE_RATE=0.05`，可通过环境变量配置

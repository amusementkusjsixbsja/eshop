# 小D 开发指南 — 管理后台服务

## 你的文件夹

```
service-admin/  ← 你的专属文件夹（只改这里）
├── main.py                     # FastAPI 入口
├── requirements.txt            # 依赖
├── Dockerfile                  # 已有
├── routers/
│   ├── category_router.py      # ★ 需要你实现：分类 CRUD + 缓存清理
│   ├── product_router.py       # ★ 需要你实现：商品 CRUD + 上下架 + 缓存清理
│   └── order_router.py         # ★ 需要你实现：查看全部订单（只读）
└── services/
    ├── category_service.py     # 业务逻辑放这里
    ├── product_service.py      # 业务逻辑放这里
    └── order_service.py        # 业务逻辑放这里
```

## 你的数据表

| 表 | 权限 | 说明 |
|-----|------|------|
| `shop.categories` | **你写** | 分类 CRUD |
| `shop.products` | **你写** | 商品 CRUD + 上下架 |
| `shop.orders` | **你读** | 查看全部订单 |
| `shop.order_items` | **你读** | 订单明细 |

## 你的接口

| 方法 | 路径 | 说明 | 关键规则 |
|------|------|------|---------|
| GET | `/b-endpoint/categories` | 全部分类 | 返回所有分类（扁平列表） |
| POST | `/b-endpoint/categories` | 创建分类 | parent_id 可选（二级） |
| PUT | `/b-endpoint/categories/{id}` | 编辑分类 | 更新后 `del categories:tree` |
| DELETE | `/b-endpoint/categories/{id}` | 删除分类 | 检查商品引用，有则拒绝 |
| GET | `/b-endpoint/products` | 全部商品 | 管理员视角（含下架商品）|
| POST | `/b-endpoint/products` | 发布商品 | 初始 `status=on_sale` |
| PUT | `/b-endpoint/products/{id}` | 编辑商品 | 更新后 `del product:{id}` + `del hot:products:list` |
| PATCH | `/b-endpoint/products/{id}/status` | 上下架 | 同上 |
| GET | `/b-endpoint/orders` | 全部订单 | 跨用户查看，只读 |
| GET | `/b-endpoint/orders/{id}` | 订单详情 | 只读 |

## 缓存失效规则（非常重要）

每次 B 端写操作后，必须删除受影响的 Redis key：

| 操作 | 需删除的 Redis key |
|------|-------------------|
| 创建/编辑/删除分类 | `categories:tree` |
| 发布商品 | `hot:products:list` |
| 编辑商品 | `product:{id}` + `hot:products:list` |
| 上架/下架商品 | `product:{id}` + `hot:products:list` |

```python
# 缓存删除示例
from shop_shared.infrastructure import delete_cache, delete_keys

# 编辑商品后
delete_keys([f"product:{product_id}", "hot:products:list"])
```

## 关键业务规则

1. **分类删除前**：`SELECT COUNT(*) FROM shop.products WHERE category_id = %s` — 有引用则拒绝
2. **商品发布**：必须关联有效分类，初始状态为 `on_sale`
3. **下架不影响已有订单**：订单明细是快照，不可修改
4. **所有接口需要 role=admin**：用 `Depends(get_current_admin)` 防护

## 开发方式

```bash
# 启动你的服务 + 基础设施
docker compose -f docker/docker-compose.yml up -d postgres redis admin

# 验证
curl http://localhost:8003/health

# 测试接口（需要管理员 Token）
# 先通过 user-product 登录获取 token
curl http://localhost:8003/b-endpoint/categories
```

## 预置管理员账号

- 邮箱: `admin@shop.local`
- 密码: `admin123`（bcrypt 加密，由 init.sql 预置）

> 获取管理员 Token：调用 `POST /api/shop/c-endpoint/auth/login` 传入管理员邮箱密码。
> 但登录接口在小B的服务中。联调阶段再跟小B协调获取 Token。
> 单人开发时可以先注释掉 `Depends(get_current_admin)` 并用 mock user。

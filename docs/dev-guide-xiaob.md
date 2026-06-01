# 小B 开发指南 — 用户与商品浏览服务

## 你的文件夹

```
service-user-product/  ← 你的专属文件夹（只改这里）
├── main.py                     # FastAPI 入口（已有，一般不用改）
├── requirements.txt            # 依赖（已有，一般不用改）
├── Dockerfile                  # 已有，一般不用改
├── routers/
│   ├── auth_router.py          # ★ 需要你实现：注册/登录/JWT/个人信息
│   ├── product_router.py       # ★ 需要你实现：商品列表/详情/热门/分类树
│   └── internal_router.py      # ★ 需要你实现：内部接口
└── services/
    ├── user_service.py         # 业务逻辑放这里（可选）
    ├── product_service.py      # 业务逻辑放这里（可选）
    └── category_service.py     # 业务逻辑放这里（可选）
```

## 你的数据表

| 表 | 权限 | 说明 |
|-----|------|------|
| `shop.users` | **你写** | 注册/登录/个人信息 |
| `shop.categories` | **你读** + 小D写 | 分类树读取 |
| `shop.products` | **你读** + 小D写 | 商品列表/详情 |

## 你的接口

### C 端接口

| 方法 | 路径 | 说明 | TODO程度 |
|------|------|------|---------|
| POST | `/c-endpoint/auth/register` | 注册（邮箱唯一 + bcrypt） | 全部替换 |
| POST | `/c-endpoint/auth/login` | 登录（bcrypt比对 + JWT签发） | 全部替换 |
| GET | `/c-endpoint/auth/me` | 个人信息 | 替换 |
| PUT | `/c-endpoint/auth/address` | 更新地址 | 替换 |
| GET | `/c-endpoint/products` | 商品列表（分类筛选/搜索/分页） | 替换 |
| GET | `/c-endpoint/products/hot` | 热门商品（Redis缓存优先） | 替换 |
| GET | `/c-endpoint/products/{id}` | 商品详情（Cache-Aside） | 替换 |
| GET | `/c-endpoint/products/categories/tree` | 分类树（Cache-Aside） | 替换 |

### 内部接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/internal/users/{user_id}` | 用户信息 |
| GET | `/internal/products/search` | 商品搜索 |
| GET | `/internal/products/{id}` | 商品详情 |

## 需要做的事

每个 router 文件中都有 `# TODO: 小B` 标记，替换 mock 数据为真实数据库查询。

### 关键逻辑

1. **注册**: `INSERT INTO shop.users (email, password, nickname)`
   - 邮箱唯一性校验 + bcrypt 加密密码
2. **登录**: `SELECT ... WHERE email = %s`
   - bcrypt 比对 → JWT 签发 (`user_id`, `email`, `role`, `exp`)
3. **商品列表**: `SELECT p.*, c.name as category_name FROM shop.products p JOIN categories c`
   - 条件: `status='on_sale'` + 分类筛选 + 关键词 ILIKE + 分页
4. **热门商品**: 优先 Redis → 未命中查 DB → 回写 Redis
5. **商品详情**: 优先 Redis → 未命中查 DB → 回写 Redis

## 开发方式

```bash
# 启动你的服务 + 基础设施
docker compose -f docker/docker-compose.yml up -d postgres redis user-product

# 验证服务健康
curl http://localhost:8001/health

# 测试你的接口
curl http://localhost:8001/c-endpoint/products

# 查看日志
docker compose -f docker/docker-compose.yml logs -f user-product
```

## 可复用的工具

```python
# 1. 自动事务查询
from shop_shared.infrastructure import get_cursor

with get_cursor() as cur:
    cur.execute("SELECT * FROM shop.products WHERE id = %s", (product_id,))
    row = cur.fetchone()

# 2. 手动事务（下单场景）
from shop_shared.infrastructure import get_connection, release_connection

conn = get_connection()
conn.autocommit = False
try:
    cur = conn.cursor()
    # ... 业务逻辑 ...
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.autocommit = True
    cur.close()
    release_connection(conn)

# 3. 缓存操作
from shop_shared.infrastructure import get_cache, set_cache, delete_cache

data = get_cache("product:1")
set_cache("product:1", data, ttl=600)
delete_cache("product:1")
```

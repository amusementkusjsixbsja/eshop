# 用户与商品服务 (service-user-product)

用户认证、商品浏览、分类树、地址管理 — 由 小B 负责。

## 端口

- 外部：`8001`
- 内部：`user-product:8001`

## 功能模块

### 1. 用户认证（`/c-endpoint/auth`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 注册（邮箱唯一性校验 + bcrypt 加密） |
| POST | `/login` | 登录（bcrypt 比对 + JWT 签发，24h 有效期） |
| GET | `/me` | 获取当前用户信息（从 JWT 解码） |
| PUT | `/address` | 更新收货地址（旧版单地址） |

### 2. 商品浏览（`/c-endpoint/products`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 商品列表（分类筛选 + 关键词搜索 + 分页） |
| GET | `/hot` | 热门商品（Redis 缓存，前 5 条） |
| GET | `/{id}` | 商品详情（Cache-Aside：Redis → DB） |
| GET | `/categories/tree` | 分类树（Redis 缓存，支持二级分类） |

### 3. 地址管理（`/c-endpoint/addresses`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 地址列表（默认地址排最前） |
| POST | `/` | 新增地址（首次自动设为默认） |
| PUT | `/{id}` | 编辑地址 |
| DELETE | `/{id}` | 删除地址 |
| PATCH | `/{id}/default` | 设为默认地址（互斥：只有一个默认） |

地址字段：收货人、手机号、详细地址、标签（家/公司）、是否默认。

### 4. 内部接口（`/internal` — 供 AI 客服调用）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/users/{id}` | 查询用户基本信息 |
| GET | `/products/search` | 搜索商品 |
| GET | `/products/{id}` | 商品详情 |

认证：`X-Internal-Token` Header。

## 数据库表

- `shop.users` — 用户（email, password, nickname, role）
- `shop.user_addresses` — 多地址（name, phone, address, is_default）
- `shop.products` — 商品（name, price, stock, status）
- `shop.categories` — 分类（parent_id 支持二级）

## 技术要点

- bcrypt 密码加密
- JWT 无状态认证（HS256）
- Redis Cache-Aside 缓存商品详情、分类树、热门商品
- `FOR UPDATE` 行级锁保障并发安全（供 order-trade 调用）

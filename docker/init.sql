-- ============================================
-- 电商平台 — 数据库初始化脚本
-- 首次启动时 PostgreSQL 自动执行
-- ============================================

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- shop schema（电商服务全部表单）
-- ============================================
CREATE SCHEMA IF NOT EXISTS shop;

-- 分类表
CREATE TABLE IF NOT EXISTS shop.categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    parent_id   INTEGER REFERENCES shop.categories(id),
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 商品表
CREATE TABLE IF NOT EXISTS shop.products (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    price       DECIMAL(10,2) NOT NULL,
    image_url   VARCHAR(500),
    stock       INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
    category_id INTEGER NOT NULL REFERENCES shop.categories(id),
    status      VARCHAR(20) DEFAULT 'on_sale',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON shop.products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_status  ON shop.products(status);

-- 用户表
CREATE TABLE IF NOT EXISTS shop.users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    nickname    VARCHAR(100),
    role        VARCHAR(20) DEFAULT 'user',
    address     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 用户地址表（支持多地址管理）
CREATE TABLE IF NOT EXISTS shop.user_addresses (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES shop.users(id),
    label       VARCHAR(50) DEFAULT '',
    name        VARCHAR(100) NOT NULL,
    phone       VARCHAR(20) NOT NULL,
    address     TEXT NOT NULL,
    is_default  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_addresses_user ON shop.user_addresses(user_id);

-- 购物车表
CREATE TABLE IF NOT EXISTS shop.cart_items (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES shop.users(id),
    product_id  INTEGER NOT NULL REFERENCES shop.products(id),
    quantity    INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, product_id)
);

-- 订单表
CREATE TABLE IF NOT EXISTS shop.orders (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES shop.users(id),
    total_amount    DECIMAL(10,2) NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',
    address         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    paid_at         TIMESTAMPTZ,
    cancelled_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_orders_user   ON shop.orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON shop.orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_pending_time ON shop.orders(created_at) WHERE status = 'pending';

-- 订单明细表
CREATE TABLE IF NOT EXISTS shop.order_items (
    id            SERIAL PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES shop.orders(id),
    product_id    INTEGER NOT NULL,
    product_name  VARCHAR(255) NOT NULL,
    price         DECIMAL(10,2) NOT NULL,
    quantity      INTEGER NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 支付记录表
CREATE TABLE IF NOT EXISTS shop.payment_records (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER NOT NULL REFERENCES shop.orders(id),
    amount      DECIMAL(10,2) NOT NULL,
    method      VARCHAR(50) DEFAULT 'mock',
    status      VARCHAR(20) DEFAULT 'success',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 物流追踪表
CREATE TABLE IF NOT EXISTS shop.logistics_records (
    id                  SERIAL PRIMARY KEY,
    order_id            INTEGER NOT NULL REFERENCES shop.orders(id),
    tracking_number     VARCHAR(100) NOT NULL,
    carrier             VARCHAR(50) DEFAULT 'SF-Express',
    status              VARCHAR(30) DEFAULT 'picked_up',
    current_location    VARCHAR(255),
    estimated_delivery  TIMESTAMPTZ,
    timeline            JSONB DEFAULT '[]',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logistics_order ON shop.logistics_records(order_id);

COMMENT ON COLUMN shop.logistics_records.status IS 'picked_up/in_transit/out_for_delivery/delivered';
COMMENT ON COLUMN shop.logistics_records.timeline IS '[{"time":"...","status":"...","location":"..."}]';

-- 售后申请表
CREATE TABLE IF NOT EXISTS shop.after_sale_requests (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES shop.users(id),
    order_id    INTEGER NOT NULL REFERENCES shop.orders(id),
    type        VARCHAR(20) NOT NULL,
    reason      TEXT,
    status      VARCHAR(20) DEFAULT 'pending',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_after_sale_user  ON shop.after_sale_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_after_sale_order ON shop.after_sale_requests(order_id);

COMMENT ON COLUMN shop.after_sale_requests.type IS 'refund/return/exchange';
COMMENT ON COLUMN shop.after_sale_requests.status IS 'pending/approved/rejected/completed';

-- 评价表
CREATE TABLE IF NOT EXISTS shop.reviews (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES shop.products(id),
    user_id     INTEGER NOT NULL REFERENCES shop.users(id),
    order_id    INTEGER NOT NULL REFERENCES shop.orders(id),
    rating      SMALLINT NOT NULL CHECK(rating >= 1 AND rating <= 5),
    content     TEXT DEFAULT '',
    status      VARCHAR(20) DEFAULT 'visible',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, order_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_product ON shop.reviews(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON shop.reviews(user_id);

-- 商品评分字段
ALTER TABLE shop.products ADD COLUMN IF NOT EXISTS avg_rating DECIMAL(3,2) DEFAULT 0;
ALTER TABLE shop.products ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;

-- ============================================
-- AI 客服 schema（customer_service）
-- ============================================
CREATE SCHEMA IF NOT EXISTS customer_service;

CREATE TABLE IF NOT EXISTS customer_service.faq_embeddings (
    id          SERIAL PRIMARY KEY,
    question    TEXT NOT NULL,
    answer      TEXT NOT NULL,
    embedding   vector(1024),
    metadata    JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_faq_embedding
    ON customer_service.faq_embeddings
    USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS customer_service.conversations (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    title       TEXT,
    status      TEXT DEFAULT 'active',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customer_service.messages (
    id              SERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    turn_number     INTEGER NOT NULL,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (conversation_id) REFERENCES customer_service.conversations(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_conv
    ON customer_service.messages(conversation_id, turn_number);

-- ============================================
-- 预置种子数据
-- ============================================

-- 管理员账号（密码: admin123）
INSERT INTO shop.users (email, password, nickname, role)
VALUES ('admin@shop.local', '$2b$12$cUhDYIcu/4WQ45jYFwZQn.Sosq61H0qcTwGRyMXldc84GELg.EFEi', 'Admin', 'admin')
ON CONFLICT (email) DO NOTHING;

-- 测试用户（密码: 123456）
INSERT INTO shop.users (email, password, nickname, role, address)
VALUES ('user@test.com', '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '测试用户', 'user', '广东省深圳市南山区科技园')
ON CONFLICT (email) DO NOTHING;

-- 分类数据
INSERT INTO shop.categories (id, name, parent_id, sort_order) VALUES
    (1, '智能家居', NULL, 1),
    (2, '数码配件', NULL, 2),
    (3, '安防设备', NULL, 3),
    (10, '智能门锁', 1, 1),
    (11, '智能照明', 1, 2),
    (20, '耳机', 2, 1),
    (21, '充电设备', 2, 2),
    (30, '摄像头', 3, 1),
    (31, '门铃', 3, 2)
ON CONFLICT (id) DO NOTHING;

-- 商品数据
INSERT INTO shop.products (id, name, description, price, image_url, stock, category_id, status) VALUES
    (1, '智能门锁 X1', '指纹/密码/钥匙三合一智能门锁，支持远程临时密码', 1299.00, 'https://picsum.photos/seed/p1/400/400', 100, 10, 'on_sale'),
    (2, '无线耳机 Pro', '主动降噪，30小时续航，IPX5防水', 499.00, 'https://picsum.photos/seed/p2/400/400', 200, 20, 'on_sale'),
    (3, '4K 网络摄像头', '超清画质，360度全景监控，夜视功能', 899.00, 'https://picsum.photos/seed/p3/400/400', 50, 30, 'on_sale'),
    (4, '智能音箱', '语音助手，高品质音效，智能家居控制中心', 299.00, 'https://picsum.photos/seed/p4/400/400', 150, 1, 'on_sale'),
    (5, 'USB-C 扩展坞', '7合1多接口，4K 60Hz输出，高速数据传输', 199.00, 'https://picsum.photos/seed/p5/400/400', 300, 21, 'on_sale'),
    (6, 'AI 智能门铃', '人脸识别，远程可视对讲，移动侦测报警', 699.00, 'https://picsum.photos/seed/p6/400/400', 80, 31, 'on_sale'),
    (7, '智能台灯', '护眼调光，手机APP控制，定时开关', 249.00, 'https://picsum.photos/seed/p7/400/400', 180, 11, 'on_sale'),
    (8, '蓝牙追踪器', '防丢神器，手机查找，超长待机', 89.00, 'https://picsum.photos/seed/p8/400/400', 500, 20, 'off_sale'),
    (9, '智能插座', '远程开关，定时控制，电量统计', 79.00, 'https://picsum.photos/seed/p9/400/400', 400, 1, 'on_sale'),
    (10, '无线充电板', '15W快充，兼容多种设备', 129.00, 'https://picsum.photos/seed/p10/400/400', 250, 21, 'on_sale')
ON CONFLICT (id) DO NOTHING;

-- 物流演示数据（关联订单，订单后面才会创建，暂不插入）

-- 重置序列
SELECT setval('shop.categories_id_seq', COALESCE((SELECT MAX(id) FROM shop.categories), 1));
SELECT setval('shop.products_id_seq', COALESCE((SELECT MAX(id) FROM shop.products), 1));
SELECT setval('shop.users_id_seq', COALESCE((SELECT MAX(id) FROM shop.users), 1));

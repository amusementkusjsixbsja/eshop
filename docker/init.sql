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

-- 支付记录表（v2.0 新增 transaction_no / error_message / finished_at 支持异步支付流程）
CREATE TABLE IF NOT EXISTS shop.payment_records (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES shop.orders(id),
    amount          DECIMAL(10,2) NOT NULL,
    method          VARCHAR(50) DEFAULT 'mock',
    status          VARCHAR(20) DEFAULT 'success',
    transaction_no  VARCHAR(100),
    error_message   TEXT,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 向前兼容：旧库无 transaction_no 列时自动追加
ALTER TABLE shop.payment_records ADD COLUMN IF NOT EXISTS transaction_no VARCHAR(100);
ALTER TABLE shop.payment_records ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE shop.payment_records ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;

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
    -- 一级分类
    (1, '智能家居', NULL, 1),
    (2, '数码配件', NULL, 2),
    (3, '安防设备', NULL, 3),
    (4, '家用电器', NULL, 4),
    (5, '运动户外', NULL, 5),
    (6, '个护健康', NULL, 6),
    -- 智能家居 子类
    (10, '智能门锁', 1, 1),
    (11, '智能照明', 1, 2),
    (12, '智能窗帘', 1, 3),
    (13, '扫地机器人', 1, 4),
    -- 数码配件 子类
    (20, '耳机', 2, 1),
    (21, '充电设备', 2, 2),
    (22, '移动电源', 2, 3),
    (23, '数据线', 2, 4),
    -- 安防设备 子类
    (30, '摄像头', 3, 1),
    (31, '门铃', 3, 2),
    (32, '智能猫眼', 3, 3),
    -- 家用电器 子类
    (40, '厨房电器', 4, 1),
    (41, '生活电器', 4, 2),
    -- 运动户外 子类
    (50, '健身器材', 5, 1),
    (51, '户外装备', 5, 2),
    -- 个护健康 子类
    (60, '美容仪器', 6, 1),
    (61, '健康监测', 6, 2)
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
    (10, '无线充电板', '15W快充，兼容多种设备', 129.00, 'https://picsum.photos/seed/p10/400/400', 250, 21, 'on_sale'),
    -- 智能家居
    (11, '智能门锁 Pro Max', '3D人脸识别 + 掌静脉识别，猫眼可视对讲', 2199.00, 'https://picsum.photos/seed/p11/400/400', 60, 10, 'on_sale'),
    (12, '全屋智能照明套装', '5盏调光灯 + 智能网关，支持语音与场景联动', 899.00, 'https://picsum.photos/seed/p12/400/400', 120, 11, 'on_sale'),
    (13, '氛围灯带 5米', 'RGB 全彩，音乐律动，APP 控制', 129.00, 'https://picsum.photos/seed/p13/400/400', 350, 11, 'on_sale'),
    (14, '智能电动窗帘', '静音电机，定时开合，光感自动', 799.00, 'https://picsum.photos/seed/p14/400/400', 90, 12, 'on_sale'),
    (15, '窗帘伴侣电机', '适配各种轨道，一分钟安装，语音控制', 259.00, 'https://picsum.photos/seed/p15/400/400', 200, 12, 'on_sale'),
    (16, '扫拖一体机器人', 'LDS激光导航，自动集尘，4000Pa大吸力', 1799.00, 'https://picsum.photos/seed/p16/400/400', 70, 13, 'on_sale'),
    (17, '迷你扫地机器人', '超薄机身，适合小户型，静音清扫', 599.00, 'https://picsum.photos/seed/p17/400/400', 140, 13, 'on_sale'),
    -- 数码配件
    (18, '入耳式有线耳机', 'HiFi音质，线控麦克风，3.5mm接口', 49.00, 'https://picsum.photos/seed/p18/400/400', 600, 20, 'on_sale'),
    (19, '头戴式降噪耳机', '40小时续航，双金标认证，舒适佩戴', 899.00, 'https://picsum.photos/seed/p19/400/400', 110, 20, 'on_sale'),
    (20, '65W 氮化镓充电器', '三口快充，折叠插脚，多设备同充', 159.00, 'https://picsum.photos/seed/p20/400/400', 320, 21, 'on_sale'),
    (21, '20000mAh 移动电源', '双向快充，数显电量，可上飞机', 199.00, 'https://picsum.photos/seed/p21/400/400', 280, 22, 'on_sale'),
    (22, '磁吸无线充电宝', 'MagSafe兼容，5000mAh，超薄便携', 179.00, 'https://picsum.photos/seed/p22/400/400', 240, 22, 'on_sale'),
    (23, '100W 数据线套装', 'C-to-C 编织线，支持PD快充，3条装', 69.00, 'https://picsum.photos/seed/p23/400/400', 500, 23, 'on_sale'),
    (24, '三合一充电线', '一线充手机/平板/手表，1.5米', 59.00, 'https://picsum.photos/seed/p24/400/400', 450, 23, 'on_sale'),
    -- 安防设备
    (25, '室外云台摄像头', '4G版免布线，全彩夜视，AI人形追踪', 459.00, 'https://picsum.photos/seed/p25/400/400', 95, 30, 'on_sale'),
    (26, '双目全景摄像头', '180°超广角，双向语音，本地云存储', 329.00, 'https://picsum.photos/seed/p26/400/400', 130, 30, 'on_sale'),
    (27, '可视门铃 Lite', '1080P高清，PIR侦测，电池版', 299.00, 'https://picsum.photos/seed/p27/400/400', 160, 31, 'on_sale'),
    (28, '智能猫眼 Plus', '5英寸大屏，人脸识别，异常抓拍', 649.00, 'https://picsum.photos/seed/p28/400/400', 75, 32, 'on_sale'),
    -- 家用电器
    (29, '空气炸锅 5L', '无油低脂，可视窗口，8种预设菜单', 399.00, 'https://picsum.photos/seed/p29/400/400', 210, 40, 'on_sale'),
    (30, '破壁料理机', '静音降噪，加热破壁，预约功能', 599.00, 'https://picsum.photos/seed/p30/400/400', 100, 40, 'on_sale'),
    (31, '即热式饮水机', '3秒速热，多档水温，台式免安装', 459.00, 'https://picsum.photos/seed/p31/400/400', 120, 40, 'on_sale'),
    (32, '除螨吸尘器', '紫外线除螨，大吸力，无线手持', 349.00, 'https://picsum.photos/seed/p32/400/400', 180, 41, 'on_sale'),
    (33, '智能加湿器', '4L大容量，恒湿净化，夜灯功能', 229.00, 'https://picsum.photos/seed/p33/400/400', 260, 41, 'on_sale'),
    (34, '桌面小风扇', 'USB充电，静音自然风，三档调节', 79.00, 'https://picsum.photos/seed/p34/400/400', 400, 41, 'on_sale'),
    -- 运动户外
    (35, '智能跳绳', '计数计时，卡路里统计，无绳可用', 99.00, 'https://picsum.photos/seed/p35/400/400', 350, 50, 'on_sale'),
    (36, '可调节哑铃', '2.5-25kg快速调节，一对装，家用健身', 899.00, 'https://picsum.photos/seed/p36/400/400', 80, 50, 'on_sale'),
    (37, '瑜伽垫加厚', 'TPE环保材质，防滑双面，附绑带', 129.00, 'https://picsum.photos/seed/p37/400/400', 300, 50, 'on_sale'),
    (38, '户外折叠椅', '铝合金超轻，承重120kg，便携收纳', 189.00, 'https://picsum.photos/seed/p38/400/400', 220, 51, 'on_sale'),
    (39, '保温运动水壶', '316不锈钢，24小时保温，1L大容量', 89.00, 'https://picsum.photos/seed/p39/400/400', 480, 51, 'on_sale'),
    (40, '登山双肩背包', '40L大容量，防泼水，多隔层设计', 269.00, 'https://picsum.photos/seed/p40/400/400', 150, 51, 'on_sale'),
    -- 个护健康
    (41, '射频美容仪', 'EMS微电流，导入导出，紧致提拉', 799.00, 'https://picsum.photos/seed/p41/400/400', 90, 60, 'on_sale'),
    (42, '脉冲脱毛仪', '冰点无痛，5档能量，全身适用', 599.00, 'https://picsum.photos/seed/p42/400/400', 110, 60, 'on_sale'),
    (43, '电动牙刷', '声波震动，5种模式，30天续航', 199.00, 'https://picsum.photos/seed/p43/400/400', 320, 60, 'on_sale'),
    (44, '智能手环', '心率血氧监测，睡眠分析，14天续航', 249.00, 'https://picsum.photos/seed/p44/400/400', 400, 61, 'on_sale'),
    (45, '电子体重秤', 'BMI体脂测量，APP数据同步，高精度', 129.00, 'https://picsum.photos/seed/p45/400/400', 360, 61, 'on_sale')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 丰富演示数据（v2.1）：用户 / 地址 / 订单 / 物流 / 售后 / 评价
-- 说明：所有下列用户密码均为 123456（复用测试用户 bcrypt 哈希）
-- ============================================

-- 追加用户（id 3-12）
INSERT INTO shop.users (id, email, password, nickname, role, address) VALUES
    (3,  'zhangwei@test.com',  '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '张伟',     'user', '北京市朝阳区建国路88号'),
    (4,  'lina@test.com',      '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '李娜',     'user', '上海市浦东新区世纪大道100号'),
    (5,  'wangfang@test.com',  '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '王芳',     'user', '广州市天河区珠江新城'),
    (6,  'liuyang@test.com',   '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '刘洋',     'user', '杭州市西湖区文三路'),
    (7,  'chenjing@test.com',  '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '陈静',     'user', '成都市高新区天府大道'),
    (8,  'yanglei@test.com',   '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '杨磊',     'user', '武汉市洪山区光谷大道'),
    (9,  'zhaomin@test.com',   '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '赵敏',     'user', '南京市鼓楼区中山路'),
    (10, 'sunhao@test.com',    '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '孙浩',     'user', '西安市雁塔区高新路'),
    (11, 'zhouli@test.com',    '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '周丽',     'user', '苏州市工业园区星湖街'),
    (12, 'wutao@test.com',     '$2b$12$pA4dNtoZ2vqeN4gXT.ioYuvi2RkSVaLGoOG7axczsbPXY4rn8ULgu', '吴涛',     'user', '重庆市渝北区新南路')
ON CONFLICT (id) DO NOTHING;

-- 用户地址（多地址演示）
INSERT INTO shop.user_addresses (user_id, label, name, phone, address, is_default) VALUES
    (2, '家',   '测试用户', '13800138000', '广东省深圳市南山区科技园南区A栋', TRUE),
    (2, '公司', '测试用户', '13800138001', '广东省深圳市福田区CBD中心大厦', FALSE),
    (2, '父母家', '张父', '13800138002', '湖南省长沙市岳麓区银盆岭', FALSE),
    (3, '家',   '张伟',   '13911112222', '北京市朝阳区建国路88号SOHO现代城', TRUE),
    (4, '家',   '李娜',   '13922223333', '上海市浦东新区世纪大道100号环球金融中心', TRUE),
    (5, '家',   '王芳',   '13933334444', '广州市天河区珠江新城华夏路10号', TRUE),
    (6, '家',   '刘洋',   '13944445555', '杭州市西湖区文三路478号华星时代广场', TRUE)
ON CONFLICT DO NOTHING;

-- 订单（多状态：paid 已支付 / pending 待支付 / cancelled 已取消）
INSERT INTO shop.orders (id, user_id, total_amount, status, address, created_at, paid_at, cancelled_at) VALUES
    (1,  2,  1299.00, 'paid',      '广东省深圳市南山区科技园南区A栋',    NOW() - INTERVAL '15 days', NOW() - INTERVAL '15 days', NULL),
    (2,  2,  499.00,  'paid',      '广东省深圳市南山区科技园南区A栋',    NOW() - INTERVAL '12 days', NOW() - INTERVAL '12 days', NULL),
    (3,  2,  598.00,  'paid',      '广东省深圳市福田区CBD中心大厦',      NOW() - INTERVAL '9 days',  NOW() - INTERVAL '9 days',  NULL),
    (4,  3,  2199.00, 'paid',      '北京市朝阳区建国路88号SOHO现代城',   NOW() - INTERVAL '11 days', NOW() - INTERVAL '11 days', NULL),
    (5,  3,  899.00,  'paid',      '北京市朝阳区建国路88号SOHO现代城',   NOW() - INTERVAL '7 days',  NOW() - INTERVAL '7 days',  NULL),
    (6,  4,  1107.00, 'paid',      '上海市浦东新区世纪大道100号',        NOW() - INTERVAL '10 days', NOW() - INTERVAL '10 days', NULL),
    (7,  4,  399.00,  'paid',      '上海市浦东新区世纪大道100号',        NOW() - INTERVAL '5 days',  NOW() - INTERVAL '5 days',  NULL),
    (8,  5,  799.00,  'paid',      '广州市天河区珠江新城华夏路10号',     NOW() - INTERVAL '8 days',  NOW() - INTERVAL '8 days',  NULL),
    (9,  5,  448.00,  'paid',      '广州市天河区珠江新城华夏路10号',     NOW() - INTERVAL '4 days',  NOW() - INTERVAL '4 days',  NULL),
    (10, 6,  1799.00, 'paid',      '杭州市西湖区文三路478号',            NOW() - INTERVAL '6 days',  NOW() - INTERVAL '6 days',  NULL),
    (11, 6,  249.00,  'paid',      '杭州市西湖区文三路478号',            NOW() - INTERVAL '3 days',  NOW() - INTERVAL '3 days',  NULL),
    (12, 7,  599.00,  'paid',      '成都市高新区天府大道',               NOW() - INTERVAL '5 days',  NOW() - INTERVAL '5 days',  NULL),
    (13, 8,  288.00,  'paid',      '武汉市洪山区光谷大道',               NOW() - INTERVAL '4 days',  NOW() - INTERVAL '4 days',  NULL),
    (14, 9,  899.00,  'paid',      '南京市鼓楼区中山路',                 NOW() - INTERVAL '6 days',  NOW() - INTERVAL '6 days',  NULL),
    (15, 10, 199.00,  'paid',      '西安市雁塔区高新路',                 NOW() - INTERVAL '2 days',  NOW() - INTERVAL '2 days',  NULL),
    -- 待支付订单
    (16, 2,  229.00,  'pending',   '广东省深圳市南山区科技园南区A栋',    NOW() - INTERVAL '1 hours', NULL, NULL),
    (17, 11, 899.00,  'pending',   '苏州市工业园区星湖街',               NOW() - INTERVAL '30 minutes', NULL, NULL),
    -- 已取消订单
    (18, 12, 129.00,  'cancelled', '重庆市渝北区新南路',                 NOW() - INTERVAL '3 days',  NULL, NOW() - INTERVAL '3 days'),
    (19, 3,  79.00,   'cancelled', '北京市朝阳区建国路88号',             NOW() - INTERVAL '2 days',  NULL, NOW() - INTERVAL '2 days')
ON CONFLICT (id) DO NOTHING;

-- 订单明细（金额与订单 total_amount 一致）
INSERT INTO shop.order_items (order_id, product_id, product_name, price, quantity) VALUES
    (1,  1,  '智能门锁 X1',       1299.00, 1),
    (2,  2,  '无线耳机 Pro',      499.00,  1),
    (3,  4,  '智能音箱',          299.00,  2),
    (4,  11, '智能门锁 Pro Max',  2199.00, 1),
    (5,  3,  '4K 网络摄像头',     899.00,  1),
    (6,  12, '全屋智能照明套装',  899.00,  1),
    (6,  13, '氛围灯带 5米',      129.00,  1),
    (6,  9,  '智能插座',          79.00,   1),
    (7,  29, '空气炸锅 5L',       399.00,  1),
    (8,  41, '射频美容仪',        799.00,  1),
    (9,  43, '电动牙刷',          199.00,  1),
    (9,  7,  '智能台灯',          249.00,  1),
    (10, 16, '扫拖一体机器人',    1799.00, 1),
    (11, 44, '智能手环',          249.00,  1),
    (12, 42, '脉冲脱毛仪',        599.00,  1),
    (13, 21, '20000mAh 移动电源', 199.00,  1),
    (13, 39, '保温运动水壶',      89.00,   1),
    (14, 19, '头戴式降噪耳机',    899.00,  1),
    (15, 5,  'USB-C 扩展坞',      199.00,  1),
    (16, 33, '智能加湿器',        229.00,  1),
    (17, 3,  '4K 网络摄像头',     899.00,  1),
    (18, 45, '电子体重秤',        129.00,  1),
    (19, 9,  '智能插座',          79.00,   1)
ON CONFLICT DO NOTHING;

-- 支付记录（已支付订单，金额与订单一致）
INSERT INTO shop.payment_records (order_id, amount, method, status, transaction_no, finished_at, created_at) VALUES
    (1,  1299.00, 'wechat', 'success', 'TXN20260618A0001', NOW() - INTERVAL '15 days', NOW() - INTERVAL '15 days'),
    (2,  499.00,  'alipay', 'success', 'TXN20260621A0002', NOW() - INTERVAL '12 days', NOW() - INTERVAL '12 days'),
    (3,  598.00,  'wechat', 'success', 'TXN20260624A0003', NOW() - INTERVAL '9 days',  NOW() - INTERVAL '9 days'),
    (4,  2199.00, 'card',   'success', 'TXN20260622A0004', NOW() - INTERVAL '11 days', NOW() - INTERVAL '11 days'),
    (5,  899.00,  'wechat', 'success', 'TXN20260626A0005', NOW() - INTERVAL '7 days',  NOW() - INTERVAL '7 days'),
    (6,  1107.00, 'alipay', 'success', 'TXN20260623A0006', NOW() - INTERVAL '10 days', NOW() - INTERVAL '10 days'),
    (7,  399.00,  'wechat', 'success', 'TXN20260628A0007', NOW() - INTERVAL '5 days',  NOW() - INTERVAL '5 days'),
    (8,  799.00,  'card',   'success', 'TXN20260625A0008', NOW() - INTERVAL '8 days',  NOW() - INTERVAL '8 days'),
    (9,  448.00,  'wechat', 'success', 'TXN20260629A0009', NOW() - INTERVAL '4 days',  NOW() - INTERVAL '4 days'),
    (10, 1799.00, 'alipay', 'success', 'TXN20260627A0010', NOW() - INTERVAL '6 days',  NOW() - INTERVAL '6 days'),
    (11, 249.00,  'wechat', 'success', 'TXN20260630A0011', NOW() - INTERVAL '3 days',  NOW() - INTERVAL '3 days'),
    (12, 599.00,  'wechat', 'success', 'TXN20260628A0012', NOW() - INTERVAL '5 days',  NOW() - INTERVAL '5 days'),
    (13, 288.00,  'alipay', 'success', 'TXN20260629A0013', NOW() - INTERVAL '4 days',  NOW() - INTERVAL '4 days'),
    (14, 899.00,  'card',   'success', 'TXN20260627A0014', NOW() - INTERVAL '6 days',  NOW() - INTERVAL '6 days'),
    (15, 199.00,  'wechat', 'success', 'TXN20260701A0015', NOW() - INTERVAL '2 days',  NOW() - INTERVAL '2 days')
ON CONFLICT DO NOTHING;

-- 物流记录（已支付订单，部分已签收、部分运输中）
INSERT INTO shop.logistics_records (order_id, tracking_number, carrier, status, current_location, estimated_delivery, timeline, created_at) VALUES
    (1,  'SF1234567890001', 'SF-Express', 'delivered', '您的手中', NOW() - INTERVAL '14 days',
     '[{"time":"09:00","status":"已揽件","location":"深圳仓库"},{"time":"12:00","status":"运输中","location":"深圳集散中心"},{"time":"15:00","status":"运输中","location":"广州中转"},{"time":"18:00","status":"派送中","location":"派送中"},{"time":"20:00","status":"已签收","location":"您的手中"}]'::jsonb, NOW() - INTERVAL '15 days'),
    (2,  'SF1234567890002', 'SF-Express', 'delivered', '您的手中', NOW() - INTERVAL '11 days',
     '[{"time":"10:00","status":"已揽件","location":"深圳仓库"},{"time":"14:00","status":"运输中","location":"深圳集散中心"},{"time":"19:00","status":"已签收","location":"您的手中"}]'::jsonb, NOW() - INTERVAL '12 days'),
    (3,  'SF1234567890003', 'SF-Express', 'delivered', '您的手中', NOW() - INTERVAL '8 days',
     '[{"time":"08:30","status":"已揽件","location":"深圳仓库"},{"time":"16:00","status":"已签收","location":"您的手中"}]'::jsonb, NOW() - INTERVAL '9 days'),
    (4,  'SF1234567890004', 'SF-Express', 'delivered', '您的手中', NOW() - INTERVAL '10 days',
     '[{"time":"09:00","status":"已揽件","location":"深圳仓库"},{"time":"20:00","status":"已签收","location":"您的手中"}]'::jsonb, NOW() - INTERVAL '11 days'),
    (5,  'SF1234567890005', 'SF-Express', 'in_transit', '广州中转', NOW() + INTERVAL '1 days',
     '[{"time":"09:00","status":"已揽件","location":"深圳仓库"},{"time":"13:00","status":"运输中","location":"广州中转"}]'::jsonb, NOW() - INTERVAL '7 days'),
    (6,  'SF1234567890006', 'SF-Express', 'delivered', '您的手中', NOW() - INTERVAL '9 days',
     '[{"time":"09:00","status":"已揽件","location":"深圳仓库"},{"time":"18:00","status":"已签收","location":"您的手中"}]'::jsonb, NOW() - INTERVAL '10 days'),
    (7,  'SF1234567890007', 'SF-Express', 'out_for_delivery', '派送中', NOW(),
     '[{"time":"09:00","status":"已揽件","location":"深圳仓库"},{"time":"11:00","status":"运输中","location":"深圳集散中心"},{"time":"14:00","status":"派送中","location":"派送中"}]'::jsonb, NOW() - INTERVAL '5 days'),
    (8,  'SF1234567890008', 'SF-Express', 'delivered', '您的手中', NOW() - INTERVAL '7 days',
     '[{"time":"09:00","status":"已揽件","location":"深圳仓库"},{"time":"19:00","status":"已签收","location":"您的手中"}]'::jsonb, NOW() - INTERVAL '8 days'),
    (10, 'SF1234567890010', 'SF-Express', 'delivered', '您的手中', NOW() - INTERVAL '5 days',
     '[{"time":"09:00","status":"已揽件","location":"深圳仓库"},{"time":"17:00","status":"已签收","location":"您的手中"}]'::jsonb, NOW() - INTERVAL '6 days')
ON CONFLICT DO NOTHING;

-- 售后申请（多状态）
INSERT INTO shop.after_sale_requests (user_id, order_id, type, reason, status, created_at) VALUES
    (2, 1,  'return',   '商品与描述不符，指纹识别不灵敏',       'pending',   NOW() - INTERVAL '13 days'),
    (3, 4,  'refund',   '收到商品有划痕，申请退款',             'approved',  NOW() - INTERVAL '9 days'),
    (4, 6,  'exchange', '灯带有一段不亮，申请换货',             'completed', NOW() - INTERVAL '8 days'),
    (5, 8,  'refund',   '美容仪充电异常，申请退款',             'rejected',  NOW() - INTERVAL '6 days'),
    (6, 10, 'return',   '扫地机器人噪音过大，申请退货',         'pending',   NOW() - INTERVAL '4 days'),
    (9, 14, 'exchange', '耳机右侧无声，申请换货',               'approved',  NOW() - INTERVAL '5 days')
ON CONFLICT DO NOTHING;

-- 商品评价（关联已支付订单，覆盖多商品多用户）
INSERT INTO shop.reviews (product_id, user_id, order_id, rating, content, status, created_at) VALUES
    (1,  2,  1,  5, '安装简单，指纹识别很灵敏，反应速度快，外观也很上档次', 'visible', NOW() - INTERVAL '13 days'),
    (2,  2,  2,  4, '降噪效果不错，音质清晰，续航给力，就是佩戴久了有点胀', 'visible', NOW() - INTERVAL '11 days'),
    (4,  2,  3,  5, '音质在这个价位无敌，语音识别准确，孩子很喜欢',         'visible', NOW() - INTERVAL '8 days'),
    (11, 3,  4,  5, '3D人脸识别太方便了，家里老人小孩都能轻松开门',         'visible', NOW() - INTERVAL '10 days'),
    (3,  3,  5,  4, '4K画质很清晰，夜视效果好，就是安装稍微复杂',           'visible', NOW() - INTERVAL '6 days'),
    (12, 4,  6,  5, '全屋照明套装很赞，场景联动很智能，安装师傅很专业',     'visible', NOW() - INTERVAL '9 days'),
    (13, 4,  6,  4, '氛围灯带颜色很正，音乐律动很有感觉',                   'visible', NOW() - INTERVAL '9 days'),
    (29, 4,  7,  5, '空气炸锅太好用了，炸鸡翅外酥里嫩，无油更健康',         'visible', NOW() - INTERVAL '4 days'),
    (41, 5,  8,  4, '射频美容仪用了两周，皮肤确实紧致了一些，坚持使用',     'visible', NOW() - INTERVAL '7 days'),
    (43, 5,  9,  5, '电动牙刷震动力度刚好，刷得很干净，续航超长',           'visible', NOW() - INTERVAL '3 days'),
    (16, 6,  10, 5, '扫拖一体机器人真香，激光导航很精准，自动集尘省心',     'visible', NOW() - INTERVAL '5 days'),
    (44, 6,  11, 4, '智能手环功能齐全，心率监测准确，续航14天名不虚传',     'visible', NOW() - INTERVAL '2 days'),
    (42, 7,  12, 4, '脱毛仪冰点无痛，用了几次效果开始显现，值得入手',       'visible', NOW() - INTERVAL '4 days'),
    (21, 8,  13, 5, '移动电源容量足，双向快充很方便，数显很直观',           'visible', NOW() - INTERVAL '3 days'),
    (19, 9,  14, 5, '头戴降噪耳机音质出色，佩戴舒适，出差必备',             'visible', NOW() - INTERVAL '5 days'),
    (5,  10, 15, 4, 'USB-C扩展坞接口齐全，4K输出稳定，做工不错',            'visible', NOW() - INTERVAL '1 days'),
    (9,  4,  6,  5, '智能插座远程控制很方便，配合音箱语音开关很实用',       'visible', NOW() - INTERVAL '9 days'),
    (7,  5,  9,  4, '智能台灯护眼调光很舒服，定时功能孩子写作业正好用',     'visible', NOW() - INTERVAL '3 days'),
    (39, 8,  13, 5, '保温水壶24小时还是热的，316钢材质放心，容量大',        'visible', NOW() - INTERVAL '3 days')
ON CONFLICT DO NOTHING;

-- 更新商品评分缓存（只统计 visible 评价）
UPDATE shop.products p SET
    avg_rating   = COALESCE((SELECT ROUND(AVG(rating)::numeric, 2) FROM shop.reviews r WHERE r.product_id = p.id AND r.status = 'visible'), 0),
    review_count = COALESCE((SELECT COUNT(*) FROM shop.reviews r WHERE r.product_id = p.id AND r.status = 'visible'), 0);

-- 重置序列
SELECT setval('shop.categories_id_seq', COALESCE((SELECT MAX(id) FROM shop.categories), 1));
SELECT setval('shop.products_id_seq', COALESCE((SELECT MAX(id) FROM shop.products), 1));
SELECT setval('shop.users_id_seq', COALESCE((SELECT MAX(id) FROM shop.users), 1));

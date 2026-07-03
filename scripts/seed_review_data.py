#!/usr/bin/env python3
"""商品评价测试数据脚本 — 为现有商品生成模拟评价数据。

用法：
  1. 确保 docker-compose 服务运行中（PostgreSQL 正常）
  2. 设置环境变量 DATABASE_URL（默认: postgresql://user:1234@postgres:5432/agent）
  3. python scripts/seed_review_data.py

前置条件：
  - 数据库已运行，shop.reviews 表已创建（小B 先完成 init.sql 变更）
  - shop.products 表有种子商品数据（init.sql 已预置）
  - shop.users 表有测试用户数据

说明：
  - 本脚本会创建几个测试用户并为各商品生成模拟评价
  - 幂等执行：同一用户对同一商品不会重复评价（基于 UNIQUE 约束）
  - 支持 --dry-run 参数预览数据而不写入
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime, timedelta

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:1234@postgres:5432/agent")

# ─── 模拟用户数据 ─────────────────────────────────────

SEED_USERS = [
    {"email": "reviewer1@eshop.com", "password": "review123", "nickname": "数码爱好者"},
    {"email": "reviewer2@eshop.com", "password": "review123", "nickname": "理性消费者"},
    {"email": "reviewer3@eshop.com", "password": "review123", "nickname": "体验派小王"},
    {"email": "reviewer4@eshop.com", "password": "review123", "nickname": "技术控老张"},
    {"email": "reviewer5@eshop.com", "password": "review123", "nickname": "品质生活家"},
    {"email": "reviewer6@eshop.com", "password": "review123", "nickname": "性价比党"},
    {"email": "reviewer7@eshop.com", "password": "review123", "nickname": "颜值控小美"},
    {"email": "reviewer8@eshop.com", "password": "review123", "nickname": "实用主义"},
]

# ─── 商品 ID 列表（来自 init.sql 种子数据） ────────────
# 1=智能门锁X1, 2=无线耳机Pro, 3=4K网络摄像头, 4=智能音箱,
# 5=USB-C扩展坞, 6=AI智能门铃, 7=智能台灯, 9=智能插座, 10=无线充电板

PRODUCT_IDS = [1, 2, 3, 4, 5, 6, 7, 9, 10]

# ─── 模拟评价数据 ─────────────────────────────────────

# 每个商品的模拟评价模板（评分分布：5星占比~40%, 4星~30%, 3星~15%, 2星~10%, 1星~5%）
RATING_WEIGHTS = [5] * 40 + [4] * 30 + [3] * 15 + [2] * 10 + [1] * 5  # 共100个权重

REVIEW_TEMPLATES = {
    1: {  # 智能门锁 X1
        "product_name": "智能门锁 X1",
        "reviews": [
            (5, "安装简单，指纹识别很灵敏，反应速度快，外观也很上档次"),
            (5, "用了一个月，非常稳定，远程临时密码功能很实用"),
            (4, "整体不错，就是指纹识别偶尔需要按两次，总体好评"),
            (4, "安全性能好，APP控制方便，推荐购买"),
            (3, "功能还可以，但电池续航一般，大概半年要换一次"),
            (2, "安装后经常有虚报报警，调整灵敏度后好一些"),
            (5, "外观漂亮，质量过硬，师傅安装也很专业"),
            (4, "性价比不错，比实体店便宜很多，功能齐全"),
            (5, "支持多种开锁方式，老人用指纹也很方便"),
            (3, "中规中矩，对得起这个价格，但期待更多智能化功能"),
            (5, "第二次购买了，给父母家也装了一个，质量稳定"),
            (1, "用了三个月就出现故障，联系售后处理中"),
        ],
    },
    2: {  # 无线耳机 Pro
        "product_name": "无线耳机 Pro",
        "reviews": [
            (5, "降噪效果非常好，坐地铁完全听不到噪音"),
            (5, "音质超出预期，低音浑厚，高音清晰"),
            (4, "佩戴舒适，长时间戴着也不会痛，续航给力"),
            (4, "连接稳定，延迟低，打游戏没问题"),
            (5, "这个价位最好的降噪耳机，强烈推荐"),
            (3, "音质不错但降噪开启后有轻微底噪"),
            (5, "防水效果好，运动出汗也不怕，很实用"),
            (2, "用了两个月右耳声音变小，希望是个例"),
            (4, "通话质量清晰，开会用很方便"),
            (3, "充电仓有点大，放口袋不太方便"),
            (5, "第二次购买了，送朋友当礼物很不错"),
            (4, "触控操作灵敏，但是偶尔会误触"),
        ],
    },
    3: {  # 4K 网络摄像头
        "product_name": "4K 网络摄像头",
        "reviews": [
            (5, "画质清晰，夜视效果很好，家里装了安心很多"),
            (4, "360度旋转很方便，APP体验流畅"),
            (5, "安装简单，自己就能搞定，画面清晰度满意"),
            (4, "移动侦测灵敏，误报率低，值得购买"),
            (3, "功能齐全但偶尔断连，需要重启"),
            (5, "4K画质确实好，放大看车牌都没问题"),
            (4, "云存储有点贵，但本地存储也够用"),
            (2, "夜间模式噪点偏多，没有宣传的那么好"),
            (5, "给店铺装的，监控范围大，清晰度高"),
            (3, "设置稍微复杂，搞了半天才配置好"),
        ],
    },
    4: {  # 智能音箱
        "product_name": "智能音箱",
        "reviews": [
            (5, "音质在这个价位无敌，低音效果惊喜"),
            (4, "语音识别准确，控制智能家居很方便"),
            (5, "外观设计好看，放家里很搭，每天用它听新闻"),
            (4, "响应速度快，孩子也很喜欢跟它互动"),
            (3, "音质不错但音量开到最大有破音"),
            (5, "性价比超高，买了两个组立体声"),
            (4, "智能家居联动功能很好用，推荐"),
            (2, "有时候听不懂方言，普通话不太标准的话有点吃力"),
            (5, "送给父母的，他们很喜欢，操作简单"),
            (4, "内容丰富，音乐故事新闻都有，日常够用"),
            (3, "偶尔唤醒不灵敏，需要在安静环境使用"),
        ],
    },
    5: {  # USB-C 扩展坞
        "product_name": "USB-C 扩展坞",
        "reviews": [
            (5, "接口齐全，4K输出稳定，做工精良"),
            (4, "小巧便携，出差带着很方便，满足日常需求"),
            (5, "传输速度快，插拔顺畅，质感好"),
            (4, "功能正常，发热控制不错，长时间使用不太烫"),
            (3, "接口布局有点密，同时插多个设备会挤"),
            (5, "性价比高，比官方便宜很多，功能一样"),
            (4, "兼容性好，Windows和Mac都能用"),
            (2, "用了三个月HDMI接口松动，希望改进做工"),
            (5, "做工精致，数据传输稳定，推荐购买"),
            (4, "支持PD快充，边充电边用拓展坞很方便"),
        ],
    },
    6: {  # AI 智能门铃
        "product_name": "AI 智能门铃",
        "reviews": [
            (5, "人脸识别准确，快递来了我在公司也能对话"),
            (4, "画质清晰，夜视效果不错，安全有保障"),
            (5, "安装方便，APP界面友好，移动侦测灵敏"),
            (4, "AI识别功能好用，能区分人和动物"),
            (3, "偶尔延迟几秒，不影响使用但体验有提升空间"),
            (5, "远程可视对讲很实用，独居女性必备"),
            (4, "电池续航不错，充一次用三个月"),
            (2, "WIFI信号弱的时候连接不稳定，需靠近路由器"),
            (5, "给爸妈装的，他们觉得很好用，来人能看到是谁"),
            (3, "功能不错但云存储订阅费用偏贵"),
            (4, "安装简单，自己半小时搞定，效果满意"),
        ],
    },
    7: {  # 智能台灯
        "product_name": "智能台灯",
        "reviews": [
            (5, "护眼效果明显，长时间看书眼睛不累"),
            (5, "APP控制很方便，可以定时开关，懒人必备"),
            (4, "亮度调节范围大，从阅读灯到氛围灯都合适"),
            (5, "外观简约好看，灯光柔和不刺眼"),
            (4, "色温调节好用，暖光看书冷光工作"),
            (3, "价格小贵但质量不错，希望耐用"),
            (5, "孩子写作业用很好，光线均匀不伤眼"),
            (4, "操作简单，触控灵敏，底座稳当"),
            (2, "智能功能需要APP，不能联网就只是个普通台灯"),
            (4, "照明范围大，整个书桌都能照亮"),
        ],
    },
    9: {  # 智能插座
        "product_name": "智能插座",
        "reviews": [
            (5, "设置简单，远程控制电器很方便"),
            (4, "定时功能很实用，用来控制热水器节省电费"),
            (5, "小巧不占地方，一个插座可以控制多个设备"),
            (4, "电量统计功能好看，能了解用电情况"),
            (3, "稳定性一般，偶尔会离线需要重新连接"),
            (5, "配合智能音箱使用，语音控制电器太方便了"),
            (4, "做工不错，用料扎实，安全有保障"),
            (2, "不支持5G WIFI，只能连2.4G有点不方便"),
            (5, "买了5个把全家电器都智能了，性价比高"),
            (4, "反应速度可以接受，远程开空调很实用"),
            (3, "APP广告有点多，希望能优化"),
        ],
    },
    10: {  # 无线充电板
        "product_name": "无线充电板",
        "reviews": [
            (5, "充电速度不错，支持快充，手机放上去就充"),
            (4, "做工精致，防滑设计好，放桌上很稳"),
            (5, "兼容性好，苹果和安卓都能充"),
            (4, "发热控制不错，充一晚上也不烫"),
            (3, "有时需要调整位置才能充上电，对齐要求高"),
            (5, "颜值高，办公桌上放一个很方便，随放随充"),
            (4, "支持手机耳机同时充挺好的"),
            (2, "充电比有线慢不少，应急可以日常有线更好"),
            (5, "质感好，送礼也很合适，朋友很喜欢"),
            (4, "价格适中，功能稳定，值得购买"),
        ],
    },
}


def seed_review_data(dry_run: bool = False):
    """执行评价测试数据入库。"""
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("[ERROR] 请先安装 psycopg2-binary: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Step 1: 创建测试用户
        print("\n📝 Step 1: 创建测试用户...")
        user_ids = {}
        for u in SEED_USERS:
            cur.execute(
                """INSERT INTO shop.users (email, password, nickname, role)
                   VALUES (%s, %s, %s, 'user')
                   ON CONFLICT (email) DO UPDATE SET nickname = EXCLUDED.nickname
                   RETURNING id""",
                (u["email"], u["password"], u["nickname"]),
            )
            uid = cur.fetchone()["id"]
            user_ids[u["email"]] = uid
            print(f"  ✅ 用户 {u['nickname']}({u['email']}) → id={uid}")

        # Step 2: 检查 shop.reviews 表是否存在
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'shop' AND table_name = 'reviews'
            )
        """)
        table_exists = cur.fetchone()["exists"]
        if not table_exists:
            print("\n❌ shop.reviews 表不存在！请先执行小B的数据库迁移（init.sql 新增 reviews 表）。")
            sys.exit(1)

        # Step 3: 检查已有评价（去重）
        cur.execute("SELECT user_id, product_id FROM shop.reviews")
        existing_reviews = {(r["user_id"], r["product_id"]) for r in cur.fetchall()}

        # Step 4: 为每个 (user, product) 创建真实订单 + 支付，再写入评价
        # reviews 表有 FK order_id → shop.orders(id)，不能用占位 0
        print("\n📝 Step 2: 生成商品评价数据（每个评价关联真实订单）...")
        total_inserted = 0
        total_skipped = 0
        total_orders = 0

        for product_id in PRODUCT_IDS:
            if product_id not in REVIEW_TEMPLATES:
                continue

            template = REVIEW_TEMPLATES[product_id]
            reviews_data = template["reviews"]
            # 从最旧到最新创建时间
            base_time = datetime.now() - timedelta(days=30)

            for i, (rating, content) in enumerate(reviews_data):
                # 轮询分配用户
                user_email = SEED_USERS[i % len(SEED_USERS)]["email"]
                user_id = user_ids[user_email]

                # 检查是否已存在（UNIQUE(user_id, order_id, product_id) 前先做应用层检查）
                if (user_id, product_id) in existing_reviews:
                    total_skipped += 1
                    continue

                created_at = base_time + timedelta(hours=i * 12 + random.randint(0, 6) * 60)

                if dry_run:
                    print(f"  📋 [DRY RUN] product_id={product_id}, user_id={user_id}, rating={rating}")
                    total_inserted += 1
                    continue

                try:
                    # 4a. 为该用户+商品创建订单（pending）
                    cur.execute(
                        """INSERT INTO shop.orders (user_id, total_amount, status, address, created_at)
                           VALUES (%s, (SELECT price FROM shop.products WHERE id = %s), 'pending',
                               '评价测试地址（自动创建）', %s)
                           RETURNING id""",
                        (user_id, product_id, created_at),
                    )
                    order_id = cur.fetchone()["id"]
                    total_orders += 1

                    # 4b. 插入订单明细（含 product_name，该列 NOT NULL）
                    cur.execute(
                        """INSERT INTO shop.order_items (order_id, product_id, product_name, quantity, price)
                           VALUES (%s, %s, (SELECT name FROM shop.products WHERE id = %s), 1,
                                   (SELECT price FROM shop.products WHERE id = %s))""",
                        (order_id, product_id, product_id, product_id),
                    )

                    # 4c. 写入评价（关联到刚创建的 order_id）
                    cur.execute(
                        """INSERT INTO shop.reviews
                           (product_id, user_id, order_id, rating, content, status, created_at, updated_at)
                           VALUES (%s, %s, %s, %s, %s, 'visible', %s, %s)""",
                        (
                            product_id,
                            user_id,
                            order_id,
                            rating,
                            content,
                            created_at,
                            created_at,
                        ),
                    )
                    total_inserted += 1
                    existing_reviews.add((user_id, product_id))
                except Exception as e:
                    if "unique" in str(e).lower():
                        total_skipped += 1
                    else:
                        print(f"  ⚠️  插入失败: {e}")

        if not dry_run:
            conn.commit()

        # Step 5: 更新 products 表的评分缓存
        if not dry_run:
            print("\n📝 Step 3: 更新商品评分缓存...")
            for product_id in PRODUCT_IDS:
                cur.execute("""
                    UPDATE shop.products
                    SET avg_rating = COALESCE((SELECT ROUND(AVG(rating)::numeric, 2) FROM shop.reviews WHERE product_id = %s), 0),
                        review_count = COALESCE((SELECT COUNT(*) FROM shop.reviews WHERE product_id = %s), 0)
                    WHERE id = %s
                """, (product_id, product_id, product_id))
            conn.commit()

        # 统计
        total_expected = sum(len(v["reviews"]) for k, v in REVIEW_TEMPLATES.items() if k in PRODUCT_IDS)
        print(f"\n{'='*50}")
        print(f"  评价种子数据生成完成")
        print(f"  {'📋 [DRY RUN] ' if dry_run else ''}")
        print(f"  计划总数: {total_expected} 条")
        print(f"  新增订单: {total_orders} 条")
        print(f"  新增评价: {total_inserted} 条")
        print(f"  跳过（已存在）: {total_skipped} 条")
        print(f"{'='*50}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="商品评价种子数据脚本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际写入数据库")
    args = parser.parse_args()

    print("=" * 50)
    print("  商品评价种子数据导入")
    print(f"  商品数: {len(PRODUCT_IDS)} 个")
    print(f"  评价模板数: {sum(len(REVIEW_TEMPLATES[pid]['reviews']) for pid in PRODUCT_IDS if pid in REVIEW_TEMPLATES)} 条")
    print(f"  测试用户: {len(SEED_USERS)} 个")
    print("=" * 50)

    seed_review_data(dry_run=args.dry_run)

    print("\n💡 提示:")
    print("   建议先以 --dry-run 预览，确认无误后再正式执行。")
    print("   如需清空评价数据重新导入：")
    print("     TRUNCATE shop.reviews CASCADE;")
    print("     UPDATE shop.products SET avg_rating=0, review_count=0;")


if __name__ == "__main__":
    main()

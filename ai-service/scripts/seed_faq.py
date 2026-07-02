#!/usr/bin/env python3
"""FAQ 种子数据脚本 — 为 RAG 知识库预置 26 条问答数据。

用法：
  1. 确保 docker-compose 服务运行中（PostgreSQL 正常）
  2. 设置环境变量 DATABASE_URL（默认: postgresql://user:1234@postgres:5432/agent）
  3. python ai-service/scripts/seed_faq.py

说明：
  - 本脚本会生成 FAQ 的 embedding 向量并写入 customer_service.faq_embeddings 表
  - 幂等执行：已存在的 FAQ 不会重复插入（按 question 去重）
  - 支持 --dry-run 参数预览数据而不写入
"""

import os
import sys
import json
import argparse

# ─── 配置 ────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:1234@postgres:5432/agent")
LLM_API_URL = os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# ─── FAQ 种子数据 ─────────────────────────────────────

FAQ_SEED_DATA = [
    # ===== 退货政策（4条） =====
    {
        "question": "退货需要什么条件？",
        "answer": "商品不影响二次销售，签收后 7 天内可申请退货退款。如果商品存在质量问题，请提供照片或视频凭证。",
        "category": "退货政策",
    },
    {
        "question": "退货的运费谁承担？",
        "answer": "因质量问题退货，运费由商家承担；非个人原因退货运费由用户承担。建议使用平台推荐的快递公司，便于后续处理。",
        "category": "退货政策",
    },
    {
        "question": "如何申请退货？",
        "answer": "在订单详情页点击「申请售后」，选择「退货退款」，填写退货原因并提交。审核通过后按提示将商品寄回即可。",
        "category": "退货政策",
    },
    {
        "question": "退款多久到账？",
        "answer": "退货审核通过后，退款将在 1-3 个工作日内原路返回。不同支付方式的到账时间略有差异：微信/支付宝通常即时到账，银行卡 1-3 个工作日。",
        "category": "退货政策",
    },
    # ===== 物流时效（4条） =====
    {
        "question": "下单后多久发货？",
        "answer": "通常在支付成功后 24 小时内发货。预售商品和定制商品以商品页面标注的发货时间为准。",
        "category": "物流时效",
    },
    {
        "question": "发货后多久能到？",
        "answer": "同城一般 1-2 天，省内 2-3 天，跨省 3-5 天。偏远地区（新疆、西藏、青海等）可能需要 5-7 天。",
        "category": "物流时效",
    },
    {
        "question": "如何查看物流信息？",
        "answer": "在订单详情页点击「查看物流」即可查看实时物流轨迹，包括揽件、运输、派送等节点的详细时间和地点。",
        "category": "物流时效",
    },
    {
        "question": "可以修改收货地址吗？",
        "answer": "订单未发货前，可在订单详情页修改收货地址。已发货的订单请联系客服尝试拦截转寄。",
        "category": "物流时效",
    },
    # ===== 支付方式（3条） =====
    {
        "question": "支持哪些支付方式？",
        "answer": "支持微信支付、支付宝、银行卡、余额支付四种方式。在进行支付时可以选择任意一种完成交易。",
        "category": "支付方式",
    },
    {
        "question": "支付失败怎么办？",
        "answer": "支付失败可能是网络问题或余额不足导致的。可在订单详情页点击「重新支付」重新发起支付。如已扣款但订单未更新，请联系客服处理。",
        "category": "支付方式",
    },
    {
        "question": "余额怎么使用和充值？",
        "answer": "目前余额仅支持退款退回，暂不支持充值。余额可在支付时选择「余额支付」直接使用。",
        "category": "支付方式",
    },
    # ===== 账户安全（3条） =====
    {
        "question": "如何修改密码？",
        "answer": "在个人中心 → 安全设置中可修改登录密码。修改时需要验证当前密码，请确保牢记新密码。",
        "category": "账户安全",
    },
    {
        "question": "如何修改绑定的手机号或邮箱？",
        "answer": "在个人中心 → 安全设置 → 修改手机号或修改邮箱中进行操作，需要验证原绑定方式。",
        "category": "账户安全",
    },
    {
        "question": "忘记密码怎么办？",
        "answer": "在登录页面点击「忘记密码」，通过注册邮箱接收验证码后即可重置密码。如无法通过邮箱验证，请联系在线客服申诉。",
        "category": "账户安全",
    },
    # ===== 商品知识（4条） =====
    {
        "question": "商品材质如何查看？",
        "answer": "在商品详情页的描述中可以查看材质信息、尺寸参数和使用说明。部分商品还有详细的规格参数表格。",
        "category": "商品知识",
    },
    {
        "question": "商品尺寸怎么选？",
        "answer": "每个商品都有详细尺寸参数，建议参考商品描述中的尺码表。如不确定，可联系在线客服获取建议。",
        "category": "商品知识",
    },
    {
        "question": "商品是否保证正品？",
        "answer": "平台所有商品均为正品，支持官方查验。如发现非正品，可凭检测报告申请退一赔三。",
        "category": "商品知识",
    },
    {
        "question": "如何查看商品评价？",
        "answer": "在商品详情页下滑即可查看已购用户的评价和评分。您可以参考其他用户的真实体验来辅助购买决策。",
        "category": "商品知识",
    },
    # ===== 售后（3条） =====
    {
        "question": "如何申请售后？",
        "answer": "在订单详情页点击「申请售后」即可提交请求。请选择售后类型并填写原因，提交后商家将在 48 小时内审核。",
        "category": "售后",
    },
    {
        "question": "售后有哪些类型？",
        "answer": "支持退款、退货退款、换货三种售后类型。退款适用于未发货订单，退货退款和换货适用于已收货订单。",
        "category": "售后",
    },
    {
        "question": "售后申请多久处理？",
        "answer": "售后申请提交后，商家将在 48 小时内审核处理。审核通过后，退款或换货流程将在 1-3 个工作日内完成。",
        "category": "售后",
    },
    # ===== 优惠活动（2条） =====
    {
        "question": "有优惠券或优惠活动吗？",
        "answer": "关注公众号可领取新用户优惠券。节假日和店庆日会有促销活动，请关注平台公告。部分商品还有限时秒杀活动。",
        "category": "优惠活动",
    },
    {
        "question": "如何参加满减活动？",
        "answer": "活动期间商品页面会显示满减规则，下单时达到满减条件会自动扣减。部分活动需要领取优惠券后方可享受。",
        "category": "优惠活动",
    },
    # ===== 其他（3条） =====
    {
        "question": "如何联系客服？",
        "answer": "点击页面右下角的客服图标即可与 AI 客服对话。AI 客服 7×24 小时在线，可以回答常见问题并协助处理订单。",
        "category": "其他",
    },
    {
        "question": "商品缺货怎么办？",
        "answer": "缺货商品可点击「到货提醒」，补货后系统会自动发送通知。您也可以联系客服咨询预计补货时间。",
        "category": "其他",
    },
    {
        "question": "可以开发票吗？",
        "answer": "在订单详情页点击「申请发票」，填写开票信息即可。支持电子发票和纸质发票，电子发票开具后可直接下载。",
        "category": "其他",
    },
]

CATEGORY_MAP = {
    "退货政策": "return_policy",
    "物流时效": "logistics",
    "支付方式": "payment",
    "账户安全": "account",
    "商品知识": "product_knowledge",
    "售后": "after_sale",
    "优惠活动": "promotion",
    "其他": "other",
}


def generate_embedding(text: str) -> list[float]:
    """调用 LLM 兼容接口生成 1024 维 embedding 向量。

    使用与 ai-service 相同的 LLM API（通义千问兼容接口），
    调用 embedding 模型生成向量。

    注意：
    - 如果 LLM_API_KEY 未配置，返回 1024 维零向量占位
    - 实际使用时需要替换为真正的 embedding 模型调用
    """
    if not LLM_API_KEY:
        print("[WARN] LLM_API_KEY 未配置，使用零向量占位（维度=1024）", file=sys.stderr)
        return [0.0] * 1024

    try:
        import requests
        resp = requests.post(
            f"{LLM_API_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "text-embedding-v3",
                "input": text,
                "dimensions": 1024,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]
    except Exception as e:
        print(f"[ERROR] Embedding 生成失败: {e}", file=sys.stderr)
        print("[WARN] 使用零向量占位", file=sys.stderr)
        return [0.0] * 1024


def seed_faq(dry_run: bool = False):
    """执行 FAQ 种子数据入库。"""
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("[ERROR] 请先安装 psycopg2-binary: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 查询已有 FAQ 列表（用于去重）
        cur.execute("SELECT question FROM customer_service.faq_embeddings")
        existing = {row["question"] for row in cur.fetchall()}

        new_count = 0
        skip_count = 0

        for faq in FAQ_SEED_DATA:
            if faq["question"] in existing:
                print(f"  ⏭️  跳过（已存在）: {faq['question'][:30]}...")
                skip_count += 1
                continue

            # 生成 embedding
            print(f"  🔄 生成 embedding: {faq['question'][:30]}...")
            embedding = generate_embedding(faq["question"] + " " + faq["answer"])

            metadata = json.dumps({
                "category": faq["category"],
                "category_en": CATEGORY_MAP.get(faq["category"], "other"),
            })

            if dry_run:
                print(f"  📋 [DRY RUN] 将插入: {faq['question'][:30]}... (category={faq['category']})")
                new_count += 1
                continue

            cur.execute(
                """INSERT INTO customer_service.faq_embeddings (question, answer, embedding, metadata)
                   VALUES (%s, %s, %s, %s)""",
                (faq["question"], faq["answer"], embedding, metadata),
            )
            new_count += 1

        if not dry_run:
            conn.commit()

        print()
        print(f"  新增: {new_count} 条")
        print(f"  跳过: {skip_count} 条（已存在）")
        print(f"  总计: {len(FAQ_SEED_DATA)} 条")

    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="FAQ 种子数据脚本")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际写入数据库")
    args = parser.parse_args()

    print("=" * 50)
    print("  FAQ 种子数据导入")
    print(f"  数据量: {len(FAQ_SEED_DATA)} 条")
    print(f"  分类数: {len(CATEGORY_MAP)} 个")
    print("=" * 50)
    print()

    for faq in FAQ_SEED_DATA:
        print(f"  [{faq['category']}] Q: {faq['question']}")
        print(f"         A: {faq['answer'][:60]}...")
        print()

    if args.dry_run:
        print(f"\n📋 DRY RUN 模式 — 将新增 {len(FAQ_SEED_DATA)} 条 FAQ")
        seed_faq(dry_run=True)
    else:
        print(f"\n🚀 开始导入 FAQ 种子数据...")
        seed_faq(dry_run=False)
        print(f"\n✅ FAQ 种子数据导入完成！")

    print("\n💡 提示:")
    print("   建议先以 --dry-run 预览，确认无误后再正式执行。")
    print("   如需重新导入全部数据，可先清空表：")
    print("     TRUNCATE customer_service.faq_embeddings;")


if __name__ == "__main__":
    main()

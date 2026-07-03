"""★ 小D：FAQ 知识库管理业务逻辑（管理后台）。

直接操作 customer_service.faq_embeddings 表。
FAQ 的 embedding 向量由 ai-service 异步补全，管理后台只管理问答文本。
"""

import json

from shop_shared.infrastructure import get_cursor
from shop_shared.common.exceptions import NotFoundError, BusinessError


def get_all_faqs(category: str | None = None) -> list:
    """获取 FAQ 列表，支持按 category 筛选。

    category 存储在 metadata JSONB 字段中：{"category": "退货政策"}
    """
    with get_cursor() as cur:
        if category:
            cur.execute(
                """SELECT id, question, answer, metadata
                   FROM customer_service.faq_embeddings
                   WHERE metadata->>'category' = %s
                   ORDER BY id""",
                [category],
            )
        else:
            cur.execute(
                """SELECT id, question, answer, metadata
                   FROM customer_service.faq_embeddings
                   ORDER BY id"""
            )

        items = []
        for row in cur.fetchall():
            item = dict(row)
            # 反序列化 metadata JSONB
            if isinstance(item.get("metadata"), str):
                item["metadata"] = json.loads(item["metadata"])
            items.append(item)

    return items


def add_faq(question: str, answer: str, category: str = "general") -> dict:
    """添加 FAQ 条目。

    embedding 用零向量占位，后续由 ai-service 异步生成真实向量。
    """
    metadata = json.dumps({"category": category}, ensure_ascii=False)

    with get_cursor() as cur:
        # 需要 public schema 的 vector 类型（数据库连接默认 search_path=shop）
        cur.execute("SET LOCAL search_path TO shop, public")

        cur.execute(
            """INSERT INTO customer_service.faq_embeddings (question, answer, embedding, metadata)
               VALUES (%s, %s, array_fill(0::float8, ARRAY[1024])::vector, %s)
               RETURNING id, question, answer, metadata""",
            [question, answer, metadata],
        )
        faq = cur.fetchone()
        if not faq:
            raise BusinessError("FAQ 添加失败")

    # 处理返回数据
    faq = dict(faq)
    if isinstance(faq.get("metadata"), str):
        faq["metadata"] = json.loads(faq["metadata"])
    faq.pop("embedding", None)  # 不返回向量给前端
    return faq


def update_faq(
    faq_id: int,
    question: str | None = None,
    answer: str | None = None,
    category: str | None = None,
) -> dict:
    """修改 FAQ 条目（支持部分更新）。"""
    sets: list[str] = []
    params: list = []

    if question is not None:
        sets.append("question = %s")
        params.append(question)
    if answer is not None:
        sets.append("answer = %s")
        params.append(answer)
    if category is not None:
        sets.append("metadata = %s")
        params.append(json.dumps({"category": category}, ensure_ascii=False))

    if not sets:
        raise BusinessError("没有需要更新的字段")

    params.append(faq_id)

    with get_cursor() as cur:
        cur.execute(
            f"""UPDATE customer_service.faq_embeddings
                SET {', '.join(sets)}
                WHERE id = %s
                RETURNING id, question, answer, metadata""",
            params,
        )
        faq = cur.fetchone()
        if not faq:
            raise NotFoundError("FAQ 不存在")

    faq = dict(faq)
    if isinstance(faq.get("metadata"), str):
        faq["metadata"] = json.loads(faq["metadata"])
    return faq


def delete_faq(faq_id: int) -> None:
    """删除 FAQ 条目。"""
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM customer_service.faq_embeddings WHERE id = %s RETURNING id",
            [faq_id],
        )
        if not cur.fetchone():
            raise NotFoundError("FAQ 不存在")

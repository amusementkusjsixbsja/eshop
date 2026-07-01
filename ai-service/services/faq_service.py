"""★ 小A：RAG FAQ 知识库检索服务。

流程：用户提问 → 生成 embedding → pgvector 余弦相似度查询 → 返回最佳匹配答案

数据来源：customer_service.faq_embeddings（vector(1024)）。
种子数据由 scripts/seed_faq.py 导入。
"""

import json
import os

import requests

from services.database import get_cursor

# ── Embedding 配置 ──
LLM_API_URL = os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-v3"  # 通义千问兼容接口 embedding 模型
EMBEDDING_DIMENSION = 1024
FAQ_MATCH_THRESHOLD = 0.85


def generate_embedding(text: str) -> list[float]:
    """调用 LLM 兼容接口生成 1024 维 embedding 向量。"""
    if not LLM_API_KEY:
        raise ValueError("LLM_API_KEY 未配置，无法生成 embedding")

    resp = requests.post(
        f"{LLM_API_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": EMBEDDING_MODEL,
            "input": text,
            "dimensions": EMBEDDING_DIMENSION,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]


def search_faq(query: str, threshold: float = FAQ_MATCH_THRESHOLD) -> str | None:
    """FAQ 向量检索。

    Args:
        query: 用户提问文本
        threshold: 相似度阈值（默认 0.85）

    Returns:
        匹配的答案字符串；无匹配或 embedding/DB 不可用时返回 None（静默降级到 LLM）。
    """
    try:
        embedding = generate_embedding(query)
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT question, answer,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM customer_service.faq_embeddings
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT 1
                """,
                (embedding, embedding),
            )
            row = cur.fetchone()
    except Exception:
        # embedding 生成失败或数据库不可用 → 降级，让 LLM 处理
        return None

    if row and row["similarity"] is not None and row["similarity"] >= threshold:
        return row["answer"]
    return None


def add_faq(question: str, answer: str, category: str = "general") -> int:
    """新增 FAQ 条目并生成 embedding，返回新记录 id。"""
    embedding = generate_embedding(question + " " + answer)
    metadata = json.dumps({"category": category})

    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO customer_service.faq_embeddings (question, answer, embedding, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (question, answer, embedding, metadata),
        )
        return cur.fetchone()["id"]

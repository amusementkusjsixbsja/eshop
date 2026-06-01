"""★ 小A：FAQ 知识库检索服务。

当前 FAQ 在 chat_router.py 中用关键词匹配实现。

如需向量检索：
  1. 确保 init.sql 中 customer_service.faq_embeddings 表已创建
  2. 填充 FAQ 问答对数据
  3. 使用 pgvector 进行余弦相似度检索：
     SELECT question, answer, 1 - (embedding <=> %s::vector) as similarity
     FROM customer_service.faq_embeddings
     ORDER BY similarity DESC LIMIT 1
  4. 相似度 > 阈值则返回匹配答案，否则 fallback
"""

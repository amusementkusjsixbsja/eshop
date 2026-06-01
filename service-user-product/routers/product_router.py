"""★ 小B：商品路由 — 将此文件的 mock 数据替换为真实数据库查询。

接口说明（对照需求文档）：
  - GET /products — 商品列表（分类筛选/关键词搜索，仅 on_sale 商品）
  - GET /products/hot — 热门商品（优先 Redis，前 5 条）
  - GET /products/{id} — 商品详情（优先 Redis Cache-Aside）
  - GET /categories/tree — 分类树（优先 Redis）
"""

from fastapi import APIRouter, Query

from shop_shared.common import success_response, paginated_response

router = APIRouter(prefix="/products", tags=["商品"])

MOCK_PRODUCTS = [
    {"id": 1, "name": "智能门锁 X1", "description": "指纹/密码/钥匙三合一智能门锁", "price": 1299.00, "image_url": "https://picsum.photos/seed/p1/400/400", "stock": 100, "category_id": 1, "category_name": "智能家居", "status": "on_sale"},
    {"id": 2, "name": "无线耳机 Pro", "description": "主动降噪，30小时续航", "price": 499.00, "image_url": "https://picsum.photos/seed/p2/400/400", "stock": 200, "category_id": 2, "category_name": "数码配件", "status": "on_sale"},
    {"id": 3, "name": "4K 网络摄像头", "description": "超清画质，360度全景监控", "price": 899.00, "image_url": "https://picsum.photos/seed/p3/400/400", "stock": 50, "category_id": 3, "category_name": "安防设备", "status": "on_sale"},
    {"id": 4, "name": "智能音箱", "description": "语音助手，高品质音效", "price": 299.00, "image_url": "https://picsum.photos/seed/p4/400/400", "stock": 150, "category_id": 1, "category_name": "智能家居", "status": "on_sale"},
    {"id": 5, "name": "USB-C 扩展坞", "description": "7合1多接口，4K输出", "price": 199.00, "image_url": "https://picsum.photos/seed/p5/400/400", "stock": 300, "category_id": 2, "category_name": "数码配件", "status": "on_sale"},
    {"id": 6, "name": "AI 智能门铃", "description": "人脸识别，远程可视对讲", "price": 699.00, "image_url": "https://picsum.photos/seed/p6/400/400", "stock": 80, "category_id": 3, "category_name": "安防设备", "status": "on_sale"},
    {"id": 7, "name": "智能台灯", "description": "护眼调光，手机控制", "price": 249.00, "image_url": "https://picsum.photos/seed/p7/400/400", "stock": 180, "category_id": 1, "category_name": "智能家居", "status": "on_sale"},
    {"id": 8, "name": "蓝牙追踪器", "description": "防丢神器，手机查找", "price": 89.00, "image_url": "https://picsum.photos/seed/p8/400/400", "stock": 500, "category_id": 2, "category_name": "数码配件", "status": "off_sale"},
]

MOCK_CATEGORIES = [
    {"id": 1, "name": "智能家居", "parent_id": None, "children": [{"id": 10, "name": "智能门锁", "parent_id": 1}, {"id": 11, "name": "智能照明", "parent_id": 1}]},
    {"id": 2, "name": "数码配件", "parent_id": None, "children": [{"id": 20, "name": "耳机", "parent_id": 2}, {"id": 21, "name": "充电设备", "parent_id": 2}]},
    {"id": 3, "name": "安防设备", "parent_id": None, "children": [{"id": 30, "name": "摄像头", "parent_id": 3}, {"id": 31, "name": "门铃", "parent_id": 3}]},
    {"id": 10, "name": "智能门锁", "parent_id": 1, "children": []},
    {"id": 11, "name": "智能照明", "parent_id": 1, "children": []},
    {"id": 20, "name": "耳机", "parent_id": 2, "children": []},
    {"id": 21, "name": "充电设备", "parent_id": 2, "children": []},
    {"id": 30, "name": "摄像头", "parent_id": 3, "children": []},
    {"id": 31, "name": "门铃", "parent_id": 3, "children": []},
]


@router.get("")
def list_products(
    category_id: int = Query(None, description="分类 ID"),
    keyword: str = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """商品列表：分类筛选 + 关键词搜索 + 分页。

    TODO: 小B — 替换为真实查询
      1. SELECT p.*, c.name as category_name FROM shop.products p
         JOIN shop.categories c ON p.category_id = c.id
         WHERE p.status = 'on_sale'
         AND (category_id IS NULL OR p.category_id IN (...子分类...))
         AND (keyword IS NULL OR p.name ILIKE '%keyword%')
         ORDER BY p.created_at DESC
         LIMIT %s OFFSET %s
      2. 分页逻辑
      3. 热门列表优先查 Redis (key: hot:products:list)
    """
    items = MOCK_PRODUCTS
    if category_id:
        items = [p for p in items if p["category_id"] == category_id]
    if keyword:
        items = [p for p in items if keyword.lower() in p["name"].lower()]
    on_sale = [p for p in items if p["status"] == "on_sale"]
    total = len(on_sale)
    return paginated_response(on_sale[:size], total, page, size)


@router.get("/hot")
def get_hot_products():
    """热门商品列表（前 5 条 on_sale 商品）。

    TODO: 小B — 替换为真实查询
      1. 优先查 Redis key: hot:products:list
      2. 未命中则 SELECT ... ORDER BY created_at DESC LIMIT 5
      3. 回写 Redis，TTL 5 分钟
    """
    hot = [p for p in MOCK_PRODUCTS if p["status"] == "on_sale"][:5]
    return success_response({"items": hot})


@router.get("/{product_id}")
def get_product_detail(product_id: int):
    """商品详情。

    TODO: 小B — 替换为真实查询（Cache-Aside）
      1. 优先查 Redis key: product:{id}
      2. 未命中则 SELECT FROM shop.products WHERE id = %s AND status = 'on_sale'
      3. 不存在则 raise NotFoundError("商品不存在")
      4. 回写 Redis，TTL 10 分钟
    """
    product = next((p for p in MOCK_PRODUCTS if p["id"] == product_id and p["status"] == "on_sale"), None)
    if not product:
        from shop_shared.common.exceptions import NotFoundError
        raise NotFoundError("商品不存在")
    return success_response(product)


# ─── 分类树挂在 products router 下（但也可以独立） ───

@router.get("/categories/tree", include_in_schema=False)
def get_category_tree():
    """分类树。

    TODO: 小B — 替换为真实查询（Cache-Aside）
      1. 优先查 Redis key: categories:tree
      2. 未命中则 SELECT * FROM shop.categories ORDER BY parent_id, sort_order
      3. 在 Python 中构造成树形结构
      4. 回写 Redis，TTL 30 分钟
    """
    return success_response({"items": [c for c in MOCK_CATEGORIES if c["parent_id"] is None]})

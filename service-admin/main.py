"""service-admin 入口 — 管理后台（分类管理 + 商品管理 + 查看订单）。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shop_shared.common import setup_logger, get_logger
from shop_shared.infrastructure import init_pool, close_pool, init_redis, close_redis
from shop_shared.middleware import (
    RequestIDMiddleware,
    RequestLogMiddleware,
    register_exception_handlers,
)

logger = get_logger("admin")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    init_pool()
    init_redis()
    logger.info("service-admin 服务启动")
    yield
    close_redis()
    close_pool()
    logger.info("service-admin 服务关闭")


app = FastAPI(
    title="电商平台 - 管理后台服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

from routers.category_router import router as category_router
from routers.product_router import router as product_router
from routers.order_router import router as order_router
from routers.review_router import router as review_router
from routers.faq_router import router as faq_router

app.include_router(category_router, prefix="/b-endpoint")
app.include_router(product_router, prefix="/b-endpoint")
app.include_router(order_router, prefix="/b-endpoint")
app.include_router(review_router, prefix="/b-endpoint")
app.include_router(faq_router, prefix="/b-endpoint")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "admin"}

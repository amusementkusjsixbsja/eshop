"""service-user-product 入口 — 用户认证 + 商品浏览 + 分类树。"""

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

logger = get_logger("user-product")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    setup_logger()
    init_pool()
    init_redis()
    logger.info("service-user-product 服务启动")
    yield
    # 关闭时
    close_redis()
    close_pool()
    logger.info("service-user-product 服务关闭")


app = FastAPI(
    title="电商平台 - 用户与商品服务",
    version="1.0.0",
    lifespan=lifespan,
)

# 中间件（注册顺序：RequestID → RequestLog → CORS）
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理器
register_exception_handlers(app)

# 路由
from routers.auth_router import router as auth_router
from routers.product_router import router as product_router
from routers.address_router import router as address_router
from routers.internal_router import router as internal_router

app.include_router(auth_router, prefix="/c-endpoint")
app.include_router(product_router, prefix="/c-endpoint")
app.include_router(address_router, prefix="/c-endpoint")
app.include_router(internal_router, prefix="/internal")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "user-product"}

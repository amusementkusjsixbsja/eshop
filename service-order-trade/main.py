"""service-order-trade 入口 — 购物车 + 订单 + 物流 + 售后 + 定时任务。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shop_shared.common import setup_logger, get_logger
from shop_shared.infrastructure import init_pool, close_pool, init_redis, close_redis
from shop_shared.infrastructure import init_scheduler, shutdown_scheduler, get_scheduler
from shop_shared.middleware import (
    RequestIDMiddleware,
    RequestLogMiddleware,
    register_exception_handlers,
)

logger = get_logger("order-trade")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    init_pool()
    init_redis()
    # 初始化调度器并注册定时任务（超时订单自动取消）
    init_scheduler()
    _register_scheduler_jobs()
    logger.info("service-order-trade 服务启动")
    yield
    shutdown_scheduler()
    close_redis()
    close_pool()
    logger.info("service-order-trade 服务关闭")


def _register_scheduler_jobs():
    """注册定时任务。"""
    scheduler = get_scheduler()
    if scheduler:
        from services.scheduler_jobs import cancel_timeout_orders
        scheduler.add_job(
            cancel_timeout_orders,
            trigger="interval",
            minutes=5,
            id="cancel_timeout_orders",
            replace_existing=True,
        )
        logger.info("定时任务已注册: 超时订单自动取消 (每5分钟)")


app = FastAPI(
    title="电商平台 - 购物车与交易服务",
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

from routers.cart_router import router as cart_router
from routers.order_router import router as order_router
from routers.logistics_router import router as logistics_router
from routers.after_sale_router import router as after_sale_router
from routers.internal_router import router as internal_router

app.include_router(cart_router, prefix="/c-endpoint")
app.include_router(order_router, prefix="/c-endpoint")
app.include_router(logistics_router, prefix="/c-endpoint")
app.include_router(after_sale_router, prefix="/c-endpoint")
app.include_router(internal_router, prefix="/internal")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "order-trade"}

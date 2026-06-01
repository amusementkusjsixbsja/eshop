"""ai-service 入口 — AI 客服对话服务。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shop_shared.common import setup_logger, get_logger

logger = get_logger("ai-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    logger.info("ai-service 启动")
    yield
    logger.info("ai-service 关闭")


app = FastAPI(
    title="电商平台 - AI 客服服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.chat_router import router as chat_router

app.include_router(chat_router, prefix="/api/ai")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ai-service"}

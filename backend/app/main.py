"""气象观测站网运维平台 后端服务入口。

启动：uvicorn app.main:app --host 127.0.0.1 --port 8000
健康检查：GET /api/health
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.modules_config import get_registry
from app.routers import ROUTERS
from app.store import store
from app.validate_modules import validate

# 启动即校验模块对齐：配置、示例数据、路由、前端声明对不上时直接起不来，
# 避免本地能跑、构建或部署后模块清单错位。
_alignment_errors = validate()
if _alignment_errors:
    raise RuntimeError(
        "模块对齐校验未通过，请先修正 modules.config.json 并运行 scripts/sync_modules.py：\n  - "
        + "\n  - ".join(_alignment_errors)
    )

app = FastAPI(title="气象观测站网运维平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module_router in ROUTERS:
    app.include_router(module_router)


@app.get("/api/health")
def health() -> dict[str, object]:
    """健康检查：确认服务已经监听、示例数据已经就绪。"""
    return {"ok": True, "app": settings.app_name, "modules": len(get_registry().modules)}


@app.get("/api/overview")
def overview() -> dict[str, object]:
    """运营概览：把各业务模块的待处理量汇总成看板卡片。"""
    return store.overview()

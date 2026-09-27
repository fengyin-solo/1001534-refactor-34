"""气象观测站网运维平台 后端服务入口。

启动：uvicorn app.main:app --host 127.0.0.1 --port 8000
健康检查：GET /api/health
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.modules import MODULES, validate_alignment
from app.routers import ROUTERS
from app.store import store

# 启动即校验：路由、服务、示例数据必须与 modules.config.json 对齐，
# 否则直接拒绝启动并给出可读的问题清单，而不是带病运行。
_alignment_problems = validate_alignment()
if _alignment_problems:
    raise RuntimeError(
        "模块对齐校验失败，请按 modules.config.json 补齐或修正以下问题：\n"
        + "\n".join(f"- {problem}" for problem in _alignment_problems)
    )

app = FastAPI(title="气象观测站网运维平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in ROUTERS:
    app.include_router(module.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    """健康检查：确认服务已经监听、示例数据已经就绪。"""
    return {"ok": True, "app": settings.app_name, "modules": len(MODULES)}


@app.get("/api/overview")
def overview() -> dict[str, object]:
    """运营概览：把各业务模块的待处理量汇总成看板卡片。"""
    return store.overview()

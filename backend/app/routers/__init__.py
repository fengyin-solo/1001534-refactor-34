"""根据模块配置动态生成每个业务模块的路由。

新增模块不需要再新建 router 文件：路由集合就是 modules.config.json 声明的集合，
启动校验会保证「配置模块 = 已注册路由 = 示例数据表」三处数量一致。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.modules_config import ModuleConfig
from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.generic import ModuleService


def build_router(module: ModuleConfig) -> APIRouter:
    router = APIRouter(prefix=module.api_prefix, tags=[module.label])
    service = ModuleService(module)

    def list_entries(
        keyword: str | None = Query(default=None, description=f"按{module.keyword_field}检索"),
        status: str | None = Query(
            default=None, description="、".join(module.statuses)
        ),
        page: int = 1,
        size: int = 20,
    ) -> PageResult[dict]:
        """按关键字与状态过滤列表；没有数据时返回空页，不报错。"""
        if size > 200:
            raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
        items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
        return PageResult(
            items=items, total=total, page=page, size=size, summary=service.counts()
        )

    def get_entry(entry_id: int) -> dict:
        """读取单条明细；不存在时给出可读的错误说明。"""
        entry = service.get_entry(entry_id)
        if entry is None:
            raise HTTPException(
                status_code=404, detail=f"{module.object_label} {entry_id} 不存在或已归档"
            )
        return entry

    def create_entry(payload: EntryPayload) -> ActionResult:
        """登记一条记录，缺字段时说明原因而不是静默丢弃。"""
        entry, missing = service.create_entry(payload.values)
        if missing:
            return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
        return ActionResult(ok=True, message=f"{module.object_label}已登记", entry=entry)

    def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
        """对单条记录执行配置里声明的动作；不允许的动作会被拦下并说明原因。"""
        action = str(payload.values.get("action") or "").strip()
        entry, message = service.run_action(entry_id, action)
        if entry is None:
            return ActionResult(ok=False, message=message)
        return ActionResult(ok=True, message=message, entry=entry)

    def export_entries() -> dict[str, Any]:
        """导出清单：返回当前模块的全量数据与统一口径统计。"""
        items = service.all_entries()
        return {"module": module.key, "total": len(items), "items": items, "summary": service.counts()}

    router.add_api_route("", list_entries, methods=["GET"], response_model=PageResult[dict])
    # /export 必须排在 /{entry_id} 前面，否则会当成条目 ID 解析。
    router.add_api_route("/export", export_entries, methods=["GET"])
    router.add_api_route("/{entry_id}", get_entry, methods=["GET"], response_model=dict)
    router.add_api_route("", create_entry, methods=["POST"], response_model=ActionResult)
    router.add_api_route(
        "/{entry_id}/actions", run_action, methods=["POST"], response_model=ActionResult
    )
    return router


def build_routers() -> list[APIRouter]:
    from app.modules_config import get_registry

    return [build_router(module) for module in get_registry().modules]


ROUTERS = build_routers()

"""业务服务：所有模块共用一套状态流转与筛选规则，差异只存在于配置里。

待处理/异常口径统一调用 ModuleConfig.annotate 派生，概览与列表不会再出现两套判断。
"""
from __future__ import annotations

from typing import Any

from app.modules_config import ModuleConfig
from app.store import store


class ModuleService:
    def __init__(self, module: ModuleConfig) -> None:
        self.module = module

    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(self.module.key)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get(self.module.keyword_field, ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        items = [self.module.annotate(dict(row)) for row in rows[start:start + size]]
        return items, total

    def all_entries(self) -> list[dict[str, Any]]:
        return [self.module.annotate(dict(row)) for row in store.rows(self.module.key)]

    def counts(self) -> dict[str, int]:
        """列表页顶部卡片与运营概览共用的统计口径。"""
        rows = [self.module.annotate(dict(row)) for row in store.rows(self.module.key)]
        return {
            "created": len(rows),
            "pending": sum(1 for row in rows if row["pending"]),
            "abnormal": sum(1 for row in rows if row["abnormal"]),
        }

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        row = store.find(self.module.key, entry_id)
        return self.module.annotate(dict(row)) if row is not None else None

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in self.module.required_fields if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(self.module.key)
        entry: dict[str, Any] = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in self.module.list_fields})
        entry["status"] = self.module.initial_status()
        rows.append(entry)
        return self.module.annotate(dict(entry)), []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(self.module.key, entry_id)
        if entry is None:
            return None, f"{self.module.object_label} {entry_id} 不存在或已归档"
        target = self.module.action_targets.get(action)
        if target is None:
            return None, f"动作「{action}」不属于{self.module.label}可执行范围"
        entry["status"] = target
        return self.module.annotate(entry), f"{self.module.object_label}已{action}"

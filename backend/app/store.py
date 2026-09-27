"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
待处理/异常的统计口径统一来自 modules.config.json，按记录的业务状态换算，
不在数据行里另存一份会过期的标记位。
"""
from __future__ import annotations

from typing import Any

from app.modules import MODULES
from app.seed import SEED_ROWS


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def overview(self) -> dict[str, object]:
        """运营概览：模块清单与待处理/异常口径都取统一配置，和各模块列表页一致。"""
        modules: list[dict[str, object]] = []
        for spec in MODULES:
            rows = self.rows(spec.key)
            flags = [spec.flags_for(row.get("status")) for row in rows]
            modules.append({
                "key": spec.key,
                "name": spec.label,
                "created": len(rows),
                "pending": sum(1 for pending, _ in flags if pending),
                "abnormal": sum(1 for _, abnormal in flags if abnormal),
            })
        cards = [
            {"label": "业务模块", "value": len(modules)},
            {"label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"cards": cards, "modules": modules}


store = Store()

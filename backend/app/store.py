"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
表集合与模块顺序都以 modules.config.json 为准，不再各维护一份清单。
"""
from __future__ import annotations

from typing import Any

from app.modules_config import get_registry
from app.seed import SEED_ROWS


class Store:
    def __init__(self) -> None:
        registry = get_registry()
        self._tables: dict[str, list[dict[str, Any]]] = {
            module.key: [dict(row) for row in SEED_ROWS[module.key]] for module in registry.modules
        }

    def module_names(self) -> list[str]:
        """按配置声明顺序返回模块 key，概览与导航顺序一致。"""
        return [module.key for module in get_registry().modules]

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def overview(self) -> dict[str, object]:
        """运营概览：卡片数字直接由模块汇总行求和，刷新后卡片与汇总必然一致。"""
        registry = get_registry()
        modules: list[dict[str, object]] = []
        for module in registry.modules:
            rows = [module.annotate(dict(row)) for row in self.rows(module.key)]
            modules.append({
                "key": module.key,
                "name": module.label,
                "created": len(rows),
                "pending": sum(1 for row in rows if row["pending"]),
                "abnormal": sum(1 for row in rows if row["abnormal"]),
            })
        totals = {
            "modules": len(modules),
            "created": sum(int(item["created"]) for item in modules),
            "pending": sum(int(item["pending"]) for item in modules),
            "abnormal": sum(int(item["abnormal"]) for item in modules),
        }
        cards = [
            {"key": card["key"], "label": card["label"], "value": totals[card["key"]]}
            for card in registry.cards
        ]
        return {"cards": cards, "modules": modules}


store = Store()

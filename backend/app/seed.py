"""示例数据：按 modules.config.json 的声明为每个模块生成示例记录。

模块数量、记录条数、状态取值全部来自配置，不再手写一份与口径脱节的状态位：
每条记录的 pending/abnormal 都由配置里的 pendingStatuses/abnormalStatuses 派生，
与运营概览、模块列表看到的完全一致。
"""
from __future__ import annotations

from datetime import date
from typing import Any

from app.modules_config import ModuleConfig, get_registry

# 视为日期/数值的字段名后缀或全名；其余按普通文本生成样例值。
DATE_FIELD_HINTS = ("日期", "时段", "期限")
INTEGER_FIELDS = {"结存数量"}
MONEY_FIELDS = {"合同金额", "应付金额", "已付金额"}

# 三条示例记录的状态槽位：待处理、正常、异常/另一态；异常口径为空时退回一个非待处理状态。
NORMAL_SLOT = 1
ABNORMAL_SLOT = 2


def _seed_statuses(module: ModuleConfig) -> list[str]:
    statuses = list(module.statuses)
    pending = [status for status in statuses if status in module.pending_statuses]
    normal = [
        status
        for status in statuses
        if status not in module.pending_statuses and status not in module.abnormal_statuses
    ]
    abnormal = [status for status in statuses if status in module.abnormal_statuses]
    chosen = [
        pending[0] if pending else statuses[0],
        normal[0] if normal else statuses[min(NORMAL_SLOT, len(statuses) - 1)],
        (abnormal[0] if abnormal else normal[-1] if normal else statuses[-1]),
    ]
    # 保证三条槽位尽量互不相同。
    if len(set(chosen)) < 3:
        for status in statuses:
            if status not in chosen:
                chosen[ABNORMAL_SLOT] = status
                break
    return chosen


def _field_value(module: ModuleConfig, field: str, index: int) -> Any:
    if field == module.list_fields[0]:
        return f"{module.code_prefix}-{index:04d}"
    if field in INTEGER_FIELDS:
        return index * 10
    if field in MONEY_FIELDS:
        return index * 12.5
    if field.endswith(DATE_FIELD_HINTS):
        return date(2026, 9, index).isoformat()
    return f"{module.label}样例{index}"


def build_seed_rows() -> dict[str, list[dict[str, Any]]]:
    """按配置生成全部示例表，并按统一口径补上 pending/abnormal 状态位。"""
    tables: dict[str, list[dict[str, Any]]] = {}
    for module in get_registry().modules:
        statuses = _seed_statuses(module)
        rows: list[dict[str, Any]] = []
        for index in range(1, module.seed_count + 1):
            row: dict[str, Any] = {"id": index}
            row.update({field: _field_value(module, field, index) for field in module.list_fields})
            row["status"] = statuses[(index - 1) % len(statuses)]
            rows.append(module.annotate(row))
        tables[module.key] = rows
    return tables


SEED_ROWS: dict[str, list[dict[str, Any]]] = build_seed_rows()

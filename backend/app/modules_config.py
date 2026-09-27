"""模块清单与统计口径配置：前后端共用 modules.config.json 的后端加载层。

这是模块清单的唯一事实来源：
- 路由注册（app.routers）按这里的 key/apiPrefix 生成；
- 示例数据（app.seed）按这里的字段与 seedCount 生成；
- 待处理/异常口径由 pendingStatuses/abnormalStatuses 统一派生，概览和列表共用。

新增模块时只需要改 modules.config.json，启动时 validate_alignment 会拦住
「配置、示例数据、路由声明」对不上的情况。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parents[2] / "modules.config.json"


@dataclass(frozen=True)
class ModuleAction:
    label: str
    target: str


@dataclass(frozen=True)
class ModuleConfig:
    key: str
    label: str
    object_label: str
    path: str
    api_prefix: str
    code_prefix: str
    list_fields: tuple[str, ...]
    required_fields: tuple[str, ...]
    keyword_field: str
    statuses: tuple[str, ...]
    pending_statuses: frozenset[str]
    abnormal_statuses: frozenset[str]
    actions: tuple[ModuleAction, ...]
    seed_count: int

    @property
    def action_targets(self) -> dict[str, str]:
        return {action.label: action.target for action in self.actions}

    def initial_status(self) -> str:
        return self.statuses[0]

    def is_pending(self, status: str) -> bool:
        return status in self.pending_statuses

    def is_abnormal(self, status: str) -> bool:
        return status in self.abnormal_statuses

    def annotate(self, row: dict[str, Any]) -> dict[str, Any]:
        """按统一口径给一行数据补 pending/abnormal 状态位。

        概览汇总与列表展示都走这里，保证两处永远一致。
        """
        status = str(row.get("status", ""))
        row["pending"] = self.is_pending(status)
        row["abnormal"] = self.is_abnormal(status)
        return row


@dataclass(frozen=True)
class ModuleRegistry:
    cards: tuple[dict[str, str], ...]
    modules: tuple[ModuleConfig, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "_index", {})

    def _by(self, attr: str) -> dict[str, ModuleConfig]:
        index = self.__dict__.get("_index", {})
        if attr not in index:
            index[attr] = {getattr(module, attr): module for module in self.modules}
        return index[attr]

    def get(self, key: str) -> ModuleConfig:
        return self._by("key")[key]

    def by_api_prefix(self, prefix: str) -> ModuleConfig:
        return self._by("api_prefix")[prefix]

    def keys(self) -> list[str]:
        return [module.key for module in self.modules]


REQUIRED_KEYS = (
    "key",
    "label",
    "objectLabel",
    "path",
    "apiPrefix",
    "codePrefix",
    "listFields",
    "requiredFields",
    "keywordField",
    "statuses",
    "pendingStatuses",
    "abnormalStatuses",
    "actions",
    "seedCount",
)


def _parse_module(raw: dict[str, Any]) -> ModuleConfig:
    missing = [key for key in REQUIRED_KEYS if key not in raw]
    if missing:
        raise ValueError(f"模块配置缺少字段：{', '.join(missing)}（模块：{raw.get('key', '?')}）")
    statuses = tuple(raw["statuses"])
    status_set = set(statuses)
    pending = frozenset(raw["pendingStatuses"])
    abnormal = frozenset(raw["abnormalStatuses"])
    for name, values in (("pendingStatuses", pending), ("abnormalStatuses", abnormal)):
        unknown = values - status_set
        if unknown:
            raise ValueError(
                f"模块 {raw['key']} 的 {name} 含未声明状态：{', '.join(sorted(unknown))}"
            )
    actions = tuple(ModuleAction(label=str(item["label"]), target=str(item["target"])) for item in raw["actions"])
    for action in actions:
        if action.target not in status_set:
            raise ValueError(
                f"模块 {raw['key']} 的动作「{action.label}」目标状态「{action.target}」不在 statuses 里"
            )
    required = tuple(raw["requiredFields"])
    listed = tuple(raw["listFields"])
    for field in required:
        if field not in listed:
            raise ValueError(f"模块 {raw['key']} 的必填字段「{field}」不在 listFields 里")
    if raw["keywordField"] not in listed:
        raise ValueError(f"模块 {raw['key']} 的检索字段「{raw['keywordField']}」不在 listFields 里")
    if int(raw["seedCount"]) <= 0:
        raise ValueError(f"模块 {raw['key']} 的 seedCount 必须为正数")
    return ModuleConfig(
        key=str(raw["key"]),
        label=str(raw["label"]),
        object_label=str(raw["objectLabel"]),
        path=str(raw["path"]),
        api_prefix=str(raw["apiPrefix"]),
        code_prefix=str(raw["codePrefix"]),
        list_fields=listed,
        required_fields=required,
        keyword_field=str(raw["keywordField"]),
        statuses=statuses,
        pending_statuses=pending,
        abnormal_statuses=abnormal,
        actions=actions,
        seed_count=int(raw["seedCount"]),
    )


def load_config(path: Path | None = None) -> ModuleRegistry:
    """读取并校验 modules.config.json，结构不合法时直接抛错。"""
    target = path or CONFIG_PATH
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"找不到模块配置文件：{target}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"模块配置文件不是合法 JSON：{target}（{exc}）") from exc

    modules = tuple(_parse_module(item) for item in raw.get("modules", []))
    if not modules:
        raise ValueError("modules.config.json 里没有声明任何模块")

    # 各唯一标识不允许重复，否则路由/导航/示例表会互相串数据。
    for values, field_name in (
        ([m.key for m in modules], "key"),
        ([m.path for m in modules], "path"),
        ([m.api_prefix for m in modules], "apiPrefix"),
        ([m.code_prefix for m in modules], "codePrefix"),
    ):
        duplicated = {value for value in values if values.count(value) > 1}
        if duplicated:
            raise ValueError(f"模块配置的 {field_name} 重复：{', '.join(sorted(duplicated))}")

    cards = tuple(
        {"key": str(card["key"]), "label": str(card["label"])} for card in raw.get("cards", [])
    )
    if {card["key"] for card in cards} != {"modules", "created", "pending", "abnormal"}:
        raise ValueError("cards 必须且只能包含 modules/created/pending/abnormal 四张卡片")
    return ModuleRegistry(cards=cards, modules=modules)


@lru_cache(maxsize=1)
def get_registry() -> ModuleRegistry:
    return load_config()

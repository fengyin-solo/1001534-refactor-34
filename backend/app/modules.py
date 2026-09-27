"""模块清单与统计口径的唯一来源：读取仓库根目录的 modules.config.json。

前端（导航、路由、概览、列表统计）与后端（路由、服务、示例数据）都围绕这份配置对齐；
`validate_alignment()` 在服务启动时运行，发现前后端模块或示例数据不一致就直接报错，
避免静默起出一个口径对不上的服务。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path(
    os.environ.get("MODULES_CONFIG")
    or (Path(__file__).resolve().parents[2] / "modules.config.json")
)


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    label: str
    entity: str
    pending_statuses: tuple[str, ...]
    abnormal_statuses: tuple[str, ...]

    def flags_for(self, status: object) -> tuple[bool, bool]:
        """按统一口径把业务状态换算成（待处理, 异常）两个标记。"""
        text = str(status or "")
        return text in self.pending_statuses, text in self.abnormal_statuses


def _load_modules() -> list[ModuleSpec]:
    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"模块配置文件读取失败：{CONFIG_PATH}（{exc}）") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"模块配置文件不是合法 JSON：{CONFIG_PATH}（{exc}）") from exc
    modules = [
        ModuleSpec(
            key=str(item["key"]),
            label=str(item["label"]),
            entity=str(item.get("entity") or item["label"]),
            pending_statuses=tuple(str(s) for s in item.get("pendingStatuses", [])),
            abnormal_statuses=tuple(str(s) for s in item.get("abnormalStatuses", [])),
        )
        for item in payload.get("modules", [])
    ]
    keys = [module.key for module in modules]
    if not modules or len(set(keys)) != len(keys):
        raise RuntimeError(f"模块配置文件 {CONFIG_PATH} 里的模块清单为空或 key 重复")
    return modules


MODULES: list[ModuleSpec] = _load_modules()
MODULE_KEYS: list[str] = [module.key for module in MODULES]
MODULE_MAP: dict[str, ModuleSpec] = {module.key: module for module in MODULES}


def validate_alignment() -> list[str]:
    """检查后端路由、服务、示例数据是否与模块配置对齐，返回问题清单（空表示通过）。"""
    problems: list[str] = []
    root = CONFIG_PATH.parent
    expected = sorted(MODULE_KEYS)

    for kind in ("routers", "services"):
        folder = root / "backend" / "app" / kind
        actual = sorted(p.stem for p in folder.glob("*.py") if p.stem != "__init__")
        if actual != expected:
            missing = sorted(set(expected) - set(actual))
            extra = sorted(set(actual) - set(expected))
            detail = []
            if missing:
                detail.append(f"缺少 {', '.join(missing)}")
            if extra:
                detail.append(f"多出 {', '.join(extra)}")
            problems.append(f"backend/app/{kind}/ 与模块配置不一致：{'；'.join(detail)}")

    from app.seed import SEED_ROWS

    if sorted(SEED_ROWS) != expected:
        missing = sorted(set(expected) - set(SEED_ROWS))
        extra = sorted(set(SEED_ROWS) - set(expected))
        detail = []
        if missing:
            detail.append(f"缺少 {', '.join(missing)}")
        if extra:
            detail.append(f"多出 {', '.join(extra)}")
        problems.append(f"示例数据 SEED_ROWS 与模块配置不一致：{'；'.join(detail)}")

    from app.routers import ROUTERS

    prefixes = sorted(getattr(module.router, "prefix", "") for module in ROUTERS)
    if prefixes != sorted(f"/api/{key}" for key in expected):
        problems.append(
            "backend/app/routers/__init__.py 注册的 ROUTERS 与模块配置不一致，"
            f"当前为 {', '.join(prefixes) or '（空）'}"
        )

    return problems

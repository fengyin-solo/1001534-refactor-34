"""模块对齐校验：本地启动、镜像构建、部署时都跑一遍。

校验「依赖声明 = 模块清单 = 示例数据 = 已注册路由」四处是否一致：
1. modules.config.json 自身结构合法、状态口径自洽；
2. 示例数据（seed）里每个配置模块都有表、行数等于 seedCount、状态都在 statuses 内；
3. 注册到 FastAPI 的模块路由与配置模块一一对应；
4. 前端依赖声明（frontend/src/modules.frontend.json，由校验脚本从同一份配置生成）
   里的模块数量、key、口径与配置一致。

任一项不满足就以非零码退出，让 dev/build/部署直接失败，而不是把不一致带到线上。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
FRONTEND_MANIFEST = REPO_ROOT / "frontend" / "src" / "modules.frontend.json"


def validate() -> list[str]:
    # 延迟导入：导入过程本身依赖配置，先确认配置可读。
    from app.modules_config import load_config
    from app.seed import SEED_ROWS

    errors: list[str] = []
    registry = load_config()
    config_keys = registry.keys()
    declared_count = len(config_keys)

    # 1. 示例数据表与模块配置一致：表数量、表名、行数、状态与口径逐项核对。
    seed_keys = set(SEED_ROWS)
    missing_tables = [key for key in config_keys if key not in seed_keys]
    extra_tables = sorted(seed_keys - set(config_keys))
    if missing_tables:
        errors.append(f"示例数据缺少模块表：{', '.join(missing_tables)}")
    if extra_tables:
        errors.append(f"示例数据存在未声明模块表：{', '.join(extra_tables)}")
    if len(seed_keys) != declared_count:
        errors.append(
            f"示例数据表数量 {len(seed_keys)} 与配置声明模块数 {declared_count} 不一致"
        )
    for module in registry.modules:
        rows = SEED_ROWS.get(module.key, [])
        if len(rows) != module.seed_count:
            errors.append(
                f"模块 {module.key} 示例数据 {len(rows)} 条，配置声明 seedCount={module.seed_count}"
            )
        ids = [int(row.get("id", -1)) for row in rows]
        if sorted(ids) != list(range(1, len(rows) + 1)):
            errors.append(f"模块 {module.key} 示例记录 id 必须从 1 连续编号")
        for row in rows:
            status = row.get("status")
            if status not in module.statuses:
                errors.append(f"模块 {module.key} 示例记录 id={row.get('id')} 状态「{status}」不在 statuses 内")
            if row.get("pending") != module.is_pending(str(status)):
                errors.append(f"模块 {module.key} 示例记录 id={row.get('id')} pending 与口径不一致")
            if row.get("abnormal") != module.is_abnormal(str(status)):
                errors.append(f"模块 {module.key} 示例记录 id={row.get('id')} abnormal 与口径不一致")

    # 2. 已注册路由与模块配置一致（动态构建，理论上恒等，仍显式核对前缀）。
    #    路由构建依赖 fastapi，未装依赖时单独标注，不影响其余纯配置类校验。
    try:
        from app.routers import ROUTERS
    except ModuleNotFoundError as exc:
        errors.append(f"无法导入路由模块做对齐校验（依赖未安装？）：{exc.name}")
    else:
        route_prefixes = {router.prefix for router in ROUTERS}
        expected_prefixes = {module.api_prefix for module in registry.modules}
        if len(ROUTERS) != declared_count:
            errors.append(
                f"注册路由数量 {len(ROUTERS)} 与配置声明模块数 {declared_count} 不一致"
            )
        if route_prefixes != expected_prefixes:
            only_routes = sorted(route_prefixes - expected_prefixes)
            only_config = sorted(expected_prefixes - route_prefixes)
            if only_routes:
                errors.append(f"路由存在未声明模块：{', '.join(only_routes)}")
            if only_config:
                errors.append(f"声明模块缺少路由：{', '.join(only_config)}")

    # 3. 前端依赖声明与模块配置一致（同一份 JSON 的生成产物）。
    if not FRONTEND_MANIFEST.exists():
        errors.append(
            f"缺少前端模块声明 {FRONTEND_MANIFEST.relative_to(REPO_ROOT)}，请先运行 scripts/sync_modules.py"
        )
    else:
        try:
            manifest = json.loads(FRONTEND_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"前端模块声明不是合法 JSON：{exc}")
        else:
            if manifest.get("version") != registry_version():
                errors.append("前端模块声明版本落后，请重新运行 scripts/sync_modules.py")
            frontend = manifest.get("modules", [])
            if len(frontend) != len(config_keys):
                errors.append(
                    f"前端声明模块数 {len(frontend)} 与配置模块数 {len(config_keys)} 不一致"
                )
            for item, module in zip(frontend, registry.modules):
                if item.get("key") != module.key:
                    errors.append(
                        f"前端模块声明顺序/key 不一致：{item.get('key')} != {module.key}"
                    )
                    continue
                if set(item.get("pendingStatuses", [])) != set(module.pending_statuses):
                    errors.append(f"模块 {module.key} 待处理口径前后端不一致")
                if set(item.get("abnormalStatuses", [])) != set(module.abnormal_statuses):
                    errors.append(f"模块 {module.key} 异常口径前后端不一致")

    return errors


def registry_version() -> int:
    from app.modules_config import CONFIG_PATH

    return int(json.loads(CONFIG_PATH.read_text(encoding="utf-8")).get("version", 0))


def main() -> int:
    try:
        errors = validate()
    except Exception as exc:  # noqa: BLE001 - 校验脚本要把任何异常转成可读的失败信息
        print(f"模块对齐校验未通过：{exc}", file=sys.stderr)
        return 1
    if errors:
        print("模块对齐校验未通过：", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"模块对齐校验通过：{len(get_registry_modules())} 个模块前后端与示例数据一致。")
    return 0


def get_registry_modules() -> list:
    from app.modules_config import get_registry

    return get_registry().modules


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""按 modules.config.json 校验前后端模块是否对齐。

只用标准库（AST 解析源码），本地开发（make check / make backend / make frontend）、
后端 Docker 构建都会跑这份校验；前端另有 scripts/check-modules.mjs 挂在 npm 的
predev/prebuild 上。新增模块时按报错清单补齐文件即可，不用再去多处对名单。
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "modules.config.json"


def load_module_keys(problems: list[str]) -> list[str]:
    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except OSError as exc:
        problems.append(f"模块配置文件读取失败：{CONFIG_PATH}（{exc}）")
        return []
    except json.JSONDecodeError as exc:
        problems.append(f"模块配置文件不是合法 JSON：{CONFIG_PATH}（{exc}）")
        return []
    modules = payload.get("modules")
    if not isinstance(modules, list) or not modules:
        problems.append("modules.config.json 里的 modules 清单为空或不是数组")
        return []
    keys: list[str] = []
    for index, item in enumerate(modules):
        key = item.get("key") if isinstance(item, dict) else None
        label = item.get("label") if isinstance(item, dict) else None
        if not key or not label:
            problems.append(f"modules.config.json 第 {index + 1} 个模块缺少 key 或 label")
            continue
        for field in ("pendingStatuses", "abnormalStatuses"):
            if not isinstance(item.get(field), list):
                problems.append(f"模块 {key} 的 {field} 不是数组，待处理/异常口径无法统一")
        keys.append(str(key))
    if len(set(keys)) != len(keys):
        problems.append("modules.config.json 里模块 key 有重复")
    return keys


def seed_keys() -> set[str]:
    """不导入后端依赖，直接字面量解析 seed.py 拿到示例数据的模块清单。"""
    tree = ast.parse((ROOT / "backend" / "app" / "seed.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "SEED_ROWS":
            return set(ast.literal_eval(node.value))
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SEED_ROWS" for target in node.targets
        ):
            return set(ast.literal_eval(node.value))
    return set()


def registered_router_keys() -> set[str]:
    """解析 routers/__init__.py 里 ROUTERS 列表引用的模块别名（router_<key>）。"""
    tree = ast.parse((ROOT / "backend" / "app" / "routers" / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "ROUTERS" for target in node.targets
        ):
            keys = set()
            for element in node.value.elts:
                if isinstance(element, ast.Name) and element.id.startswith("router_"):
                    keys.add(element.id.removeprefix("router_"))
            return keys
    return set()


def diff_detail(expected: set[str], actual: set[str]) -> str:
    detail = []
    if missing := sorted(expected - actual):
        detail.append(f"缺少 {', '.join(missing)}")
    if extra := sorted(actual - expected):
        detail.append(f"多出 {', '.join(extra)}")
    return "；".join(detail)


def check_backend(expected: set[str], problems: list[str]) -> None:
    for kind in ("routers", "services"):
        folder = ROOT / "backend" / "app" / kind
        actual = {p.stem for p in folder.glob("*.py") if p.stem != "__init__"}
        if actual != expected:
            problems.append(f"backend/app/{kind}/ 与模块配置不一致：{diff_detail(expected, actual)}")

    if (actual := seed_keys()) != expected:
        problems.append(f"示例数据 backend/app/seed.py 与模块配置不一致：{diff_detail(expected, actual)}")

    if (actual := registered_router_keys()) != expected:
        problems.append(
            f"backend/app/routers/__init__.py 注册的 ROUTERS 与模块配置不一致：{diff_detail(expected, actual)}"
        )


def check_frontend(expected: set[str], problems: list[str]) -> None:
    views = ROOT / "frontend" / "src" / "views"
    actual = {p.parent.name for p in views.glob("*/index.vue")}
    if actual != expected:
        problems.append(f"frontend/src/views/ 与模块配置不一致：{diff_detail(expected, actual)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="按 modules.config.json 校验前后端模块对齐")
    parser.add_argument("--backend", action="store_true", help="只校验后端")
    parser.add_argument("--frontend", action="store_true", help="只校验前端")
    args = parser.parse_args()
    check_all = not (args.backend or args.frontend)

    problems: list[str] = []
    keys = set(load_module_keys(problems))
    if keys:
        if check_all or args.backend:
            check_backend(keys, problems)
        if check_all or args.frontend:
            check_frontend(keys, problems)

    if problems:
        print("模块对齐校验失败：", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"模块对齐校验通过：{len(keys)} 个模块（{CONFIG_PATH.name}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

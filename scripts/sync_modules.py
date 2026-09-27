#!/usr/bin/env python3
"""把仓库根目录的 modules.config.json 投影成前端可用的模块声明。

只此一处可以写 frontend/src/modules.frontend.json，前端代码一律 import 生成产物，
不要手写第二份模块清单。后端 validate_modules 会校验生成产物与源配置没有偏差，
所以本地 dev、vite build、镜像构建任何一步用了过期声明都会直接失败。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "modules.config.json"
TARGET = REPO_ROOT / "frontend" / "src" / "modules.frontend.json"

# 前端渲染需要的字段白名单：保持精简，避免把后端细节泄漏给构建产物。
MODULE_FIELDS = (
    "key",
    "label",
    "objectLabel",
    "path",
    "apiPrefix",
    "listFields",
    "requiredFields",
    "keywordField",
    "statuses",
    "pendingStatuses",
    "abnormalStatuses",
    "actions",
    "seedCount",
)


def main() -> int:
    try:
        config = json.loads(SOURCE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"读取模块配置失败：{exc}", file=sys.stderr)
        return 1
    modules = []
    for module in config.get("modules", []):
        modules.append({field: module[field] for field in MODULE_FIELDS})
    manifest = {
        "version": config["version"],
        "source": "modules.config.json",
        "cards": config["cards"],
        "modules": modules,
    }
    TARGET.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已同步 {len(modules)} 个模块声明到 {TARGET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

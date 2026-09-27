#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
# 启动前先校验模块配置与前后端声明是否对齐，对不上直接退出。
.venv/bin/python -m app.validate_modules
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

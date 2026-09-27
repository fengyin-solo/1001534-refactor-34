.PHONY: install backend frontend check

# 模块对齐校验：前后端路由/服务/页面/示例数据都必须与 modules.config.json 一致
check:
	python3 scripts/check_modules.py

install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd frontend && npm install

backend: check
	cd backend && ./run.sh

frontend: check
	cd frontend && npm run dev

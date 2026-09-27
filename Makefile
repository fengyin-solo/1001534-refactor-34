.PHONY: install sync check check-backend check-frontend backend frontend

# 修改 modules.config.json 后执行：把同一份配置投影到前端声明
sync:
	python3 scripts/sync_modules.py

# 前后端模块对齐校验：本地启动前、CI、部署前都应执行
check: check-backend check-frontend

check-backend:
	cd backend && python3 -m app.validate_modules

check-frontend:
	cd frontend && node scripts/check-modules.cjs

install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd frontend && npm install

backend: check-backend
	cd backend && ./run.sh

frontend: check-frontend
	cd frontend && npm run dev

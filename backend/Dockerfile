FROM python:3.12-slim
# 构建上下文是仓库根目录（见 docker-compose.yml），
# 镜像内保持与仓库相同的相对布局，modules.config.json 才能落在后端约定的位置。
WORKDIR /srv
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY modules.config.json modules.config.json
COPY scripts/ scripts/
COPY backend/ backend/
# 构建时即校验模块对齐，不一致直接构建失败
RUN python scripts/check_modules.py --backend
WORKDIR /srv/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

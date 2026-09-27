FROM python:3.12-slim
WORKDIR /srv
# 先装依赖，利用层缓存
COPY backend/requirements.txt /srv/backend/requirements.txt
RUN pip install --no-cache-dir -r /srv/backend/requirements.txt
# 后端代码与跨端共享的模块清单一起进镜像
COPY backend /srv/backend
COPY modules.config.json /srv/modules.config.json
# 镜像构建时即校验：模块配置、示例数据、前端声明对不上就让构建失败，不把问题带到部署
RUN cd /srv/backend && python -m app.validate_modules
WORKDIR /srv/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

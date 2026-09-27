FROM node:20-alpine
# 构建上下文是仓库根目录（见 docker-compose.yml），
# modules.config.json 放在前端目录的上一级，与本地开发的相对位置一致。
WORKDIR /srv/frontend
COPY frontend/package.json ./
RUN npm install
COPY modules.config.json /srv/modules.config.json
COPY frontend/ ./
# 构建时即校验模块对齐，不一致直接构建失败
RUN node scripts/check-modules.mjs
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

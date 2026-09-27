FROM node:20-alpine
WORKDIR /srv/web
# 模块清单的唯一事实来源在仓库根目录，构建上下文必须是仓库根（见 docker-compose.yml）。
COPY frontend/package.json ./
RUN npm install
# 源配置与脚本先进镜像，构建时重新投影前端声明，避免提交了过期声明也能蒙混过关
COPY modules.config.json /srv/modules.config.json
COPY frontend/scripts ./scripts
COPY frontend .
RUN node scripts/sync-modules.cjs && node scripts/check-modules.cjs
EXPOSE 5173
# dev 启动前 predev 会再次校验模块对齐
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# 气象观测站网运维平台

面向区域气象观测站网的站点入网、传感器检定、观测数据质控、供电通信保障与运维结算的一体化运行监控后台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── modules.config.json     业务模块清单与待处理/异常统计口径的唯一来源
├── scripts/
│   └── check_modules.py    按配置校验前后端模块是否对齐（make check）
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/            每个业务模块一个页面
│   ├── src/modules.ts        读取 modules.config.json 的前端入口
│   ├── src/api/              统一请求封装
│   ├── src/stores/           会话与筛选状态
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/modules.py        读取 modules.config.json 的后端入口与启动校验
│   ├── app/routers/          每个业务模块一组接口
│   ├── app/services/         业务规则与状态流转
│   └── app/store.py          内存数据仓库与示例数据
├── .gitignore
└── docker-compose.yml
```

## 模块清单与统计口径

`modules.config.json` 是唯一一份模块配置，前后端都从这里取数：

- 每个模块登记 `key`（目录名/接口前缀）、`label`（中文名）、`entity`（业务对象）。
- `pendingStatuses` / `abnormalStatuses` 是待处理与异常的统一口径：
  运营概览的汇总、各模块列表页的统计卡片都按记录的业务状态落不落在
  这两个集合里来换算，不再各自判断，两处必然一致。
- 前端的侧边导航、路由、运营概览的模块行都由它生成；接口不可用时概览页
  会列出全部模块并给出可读的原因说明，不会回退到写死的假数据。

校验贯穿整个流程，不一致就直接失败并打印问题清单：

- 本地启动：`make backend` / `make frontend` 前会先跑 `make check`
  （即 `python3 scripts/check_modules.py`），前端 `npm run dev` / `npm run build`
  也会先跑 `frontend/scripts/check-modules.mjs`。
- 后端启动：`app/main.py` 导入时执行同样的对齐校验，失败则拒绝启动。
- 构建部署：前后端 Dockerfile 在构建期分别跑校验脚本，镜像构建即卡口。

新增模块的步骤（校验脚本会逐项提醒缺什么）：

1. 在 `modules.config.json` 里登记模块 key、中文名与待处理/异常口径。
2. 补后端 `app/routers/<key>.py`、`app/services/<key>.py`，并在
   `app/routers/__init__.py` 的 `ROUTERS` 里注册。
3. 补前端 `frontend/src/views/<key>/index.vue`。
4. 在 `app/seed.py` 里为该模块准备示例数据。
5. 跑 `make check` 确认前后端对齐。

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh
```

健康检查：`curl http://127.0.0.1:8000/api/health`

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`。

## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 观测站点 | `station` | 观测站点 | 站点编码、站点名称、站点类别 |
| 观测传感器 | `sensor` | 观测传感器 | 传感器编号、所属站点、观测要素 |
| 观测记录 | `observation` | 观测记录 | 记录编号、所属站点、观测要素 |
| 数据质控 | `quality` | 质控任务 | 质控编号、质控时段、涉及站点 |
| 设备标定 | `calibration` | 标定记录 | 标定编号、标定对象、标定机构 |
| 数据传输 | `transmission` | 传输链路 | 链路编号、所属站点、传输方式 |
| 供电保障 | `power` | 供电单元 | 供电编号、所属站点、供电方式 |
| 站网布局 | `layout` | 站网规划 | 规划编号、规划区域、目标站距 |
| 巡检任务 | `inspection` | 巡检单 | 巡检单号、巡检站点、巡检人员 |
| 故障处置 | `fault` | 故障记录 | 故障编号、涉及站点、故障现象 |
| 备件器材 | `sparepart` | 备件器材 | 备件编号、备件名称、适用型号 |
| 元数据登记 | `metainfo` | 元数据记录 | 元数据编号、关联站点、元数据类型 |
| 告警监测 | `alarm` | 告警记录 | 告警编号、告警来源、告警类型 |
| 通信设备 | `comm` | 通信设备 | 设备编号、设备名称、设备型号 |
| 服务保障 | `service` | 服务事项 | 事项编号、服务对象、服务类别 |
| 运维合同 | `contract` | 运维合同 | 合同编号、服务单位、合同金额 |
| 经费结算 | `settlement` | 结算单 | 结算单号、关联合同、结算周期 |
| 人员培训 | `training` | 培训记录 | 培训编号、培训主题、培训对象 |

## 约定

- 模块清单与待处理/异常口径以根目录 `modules.config.json` 为准，见上节。
- 每个模块的前端页面在 `frontend/src/views/<模块>/index.vue`，后端接口在
  `backend/app/routers/<模块>.py`，业务规则在 `backend/app/services/<模块>.py`。
- 列表接口统一返回 `{ items, total, page, size }`，动作接口统一返回 `{ ok, message }`。
- 状态流转只允许在 `app/services` 里改，路由层不做业务判断。
- 待处理/异常不在数据行里存标记位，统一按 `modules.config.json` 的口径
  从业务状态实时换算，概览与列表页因此始终一致。

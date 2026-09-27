# 气象观测站网运维平台

面向区域气象观测站网的站点入网、传感器检定、观测数据质控、供电通信保障与运维结算的一体化运行监控后台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 模块清单只有一份：`modules.config.json`

侧边导航、前端路由、各模块列表页、运营概览、后端接口注册、示例数据，全部从仓库根目录的
**`modules.config.json`** 生成，任何地方都不再手写第二份模块清单。

每个模块在配置里声明：

- `key` / `label` / `path` / `apiPrefix`：模块标识、中文名、前端路由、后端接口前缀；
- `statuses`：完整状态序列；
- `pendingStatuses`：**待处理口径**，状态命中即待处理；
- `abnormalStatuses`：**异常口径**，状态命中即异常；
- `actions`：可执行动作及其目标状态；
- `listFields` / `requiredFields` / `keywordField`：列表列、必填项、检索字段；
- `seedCount`：示例数据条数。

运营概览的汇总和列表页的待处理/异常数字都由同一份 `pendingStatuses`/`abnormalStatuses`
派生，刷新后卡片数字就是模块汇总行的求和，不会再出现两处对不上。

### 新增或修改一个模块

1. 只改 `modules.config.json`（新增一个模块对象，或调整某模块的状态/口径）；
2. 运行 `make sync`（等价于 `python3 scripts/sync_modules.py`），把配置投影到
   `frontend/src/modules.frontend.json`；
3. 运行 `make check` 做前后端对齐校验。

不需要再新增 router/service/view 文件，也不需要改导航、路由、概览——它们全部由配置生成。

## 对齐校验（本地启动 / 构建 / 部署都会执行）

`make check` 会校验「依赖声明 = 模块清单 = 示例数据 = 已注册路由」四处一致：

| 时机 | 校验 |
| --- | --- |
| 后端本地启动（`./run.sh`、`make backend`） | 先跑 `python -m app.validate_modules`，且应用导入时再校验一次 |
| 前端本地启动（`npm run dev`、`make frontend`） | `predev` 钩子跑 `node scripts/check-modules.cjs`，vite 插件在 `buildStart` 再校验一次 |
| 前端构建（`npm run build`） | `prebuild` 钩子先校验，模块数/口径对不上直接构建失败 |
| 镜像构建（`docker compose build`） | 后端镜像构建时跑 `validate_modules`；前端镜像重新投影声明后跑 `check-modules.cjs` |

校验内容包括：配置结构自洽（口径状态必须在状态序列内）、示例数据表数量与 `seedCount`、
状态位与口径一致、注册路由前缀一一对应、前端声明的模块数量/顺序/key/口径与配置完全相同。

## 目录结构

```text
.
├── modules.config.json        模块清单与统计口径的唯一事实来源
├── scripts/sync_modules.py    把配置投影成前端声明（Node 版：frontend/scripts/sync-modules.cjs）
├── frontend/                  Vue 3 + Vite + TypeScript 前端
│   ├── src/modules.ts         前端访问模块清单/口径的唯一入口
│   ├── src/modules.frontend.json  由配置生成的前端声明（提交入库，构建时重新投影校验）
│   ├── src/views/ModuleView.vue  所有模块共用的配置驱动列表页
│   └── scripts/check-modules.cjs 前端对齐校验
├── backend/                   FastAPI（Python） 后端
│   ├── app/modules_config.py  配置加载、口径派生（is_pending/is_abnormal/annotate）
│   ├── app/routers/__init__.py   按配置为每个模块生成路由
│   ├── app/services/generic.py   所有模块共用的业务规则
│   ├── app/seed.py            按配置生成示例数据
│   └── app/validate_modules.py   后端对齐校验
└── docker-compose.yml
```

## 启动

### 后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh   # 启动前自动做模块对齐校验
```

健康检查：`curl http://127.0.0.1:8000/api/health`

### 前端

```bash
cd frontend
npm install
npm run dev   # predev 自动做模块对齐校验
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`。

## 接口不可用时的行为

运营概览与各模块列表在接口请求失败时**不会退回写死的假数据**：

- 运营概览仍按配置列出全部模块名称（导航有哪些模块就列哪些），统计数字显示「—」，
  顶部给出可读的失败说明，并提供「刷新概览」按钮在接口恢复后重新拉取；
- 列表页在页内显示失败原因，表格区域展示可读的空态说明。

## 约定

- 列表接口统一返回 `{ items, total, page, size, summary }`，其中 `summary` 是
  `{ created, pending, abnormal }`，与运营概览该模块那一行同口径；
  动作接口统一返回 `{ ok, message, entry? }`。
- 待处理/异常状态位一律由 `ModuleConfig.annotate` 按配置派生，路由层不做业务判断。

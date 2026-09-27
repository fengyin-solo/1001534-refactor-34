#!/usr/bin/env node
/**
 * 把仓库根目录的 modules.config.json 投影成前端声明 src/modules.frontend.json。
 *
 * 与 scripts/sync_modules.py 行为完全一致，提供纯 Node 版本是为了在没有 Python
 * 的前端镜像/CI 里也能生成声明。唯一事实来源始终是 modules.config.json，
 * 前端代码不要手写或直接引用仓库根配置。
 *
 * 路径解析同时兼容两种布局：
 * - 仓库内：frontend/scripts/<本文件>，仓库根在上两级；
 * - 前端镜像内：/srv/web/scripts/<本文件>，源配置在 /srv/modules.config.json
 *   （可用 MODULES_CONFIG_PATH 显式覆盖）。
 */
const fs = require('node:fs')
const path = require('node:path')

const scriptDir = __dirname
const frontendRoot = path.resolve(scriptDir, '..')
// 仓库布局：源配置在 frontend 的上一级；镜像布局：源配置在 /srv，前端代码在 /srv/web。
const candidates = process.env.MODULES_CONFIG_PATH
  ? [process.env.MODULES_CONFIG_PATH]
  : [
      path.resolve(frontendRoot, '..', 'modules.config.json'),
      path.join(frontendRoot, 'modules.config.json'),
      '/srv/modules.config.json',
    ]
const sourcePath = candidates.find((candidate) => fs.existsSync(candidate))
if (!sourcePath) {
  console.error('找不到 modules.config.json，可用 MODULES_CONFIG_PATH 指定其位置。')
  process.exit(1)
}
const targetPath = process.env.FRONTEND_MANIFEST_PATH
  ? process.env.FRONTEND_MANIFEST_PATH
  : path.join(frontendRoot, 'src', 'modules.frontend.json')

// 与 scripts/sync_modules.py 的白名单保持一致；后端校验会交叉核对。
const MODULE_FIELDS = [
  'key',
  'label',
  'objectLabel',
  'path',
  'apiPrefix',
  'listFields',
  'requiredFields',
  'keywordField',
  'statuses',
  'pendingStatuses',
  'abnormalStatuses',
  'actions',
  'seedCount',
]

const config = JSON.parse(fs.readFileSync(sourcePath, 'utf8'))
const manifest = {
  version: config.version,
  source: 'modules.config.json',
  cards: config.cards,
  modules: config.modules.map((module) =>
    Object.fromEntries(MODULE_FIELDS.map((field) => [field, module[field]])),
  ),
}

fs.mkdirSync(path.dirname(targetPath), { recursive: true })
fs.writeFileSync(targetPath, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8')
const displayPath = path.relative(frontendRoot, targetPath) || targetPath
console.log(`已同步 ${manifest.modules.length} 个模块声明到 ${displayPath}`)

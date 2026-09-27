#!/usr/bin/env node
/**
 * 前端模块对齐校验：dev 启动、vite build、镜像构建时都会执行。
 *
 * 校验内容：
 * 1. 前端声明 modules.frontend.json 是源配置 modules.config.json 的最新投影
 *   （版本一致、模块数量/顺序/key/待处理与异常口径完全相同）；
 * 2. 前端声明自身结构合法（路径、接口前缀、状态集合自洽）；
 * 3. 代码里没有再手写第二份模块清单（router/App.vue 必须引用 @/modules）。
 *
 * 任一项失败就以非零码退出，让启动/构建/部署直接失败。
 */
const fs = require('node:fs')
const path = require('node:path')

const scriptDir = __dirname
// scripts 目录的上一级就是前端根（仓库布局 frontend/scripts；镜像布局 /srv/web/scripts）。
const frontendRoot = path.resolve(scriptDir, '..')
// 源配置优先取显式环境变量；仓库布局下在前端根的上一级，镜像布局下与前端根同级（/srv）。
const sourceCandidates = process.env.MODULES_CONFIG_PATH
  ? [process.env.MODULES_CONFIG_PATH]
  : [
      path.resolve(frontendRoot, '..', 'modules.config.json'),
      path.join(frontendRoot, 'modules.config.json'),
      '/srv/modules.config.json',
    ]
const sourcePath = sourceCandidates.find((candidate) => fs.existsSync(candidate))
const manifestPath = process.env.FRONTEND_MANIFEST_PATH
  ? process.env.FRONTEND_MANIFEST_PATH
  : path.join(frontendRoot, 'src', 'modules.frontend.json')
const frontendSrc = path.join(frontendRoot, 'src')

const errors = []

function fail(message) {
  errors.push(message)
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'))
}

let source
let manifest
if (!sourcePath) {
  fail('找不到 modules.config.json，可用 MODULES_CONFIG_PATH 指定其位置')
} else {
  try {
    source = readJson(sourcePath)
  } catch (error) {
    fail(`无法读取源配置 modules.config.json：${error.message}`)
  }
}
try {
  manifest = readJson(manifestPath)
} catch (error) {
  fail(`无法读取前端模块声明 src/modules.frontend.json：${error.message}（请先运行 scripts/sync_modules.py）`)
}

if (source && manifest) {
  if (manifest.version !== source.version) {
    fail(`前端声明版本 ${manifest.version} 与源配置版本 ${source.version} 不一致，请重新运行 scripts/sync_modules.py`)
  }
  const a = source.modules
  const b = manifest.modules
  // 依赖声明（前端清单）里的模块数量必须与配置一致
  if (!Array.isArray(b) || b.length === 0) {
    fail('前端模块声明为空，请先运行 scripts/sync_modules.py（或 node frontend/scripts/sync-modules.cjs）')
  }
  if (a.length !== b.length) {
    fail(`模块数量不一致：源配置 ${a.length} 个，前端声明 ${b.length} 个`)
  }
  const count = Math.max(a.length, b.length)
  for (let i = 0; i < count; i += 1) {
    const src = a[i]
    const dst = b[i]
    if (!src || !dst || src.key !== dst.key) {
      fail(`第 ${i + 1} 个模块不一致：${src?.key ?? '缺失'} != ${dst?.key ?? '缺失'}`)
      continue
    }
    for (const field of [
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
      'seedCount',
    ]) {
      const left = JSON.stringify(src[field])
      const right = JSON.stringify(dst[field])
      if (left !== right) {
        fail(`模块 ${src.key} 的 ${field} 前后端不一致：${left} != ${right}`)
      }
    }
    const srcActions = src.actions.map((item) => `${item.label}->${item.target}`)
    const dstActions = dst.actions.map((item) => `${item.label}->${item.target}`)
    if (JSON.stringify(srcActions) !== JSON.stringify(dstActions)) {
      fail(`模块 ${src.key} 的动作声明前后端不一致`)
    }
    // 结构自洽：口径状态必须在状态集合内。
    for (const status of [...dst.pendingStatuses, ...dst.abnormalStatuses]) {
      if (!dst.statuses.includes(status)) {
        fail(`模块 ${src.key} 的口径状态「${status}」不在 statuses 内`)
      }
    }
  }
}

// 代码层不能再出现第二份手写清单。
const routerSource = fs.readFileSync(path.join(frontendSrc, 'router', 'index.ts'), 'utf8')
if (!routerSource.includes("from '@/modules'")) {
  fail('router/index.ts 必须从 @/modules 生成路由，不能手写模块路由')
}
const appSource = fs.readFileSync(path.join(frontendSrc, 'App.vue'), 'utf8')
if (!appSource.includes("from '@/modules'")) {
  fail('App.vue 必须从 @/modules 生成导航，不能手写模块清单')
}

if (errors.length) {
  console.error('前端模块对齐校验未通过：')
  for (const error of errors) console.error(`  - ${error}`)
  process.exit(1)
}
console.log(`前端模块对齐校验通过：${manifest.modules.length} 个模块与源配置一致。`)

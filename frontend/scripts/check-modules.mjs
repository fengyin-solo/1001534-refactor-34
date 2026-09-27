#!/usr/bin/env node
/**
 * 前端模块对齐校验：dev 启动（predev）与构建（prebuild）前自动运行，
 * 确认 frontend/src/views/ 下的页面与仓库根目录 modules.config.json 的模块清单一一对应。
 * 后端侧的对齐由 scripts/check_modules.py 负责（make check / 后端启动时都会跑）。
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const repoRoot = dirname(frontendRoot)
const configPath = join(repoRoot, 'modules.config.json')

const problems = []
let modules = []
try {
  modules = JSON.parse(readFileSync(configPath, 'utf-8')).modules ?? []
} catch (error) {
  problems.push(`模块配置文件读取失败：${configPath}（${error.message}）`)
}

if (!modules.length) {
  problems.push('modules.config.json 里的 modules 清单为空')
}

const expected = new Set(modules.map((module) => module.key))
const viewsDir = join(frontendRoot, 'src', 'views')
const actual = new Set(
  readdirSync(viewsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(viewsDir, entry.name, 'index.vue')))
    .map((entry) => entry.name),
)

const missing = [...expected].filter((key) => !actual.has(key))
const extra = [...actual].filter((key) => !expected.has(key))
if (missing.length) problems.push(`frontend/src/views/ 缺少模块页面：${missing.join(', ')}`)
if (extra.length) problems.push(`frontend/src/views/ 多出未登记的模块目录：${extra.join(', ')}`)

if (problems.length) {
  console.error('模块对齐校验失败：')
  for (const problem of problems) console.error(`  - ${problem}`)
  process.exit(1)
}
console.log(`模块对齐校验通过：${expected.size} 个模块（modules.config.json）`)

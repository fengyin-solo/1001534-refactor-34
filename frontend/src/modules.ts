/**
 * 模块清单与统计口径的唯一前端入口。
 *
 * 数据来源是 scripts/sync_modules.py 从仓库根目录 modules.config.json 生成的
 * modules.frontend.json，前端任何地方都不要再手写模块名、路径或状态口径：
 * 侧边导航、路由、列表页、运营概览都从这里取。后端启动/构建校验会保证这份
 * 声明与源配置、示例数据完全一致。
 */
import manifest from './modules.frontend.json'

export interface ModuleAction {
  label: string
  target: string
}

export interface ModuleDef {
  key: string
  label: string
  objectLabel: string
  path: string
  apiPrefix: string
  listFields: string[]
  requiredFields: string[]
  keywordField: string
  statuses: string[]
  pendingStatuses: string[]
  abnormalStatuses: string[]
  actions: ModuleAction[]
  seedCount: number
}

export interface CardDef {
  key: 'modules' | 'created' | 'pending' | 'abnormal'
  label: string
}

export interface ModuleRow {
  id: number
  status: string
  pending?: boolean
  abnormal?: boolean
  [field: string]: string | number | boolean | null | undefined
}

export interface PagePayload {
  items: ModuleRow[]
  total: number
  page: number
  size: number
  summary?: { created: number; pending: number; abnormal: number }
}

export interface OverviewModule {
  key: string
  name: string
  created: number
  pending: number
  abnormal: number
}

export interface OverviewPayload {
  cards: { key?: string; label: string; value: number }[]
  modules: OverviewModule[]
}

export const cards: CardDef[] = manifest.cards as CardDef[]
export const modules: ModuleDef[] = manifest.modules as ModuleDef[]

const byKey = new Map(modules.map((module) => [module.key, module]))
const byPath = new Map(modules.map((module) => [module.path, module]))

export function getModule(key: string): ModuleDef {
  const module = byKey.get(key)
  if (!module) throw new Error(`未在模块配置中找到模块：${key}`)
  return module
}

export function getModuleByPath(path: string): ModuleDef {
  const module = byPath.get(path)
  if (!module) throw new Error(`未在模块配置中找到路由：${path}`)
  return module
}

/** 与后端 ModuleConfig.is_pending 完全相同的口径，前端兜底时也用它。 */
export function isPending(module: ModuleDef, status: string): boolean {
  return module.pendingStatuses.includes(status)
}

export function isAbnormal(module: ModuleDef, status: string): boolean {
  return module.abnormalStatuses.includes(status)
}

/**
 * 业务模块清单与统计口径的唯一来源：仓库根目录的 modules.config.json。
 * 侧边导航、路由、运营概览、各模块列表的统计卡片都从这里取数，
 * 新增模块只需要改配置并补齐对应文件，不再多处维护名单。
 */
import modulesConfig from '../../modules.config.json'

export type ModuleSpec = {
  key: string
  label: string
  entity: string
  pendingStatuses: string[]
  abnormalStatuses: string[]
}

export const MODULES: ModuleSpec[] = modulesConfig.modules

export const MODULE_MAP: ReadonlyMap<string, ModuleSpec> = new Map(
  MODULES.map((module) => [module.key, module]),
)

export type StatusCounts = { total: number; pending: number; abnormal: number }

/** 按统一口径统计一批记录：状态落在配置的状态集合里才计入待处理/异常。 */
export function countByCriteria(key: string, rows: Array<Record<string, unknown>>): StatusCounts {
  const spec = MODULE_MAP.get(key)
  const pendingStatuses = new Set(spec?.pendingStatuses ?? [])
  const abnormalStatuses = new Set(spec?.abnormalStatuses ?? [])
  let pending = 0
  let abnormal = 0
  for (const row of rows) {
    const status = String(row.status ?? '')
    if (pendingStatuses.has(status)) pending += 1
    if (abnormalStatuses.has(status)) abnormal += 1
  }
  return { total: rows.length, pending, abnormal }
}

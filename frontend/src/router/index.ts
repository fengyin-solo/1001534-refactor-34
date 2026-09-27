import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '@/views/Dashboard.vue'
import { MODULES } from '@/modules'

// 页面组件按目录约定自动收集，路由按 modules.config.json 的模块清单生成，
// 新增模块只要补 frontend/src/views/<模块>/index.vue，不再手工登记路由。
const pages = import.meta.glob('../views/*/index.vue')

const moduleRoutes = MODULES.map((module) => {
  const component = pages[`../views/${module.key}/index.vue`]
  if (!component) {
    // predev/prebuild 的模块对齐校验会先拦住这种情况；这里兜底给出可读信息
    throw new Error(`模块 ${module.key}（${module.label}）缺少页面 frontend/src/views/${module.key}/index.vue`)
  }
  return { path: `/${module.key}`, name: module.key, component }
})

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', name: 'dashboard', component: Dashboard }, ...moduleRoutes],
})

export default router

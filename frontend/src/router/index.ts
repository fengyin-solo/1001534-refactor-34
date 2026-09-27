import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import Dashboard from '@/views/Dashboard.vue'
import ModuleView from '@/views/ModuleView.vue'
import { modules } from '@/modules'

// 路由表由模块配置生成：新增模块只需改 modules.config.json，这里不用动。
const moduleRoutes: RouteRecordRaw[] = modules.map((module) => ({
  path: module.path,
  name: module.key,
  component: ModuleView,
  props: { moduleKey: module.key },
}))

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    ...moduleRoutes,
  ],
})

export default router

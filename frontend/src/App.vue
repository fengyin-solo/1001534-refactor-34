<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">气象观测站网运维平台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向区域气象观测站网的站点入网、传感器检定、观测数据质控、供电通信保障与运维结算的一体化运行监控后台。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { MODULES } from '@/modules'
import { useSessionStore } from '@/stores/session'

const store = useSessionStore()

// 导航与运营概览、路由共用同一份模块清单，新增模块不需要再改这里
const navItems = [
  { label: '运营概览', path: '/' },
  ...MODULES.map((module) => ({ label: module.label, path: `/${module.key}` })),
]
</script>

<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
      <div class="page-actions">
        <button class="btn" type="button" :disabled="loading" @click="load">
          {{ loading ? '刷新中…' : '刷新概览' }}
        </button>
      </div>
    </header>

    <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.key">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'
import { MODULES } from '@/modules'

type ModuleRow = { key: string; name: string; created: number | string; pending: number | string; abnormal: number | string }
type Overview = { modules: Array<{ key?: string; name: string; created: number; pending: number; abnormal: number }> }

const EMPTY = '—'

// 接口不可用时也按统一模块清单列出全部模块，数值用占位符，
// 只提示真实原因，不回退到写死的假数据。
const moduleRows = ref<ModuleRow[]>(
  MODULES.map((module) => ({ key: module.key, name: module.label, created: EMPTY, pending: EMPTY, abnormal: EMPTY })),
)
const errorMessage = ref('')
const loading = ref(false)

// 卡片直接由模块汇总行推导，刷新后卡片与汇总表必然一致
const cards = computed(() => {
  const rows = moduleRows.value
  const ready = rows.every((row) => typeof row.created === 'number')
  const sum = (pick: (row: ModuleRow) => number | string) =>
    ready ? rows.reduce((total, row) => total + Number(pick(row)), 0) : EMPTY
  return [
    { label: '业务模块', value: rows.length },
    { label: '今日新增', value: sum((row) => row.created) },
    { label: '待处理', value: sum((row) => row.pending) },
    { label: '异常量', value: sum((row) => row.abnormal) },
  ]
})

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    moduleRows.value = payload.modules.map((row, index) => ({
      key: row.key ?? MODULES[index]?.key ?? `module-${index}`,
      name: row.name,
      created: row.created,
      pending: row.pending,
      abnormal: row.abnormal,
    }))
  } catch (error) {
    const detail = error instanceof Error ? error.message : '未知原因'
    errorMessage.value = `运营概览接口暂不可用（${detail}）。请确认后端已启动（make backend 或 cd backend && ./run.sh）后点击「刷新概览」重试。`
    moduleRows.value = MODULES.map((module) => ({
      key: module.key,
      name: module.label,
      created: EMPTY,
      pending: EMPTY,
      abnormal: EMPTY,
    }))
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

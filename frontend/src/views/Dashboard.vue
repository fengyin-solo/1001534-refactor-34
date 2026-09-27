<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。卡片数字由模块汇总直接求和，刷新后两处必然一致。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" :disabled="loading" @click="loadOverview">
          {{ loading ? '刷新中…' : '刷新概览' }}
        </button>
      </div>
    </header>

    <p v-if="errorMessage" class="error-banner" role="alert">{{ errorMessage }}</p>

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
        <tr v-for="row in displayedRows" :key="row.key">
          <td>{{ row.name }}</td>
          <td>{{ row.unavailable ? DASH : row.created }}</td>
          <td>{{ row.unavailable ? DASH : row.pending }}</td>
          <td>{{ row.unavailable ? DASH : row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'
import { cards as cardDefs, modules, type OverviewPayload } from '@/modules'

const DASH = '—'

type DisplayRow = OverviewPayload['modules'][number] & { unavailable?: boolean }

const moduleRows = ref<DisplayRow[]>([])
const loading = ref(false)
const errorMessage = ref('')

// 接口可用时展示真实汇总；不可用时仍按配置列出模块清单，数字用「—」占位，
// 既不写死假数据，也不让页面空成一片。
const displayedRows = computed<DisplayRow[]>(() =>
  moduleRows.value.length
    ? moduleRows.value
    : modules.map((module) => ({
        key: module.key,
        name: module.label,
        created: 0,
        pending: 0,
        abnormal: 0,
        unavailable: true,
      })),
)

// 卡片数字一律由当前展示的模块行在前端再求一次和，和后端同一份配置口径，
// 从结构上杜绝「卡片」与「模块汇总」对不上。
const cards = computed(() => {
  const rows = moduleRows.value
  const unavailable = rows.length === 0
  const totals: Record<string, number | string> = {
    modules: unavailable ? DASH : rows.length,
    created: unavailable ? DASH : rows.reduce((sum, row) => sum + row.created, 0),
    pending: unavailable ? DASH : rows.reduce((sum, row) => sum + row.pending, 0),
    abnormal: unavailable ? DASH : rows.reduce((sum, row) => sum + row.abnormal, 0),
  }
  return cardDefs.map((def) => ({ label: def.label, value: String(totals[def.key]) }))
})

async function loadOverview() {
  loading.value = true
  errorMessage.value = ''
  try {
    const payload = await fetchJson<OverviewPayload>('/api/overview')
    moduleRows.value = payload.modules
  } catch (error) {
    // 可读的兜底说明：明确告诉值班人员数据暂时不可用，绝不退回写死的假数据。
    moduleRows.value = []
    errorMessage.value =
      error instanceof Error
        ? `运营概览暂时无法获取：${error.message}。模块清单仍按配置展示，数字待接口恢复后点击「刷新概览」。`
        : '运营概览暂时无法获取：后端接口不可用，请检查后端服务后点击「刷新概览」。'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadOverview()
})
</script>

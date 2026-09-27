<template>
  <section class="page" :data-module="module.key">
    <header class="page-head">
      <div>
        <h2>{{ module.label }}管理</h2>
        <p class="page-desc">
          维护{{ module.objectLabel }}，围绕{{ module.listFields.slice(0, 3).join('、') }}做登记、筛选与状态流转。
        </p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记{{ module.objectLabel }}</button>
        <button class="btn" type="button" @click="exportRows">导出{{ module.label }}清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article class="stat-card">
        <span class="stat-label">记录总数</span>
        <strong class="stat-value">{{ stats.created }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">待处理</span>
        <strong class="stat-value">{{ stats.pending }}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">异常量</span>
        <strong class="stat-value">{{ stats.abnormal }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>{{ module.keywordField }}</span>
        <input v-model="keyword" :placeholder="`按${module.keywordField}检索`" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in module.listFields" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in module.listFields" :key="column">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button
              v-for="action in module.actions"
              :key="action.label"
              class="link"
              type="button"
              @click="runAction(action.label, row)"
            >
              {{ action.label }}
            </button>
          </td>
        </tr>
        <tr v-if="loaded && !rows.length && !errorMessage">
          <td :colspan="module.listFields.length + 1" class="empty-state">
            暂无{{ module.label }}数据，可先登记{{ module.objectLabel }}
          </td>
        </tr>
        <tr v-if="errorMessage">
          <td :colspan="module.listFields.length + 1" class="empty-state error-text">{{ errorMessage }}</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条{{ module.objectLabel }}记录</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson, type RequestError } from '@/api/client'
import { getModule, isAbnormal, isPending, type ModuleRow, type PagePayload } from '@/modules'

const props = defineProps<{ moduleKey: string }>()
const module = getModule(props.moduleKey)

const ENDPOINT = module.apiPrefix

const rows = ref<ModuleRow[]>([])
const total = ref(0)
const summary = ref<{ created: number; pending: number; abnormal: number } | null>(null)
const loaded = ref(false)
const errorMessage = ref('')
const keyword = ref('')

// 列表顶部卡片与运营概览同一口径：后端列表接口返回全量 summary。
// 接口缺字段时（旧后端/降级）用当前页数据 + 同一份 pendingStatuses/abnormalStatuses
// 口径估算，并保持数字可见，不再写死一组永远为 0 的假卡片。
const stats = computed(() => {
  if (summary.value) return summary.value
  return {
    created: total.value,
    pending: countBy(rows.value, (row) => isPending(module, String(row.status))),
    abnormal: countBy(rows.value, (row) => isAbnormal(module, String(row.status))),
  }
})

function countBy(source: ModuleRow[], test: (row: ModuleRow) => boolean): number {
  return source.reduce((sum, row) => sum + (test(row) ? 1 : 0), 0)
}

function resetFilters() {
  keyword.value = ''
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = `${module.objectLabel}登记入口尚未接入审批流`
}

async function runAction(action: string, row: ModuleRow) {
  errorMessage.value = ''
  try {
    const result = await fetchJson<{ ok: boolean; message: string }>(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    if (!result.ok) {
      throw new Error(result.message)
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : `${module.label}操作失败`
  }
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams(keyword.value ? { keyword: keyword.value.trim() } : {}).toString()
  try {
    const payload = await fetchJson<PagePayload>(`${ENDPOINT}?${query}`)
    rows.value = payload.items ?? []
    summary.value = payload.summary ?? null
    total.value = payload.summary?.created ?? payload.total ?? rows.value.length
    loaded.value = true
  } catch (error) {
    loaded.value = true
    rows.value = []
    summary.value = null
    total.value = 0
    errorMessage.value = (error as RequestError).message || `${module.label}列表读取失败`
  }
}

onMounted(reload)
</script>

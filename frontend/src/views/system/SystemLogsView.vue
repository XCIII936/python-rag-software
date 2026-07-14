<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统日志</h2>
    </div>

    <!-- 搜索过滤器 -->
    <el-card shadow="never" class="filter-card">
      <el-form :model="filters" layout="inline" class="filter-form">
        <el-form-item label="日志级别">
          <el-select
            v-model="filters.level"
            placeholder="全部级别"
            clearable
            style="width: 140px"
          >
            <el-option label="DEBUG" value="DEBUG" />
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
            <el-option label="CRITICAL" value="CRITICAL" />
          </el-select>
        </el-form-item>

        <el-form-item label="模块">
          <el-select
            v-model="filters.module"
            placeholder="全部模块"
            clearable
            style="width: 140px"
          >
            <el-option label="认证" value="auth" />
            <el-option label="章节" value="chapter" />
            <el-option label="文档" value="document" />
            <el-option label="测评" value="assessment" />
            <el-option label="智能体" value="agent" />
            <el-option label="系统" value="system" />
            <el-option label="LLM" value="llm" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 260px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志列表 -->
    <el-card shadow="never" class="logs-card">
      <el-table
        :data="logs"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无日志"
        size="small"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="级别" width="90">
          <template #default="{ row }">
            <el-tag
              :type="levelType(row.level)"
              size="small"
              effect="dark"
            >
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="100" />
        <el-table-column prop="action" label="操作" width="120" />
        <el-table-column prop="message" label="消息" min-width="260" show-overflow-tooltip />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getLogs, type LogItem } from '@/api/system'

const logs = ref<LogItem[]>([])
const loading = ref(true)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  level: '',
  module: '',
})

const dateRange = ref<[string, string] | null>(null)

onMounted(() => {
  fetchLogs()
})

async function fetchLogs() {
  loading.value = true
  try {
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (filters.level) params.level = filters.level
    if (filters.module) params.module = filters.module
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const res = await getLogs(params)
    logs.value = res.items
    total.value = res.total
  } catch {
    // 错误已在 request.ts 中处理
  } finally {
    loading.value = false
  }
}

function levelType(level: string): 'success' | 'warning' | 'danger' | 'info' {
  switch (level) {
    case 'INFO': return 'success'
    case 'WARNING': return 'warning'
    case 'ERROR':
    case 'CRITICAL': return 'danger'
    default: return 'info'
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchLogs()
}

function handleReset() {
  filters.level = ''
  filters.module = ''
  dateRange.value = null
  currentPage.value = 1
  fetchLogs()
}

function handleRefresh() {
  fetchLogs()
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchLogs()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  fetchLogs()
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.filter-card {
  margin-bottom: 16px;

  .filter-form {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0;

    :deep(.el-form-item) {
      margin-bottom: 0;
      margin-right: 16px;
    }
  }
}

.logs-card {
  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    padding-top: 16px;
  }
}
</style>

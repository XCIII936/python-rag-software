<template>
  <div class="page-container">
    <div class="page-header">
      <h2>测评结果</h2>
    </div>

    <el-card shadow="never" class="result-card">
      <div class="result-header">
        <el-result
          :icon="passed ? 'success' : 'error'"
          :title="passed ? '恭喜通过！' : '继续加油！'"
          :sub-title="`正确 ${correctCount} / ${totalCount} 题`"
        >
          <template #extra>
            <div class="score-display">
              <span class="score-value">{{ Math.round((correctCount / totalCount) * 100) }}</span>
              <span class="score-unit">分</span>
            </div>
            <el-progress
              type="circle"
              :percentage="Math.round((correctCount / totalCount) * 100)"
              :width="120"
              :stroke-width="8"
              :color="passed ? '#67C23A' : '#F56C6C'"
            />
          </template>
        </el-result>
      </div>

      <el-divider />

      <div class="result-detail">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="正确题数">{{ correctCount }}</el-descriptions-item>
          <el-descriptions-item label="错误题数">{{ totalCount - correctCount }}</el-descriptions-item>
          <el-descriptions-item label="正确率">{{ Math.round((correctCount / totalCount) * 100) }}%</el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="result-actions">
        <el-button type="primary" @click="router.push('/chapters')">
          返回章节列表
        </el-button>
        <el-button @click="router.back()">
          重新测评
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const correctCount = computed(() => Number(route.query.correct) || 0)
const totalCount = computed(() => Number(route.query.total) || 0)
const passed = computed(() => correctCount.value >= totalCount.value * 0.6)
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.result-card {
  max-width: 600px;
  margin: 0 auto;
}

.result-header {
  :deep(.el-result) {
    padding: 20px 0;
  }
}

.score-display {
  text-align: center;
  margin-bottom: 20px;

  .score-value {
    font-size: 48px;
    font-weight: 700;
    color: $text-primary;
  }

  .score-unit {
    font-size: 18px;
    color: $text-secondary;
    margin-left: 4px;
  }
}

.result-detail {
  margin: 20px 0;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
}
</style>

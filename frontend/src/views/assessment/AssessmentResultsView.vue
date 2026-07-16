<template>
  <div class="page-container">
    <div class="page-header">
      <h2>测评结果</h2>
    </div>

    <el-card shadow="never" class="result-card" v-loading="loading">
      <div class="result-header">
        <el-result
          :icon="passed ? 'success' : 'error'"
          :title="passed ? '恭喜通过！' : '继续加油！'"
          :sub-title="subtitle"
        >
          <template #extra>
            <div class="score-display">
              <span class="score-value">{{ Math.round(score) }}</span>
              <span class="score-unit">分</span>
            </div>
            <el-progress
              type="circle"
              :percentage="score"
              :width="120"
              :stroke-width="8"
              :color="passed ? '#67C23A' : '#F56C6C'"
            />
          </template>
        </el-result>
      </div>

      <el-divider />

      <!-- 报告详情（从后端获取的完整报告） -->
      <div v-if="report" class="report-detail">
        <!-- 维度评分：雷达图 + 条形对照 -->
        <div v-if="dimensions.length > 0" class="dimension-section">
          <h3>各维度评分</h3>
          <div class="dimension-layout">
            <div class="dimension-radar">
              <RadarChart :dimensions="dimensions" height="300px" />
            </div>
            <div class="dimension-bars">
              <div v-for="(dim, idx) in dimensions" :key="idx" class="dimension-item">
                <div class="dimension-header">
                  <span class="dimension-name">{{ dim.name || dim.dimension }}</span>
                  <span class="dimension-score">{{ dim.score }}分</span>
                </div>
                <el-progress
                  :percentage="dim.score"
                  :color="dim.score >= 60 ? '#67C23A' : '#F56C6C'"
                  :stroke-width="12"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- 总体评语 -->
        <div v-if="report.summary_comment" class="comment-section">
          <h3>总体评语</h3>
          <p class="comment-text">{{ report.summary_comment }}</p>
        </div>

        <!-- 优点 -->
        <div v-if="strengthsList.length > 0" class="strengths-section">
          <h3>掌握较好的方面</h3>
          <ul>
            <li v-for="(s, idx) in strengthsList" :key="idx">{{ s }}</li>
          </ul>
        </div>

        <!-- 薄弱点 -->
        <div v-if="weaknessesList.length > 0" class="weaknesses-section">
          <h3>需要加强的方面</h3>
          <ul>
            <li v-for="(w, idx) in weaknessesList" :key="idx">{{ w }}</li>
          </ul>
        </div>

        <!-- 复习建议 -->
        <div v-if="suggestionsList.length > 0" class="suggestions-section">
          <h3>复习建议</h3>
          <ul>
            <li v-for="(sg, idx) in suggestionsList" :key="idx">{{ sg }}</li>
          </ul>
        </div>
      </div>

      <!-- 简单统计（无报告时） -->
      <div v-else class="result-detail">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="正确题数">{{ correctCount }}</el-descriptions-item>
          <el-descriptions-item label="错误题数">{{ totalCount - correctCount }}</el-descriptions-item>
          <el-descriptions-item label="正确率">{{ Math.round((correctCount / totalCount) * 100) }}%</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 逐题详细回顾：错题点评纠正 -->
      <div class="question-review-section">
        <el-divider />
        <div class="review-section-header">
          <h3>逐题详细回顾</h3>
          <el-radio-group v-model="reviewFilter" size="small">
            <el-radio-button value="all">全部 ({{ reviewItems.length }})</el-radio-button>
            <el-radio-button value="wrong">仅看错题 ({{ wrongCount }})</el-radio-button>
          </el-radio-group>
        </div>

        <div v-loading="reviewLoading">
          <template v-if="filteredReviewItems.length > 0">
            <QuestionReviewCard
              v-for="item in filteredReviewItems"
              :key="item.id"
              :item="item"
            />
          </template>
          <el-empty v-else-if="!reviewLoading" description="暂无题目详情" />
        </div>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getReport,
  getAssessmentReview,
  type ReportData,
  type QuestionReviewItem as QuestionReviewItemType,
} from '@/api/assessment'
import RadarChart from '@/components/assessment/RadarChart.vue'
import QuestionReviewCard from '@/components/assessment/QuestionReviewCard.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const reviewLoading = ref(true)
const report = ref<ReportData | null>(null)
const reviewItems = ref<QuestionReviewItemType[]>([])
const reviewFilter = ref<'all' | 'wrong'>('all')

const recordId = computed(() => Number(route.params.recordId))
const correctCount = computed(() => Number(route.query.correct) || 0)
const totalCount = computed(() => Number(route.query.total) || 0)
const score = computed(() => Number(route.query.score) || Math.round((correctCount.value / (totalCount.value || 1)) * 100))
const passed = computed(() => score.value >= 60)

const subtitle = computed(() => `正确 ${correctCount.value} / ${totalCount.value} 题`)

const dimensions = computed(() => {
  if (!report.value?.dimension_scores) return []
  const raw = report.value.dimension_scores
  if (Array.isArray(raw)) return raw
  if (typeof raw === 'string') {
    try { return JSON.parse(raw) } catch { return [] }
  }
  return []
})

const strengthsList = computed(() => {
  if (!report.value?.strengths) return []
  if (Array.isArray(report.value.strengths)) return report.value.strengths
  if (typeof report.value.strengths === 'string') {
    try { return JSON.parse(report.value.strengths) } catch { return [] }
  }
  return []
})

const weaknessesList = computed(() => {
  if (!report.value?.weaknesses) return []
  if (Array.isArray(report.value.weaknesses)) return report.value.weaknesses
  if (typeof report.value.weaknesses === 'string') {
    try { return JSON.parse(report.value.weaknesses) } catch { return [] }
  }
  return []
})

const suggestionsList = computed(() => {
  if (!report.value?.review_suggestions) return []
  if (Array.isArray(report.value.review_suggestions)) return report.value.review_suggestions
  if (typeof report.value.review_suggestions === 'string') {
    try { return JSON.parse(report.value.review_suggestions) } catch { return [] }
  }
  return []
})

const wrongCount = computed(() => reviewItems.value.filter(i => i.is_correct === false).length)

const filteredReviewItems = computed(() => {
  if (reviewFilter.value === 'wrong') {
    return reviewItems.value.filter(i => i.is_correct === false)
  }
  return reviewItems.value
})

onMounted(async () => {
  if (recordId.value && recordId.value > 0) {
    try {
      report.value = await getReport(recordId.value)
    } catch {
      // 报告不存在或尚未生成，使用 query 参数中的数据
    }

    try {
      reviewItems.value = await getAssessmentReview(recordId.value)
      // 默认若存在错题，自动切换到"仅看错题"视图，帮助学生第一时间关注薄弱点
      if (reviewItems.value.some(i => i.is_correct === false)) {
        reviewFilter.value = 'wrong'
      }
    } catch {
      reviewItems.value = []
    } finally {
      reviewLoading.value = false
    }
  } else {
    reviewLoading.value = false
  }
  loading.value = false
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.result-card {
  max-width: 860px;
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

.report-detail {
  margin: 20px 0;

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    margin: 20px 0 12px;

    &:first-child {
      margin-top: 0;
    }
  }

  ul {
    padding-left: 20px;
    line-height: 1.8;
    color: $text-regular;
  }
}

.dimension-layout {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  align-items: center;

  .dimension-radar {
    flex: 1 1 320px;
    min-width: 280px;
  }

  .dimension-bars {
    flex: 1 1 280px;
    min-width: 240px;
  }
}

.dimension-item {
  margin-bottom: 16px;

  .dimension-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;

    .dimension-name {
      font-size: 14px;
      color: $text-primary;
    }

    .dimension-score {
      font-size: 14px;
      font-weight: 600;
      color: $text-primary;
    }
  }
}

.comment-section {
  .comment-text {
    font-size: 14px;
    color: $text-regular;
    line-height: 1.7;
    background: $bg-base;
    padding: 16px;
    border-radius: 8px;
  }
}

.question-review-section {
  margin-top: 8px;
}

.review-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;

  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
}
</style>

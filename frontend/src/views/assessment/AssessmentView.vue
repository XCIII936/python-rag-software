<template>
  <div class="page-container">
    <div class="page-header">
      <h2>章节测评</h2>
    </div>

    <el-card shadow="never" v-loading="loading">
      <template v-if="!loading && questions.length === 0">
        <el-empty description="暂无测评题目" />
      </template>

      <template v-if="questions.length > 0">
        <div class="assessment-progress">
          <span>第 {{ currentIndex + 1 }} / {{ questions.length }} 题</span>
          <el-progress
            :percentage="Math.round(((currentIndex + 1) / questions.length) * 100)"
            :stroke-width="8"
          />
        </div>

        <el-divider />

        <div class="question-card">
          <h3 class="question-title">{{ currentIndex + 1 }}. {{ currentQuestion.question }}</h3>

          <div class="options-list">
            <div
              v-for="(option, idx) in currentQuestion.options"
              :key="idx"
              :class="[
                'option-item',
                { 'option-selected': selectedIndex === idx },
                { 'option-correct': submitted && idx === currentQuestion.correct },
                { 'option-wrong': submitted && selectedIndex === idx && idx !== currentQuestion.correct },
              ]"
              @click="!submitted && (selectedIndex = idx)"
            >
              <span class="option-label">{{ String.fromCharCode(65 + idx) }}</span>
              <span class="option-text">{{ option }}</span>
              <el-icon v-if="submitted && idx === currentQuestion.correct" color="#67C23A"><Check /></el-icon>
              <el-icon v-else-if="submitted && selectedIndex === idx && idx !== currentQuestion.correct" color="#F56C6C"><Close /></el-icon>
            </div>
          </div>

          <div v-if="submitted" class="question-feedback">
            <el-alert
              :type="selectedIndex === currentQuestion.correct ? 'success' : 'error'"
              :description="currentQuestion.explanation"
              show-icon
              :closable="false"
            />
          </div>
        </div>

        <div class="assessment-actions">
          <el-button v-if="!submitted" type="primary" :disabled="selectedIndex === null" @click="submitAnswer">
            提交答案
          </el-button>
          <el-button v-else @click="nextQuestion">
            {{ currentIndex < questions.length - 1 ? '下一题' : '查看结果' }}
          </el-button>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const questions = ref<any[]>([])
const currentIndex = ref(0)
const selectedIndex = ref<number | null>(null)
const submitted = ref(false)
const answers = ref<number[]>([])

const currentQuestion = computed(() => questions.value[currentIndex.value])

onMounted(async () => {
  const chapterId = Number(route.params.id)
  try {
    // TODO: 接入后端 API 获取测评题目
    // 模拟数据
    questions.value = [
      {
        question: '以下哪种排序算法的时间复杂度为 O(n log n)？',
        options: ['冒泡排序', '快速排序', '选择排序', '插入排序'],
        correct: 1,
        explanation: '快速排序的平均时间复杂度为 O(n log n)。冒泡、选择、插入排序的时间复杂度均为 O(n^2)。',
      },
      {
        question: '在计算机科学中，栈（Stack）是一种什么结构？',
        options: ['先进先出（FIFO）', '先进后出（FILO）', '随机访问', '以上都不是'],
        correct: 1,
        explanation: '栈是一种先进后出（FILO, First In Last Out）的数据结构。',
      },
      {
        question: 'HTTP 状态码 404 表示什么？',
        options: ['服务器错误', '未授权', '资源未找到', '请求成功'],
        correct: 2,
        explanation: '404 Not Found 表示服务器无法找到请求的资源。',
      },
    ]
  } catch {
    // 错误已在 request.ts 中处理
  } finally {
    loading.value = false
  }
})

function submitAnswer() {
  if (selectedIndex.value === null) {
    ElMessage.warning('请先选择一个答案')
    return
  }
  submitted.value = true
  answers.value[currentIndex.value] = selectedIndex.value
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    selectedIndex.value = answers.value[currentIndex.value] ?? null
    submitted.value = answers.value[currentIndex.value] !== undefined
  } else {
    // 查看结果
    const correctCount = answers.value.filter((a, i) => a === questions.value[i]?.correct).length
    router.push(`/assessment/0/results?correct=${correctCount}&total=${questions.value.length}`)
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.assessment-progress {
  display: flex;
  align-items: center;
  gap: 16px;

  span {
    white-space: nowrap;
    font-size: 14px;
    color: $text-secondary;
  }

  .el-progress {
    flex: 1;
  }
}

.question-card {
  .question-title {
    font-size: 18px;
    font-weight: 600;
    color: $text-primary;
    line-height: 1.6;
  }
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 20px 0;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid $border-base;
  border-radius: 8px;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    border-color: $primary-color;
  }

  &.option-selected {
    border-color: $primary-color;
    background-color: rgba(64, 158, 255, 0.05);
  }

  &.option-correct {
    border-color: $success-color;
    background-color: rgba(103, 194, 58, 0.05);
  }

  &.option-wrong {
    border-color: $danger-color;
    background-color: rgba(245, 108, 108, 0.05);
  }
}

.option-label {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: $bg-base;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: $text-regular;
  flex-shrink: 0;
}

.option-text {
  flex: 1;
  color: $text-primary;
}

.question-feedback {
  margin: 20px 0;
}

.assessment-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}
</style>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>章节测评</h2>
    </div>

    <el-card shadow="never" v-loading="loading">
      <template v-if="!loading && questions.length === 0">
        <el-empty description="暂无测评题目" />
      </template>

      <template v-if="questions.length > 0 && currentQuestion">
        <div class="assessment-progress">
          <span>第 {{ currentIndex + 1 }} / {{ totalCount }} 题</span>
          <el-progress
            :percentage="Math.round(((currentIndex + 1) / totalCount) * 100)"
            :stroke-width="8"
          />
        </div>

        <el-divider />

        <div class="question-card">
          <el-tag :type="questionTypeTag" size="small" effect="plain">
            {{ questionTypeLabel }}
          </el-tag>
          <h3 class="question-title">{{ currentIndex + 1 }}. {{ currentQuestion.question_content }}</h3>

          <!-- 选择题选项 -->
          <div v-if="currentQuestion.question_type === 'choice' && parsedOptions.length > 0" class="options-list">
            <div
              v-for="(option, idx) in parsedOptions"
              :key="idx"
              :class="[
                'option-item',
                { 'option-selected': selectedIndex === idx },
              ]"
              @click="!submitted && (selectedIndex = idx)"
            >
              <span class="option-label">{{ String.fromCharCode(65 + idx) }}</span>
              <span class="option-text">{{ option }}</span>
            </div>
          </div>

          <!-- 判断题选项 -->
          <div v-if="currentQuestion.question_type === 'true_false'" class="options-list">
            <div
              v-for="(opt, idx) in ['正确', '错误']"
              :key="idx"
              :class="[
                'option-item',
                { 'option-selected': selectedIndex === idx },
              ]"
              @click="!submitted && (selectedIndex = idx)"
            >
              <span class="option-label">{{ idx === 0 ? '✓' : '✗' }}</span>
              <span class="option-text">{{ opt }}</span>
            </div>
          </div>

          <!-- 简答题输入 -->
          <div v-if="currentQuestion.question_type === 'short_answer'" class="short-answer-input">
            <el-input
              v-model="shortAnswerText"
              type="textarea"
              :rows="4"
              placeholder="请输入你的答案..."
              :disabled="submitted"
            />
          </div>
        </div>

        <div class="assessment-actions">
          <el-button
            v-if="currentIndex > 0"
            @click="prevQuestion"
          >
            上一题
          </el-button>
          <el-button
            v-if="!submitted"
            type="primary"
            :disabled="!canSubmit"
            @click="handleSubmitAnswer"
          >
            提交答案
          </el-button>
          <el-button v-else-if="!allAnswered" @click="nextQuestion">
            下一题
          </el-button>
          <el-button v-else type="success" :loading="submitting" @click="handleSubmitAll">
            交卷
          </el-button>
        </div>

        <div v-if="submitted && !allAnswered" class="answered-hint">
          <el-alert type="success" :closable="false" show-icon>
            <template #title>
              答案已保存（{{ answeredCount }}/{{ totalCount }}）
            </template>
          </el-alert>
        </div>
      </template>

      <!-- 加载完成后但无题目 -->
      <template v-if="!loading && questions.length === 0">
        <div style="text-align: center; padding: 40px 0;">
          <el-button type="primary" @click="router.push('/chapters')">
            返回章节列表
          </el-button>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  startAssessment,
  getCurrentQuestion,
  submitAnswer as apiSubmitAnswer,
  submitAssessment,
  type QuestionData,
  type StartResult,
} from '@/api/assessment'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const submitting = ref(false)
const questions = ref<QuestionData[]>([])
const recordId = ref<number>(0)
const totalCount = ref(0)
const answeredCount = ref(0)
const currentIndex = ref(0)
const selectedIndex = ref<number | null>(null)
const shortAnswerText = ref('')
const submitted = ref(false)
const allAnswered = ref(false)

// Track answers per question index for back/forward navigation
interface AnswerState {
  selectedIndex: number | null
  shortAnswerText: string
  submitted: boolean
}
const answerMap = ref<Record<number, AnswerState>>({})

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)

const parsedOptions = computed(() => {
  const q = currentQuestion.value
  if (!q || !q.options) return []
  try {
    return JSON.parse(q.options)
  } catch {
    return []
  }
})

const questionTypeLabel = computed(() => {
  const type = currentQuestion.value?.question_type
  switch (type) {
    case 'choice': return '选择题'
    case 'true_false': return '判断题'
    case 'short_answer': return '简答题'
    default: return type || ''
  }
})

const questionTypeTag = computed(() => {
  const type = currentQuestion.value?.question_type
  switch (type) {
    case 'choice': return 'primary'
    case 'true_false': return 'warning'
    case 'short_answer': return 'success'
    default: return 'info'
  }
})

const canSubmit = computed(() => {
  if (!currentQuestion.value) return false
  if (currentQuestion.value.question_type === 'short_answer') {
    return shortAnswerText.value.trim().length > 0
  }
  return selectedIndex.value !== null
})

onMounted(async () => {
  const chapterId = Number(route.params.id)
  if (!chapterId) {
    ElMessage.error('无效的章节 ID')
    loading.value = false
    return
  }

  try {
    // 开始测评 — 后端会通过 LLM 生成题目
    const result: StartResult = await startAssessment(chapterId)
    recordId.value = result.record_id
    totalCount.value = result.total_questions

    // 逐个加载题目
    await loadNextQuestion()
  } catch (err: any) {
    ElMessage.error(err.message || '无法开始测评，请确认该章节已配置考核')
  } finally {
    loading.value = false
  }
})

async function loadNextQuestion() {
  if (!recordId.value) return
  try {
    const res = await getCurrentQuestion(recordId.value)
    if ('status' in res && res.status === 'complete') {
      // 所有题目已加载完毕
      allAnswered.value = true
      return
    }
    questions.value.push(res as QuestionData)
  } catch {
    ElMessage.error('加载题目失败')
  }
}

function saveCurrentAnswer() {
  // 保存当前答案到 answerMap
  answerMap.value[currentIndex.value] = {
    selectedIndex: selectedIndex.value,
    shortAnswerText: shortAnswerText.value,
    submitted: submitted.value,
  }
}

function restoreAnswer(index: number) {
  const saved = answerMap.value[index]
  if (saved) {
    selectedIndex.value = saved.selectedIndex
    shortAnswerText.value = saved.shortAnswerText
    submitted.value = saved.submitted
  } else {
    selectedIndex.value = null
    shortAnswerText.value = ''
    submitted.value = false
  }
}

function handleSubmitAnswer() {
  if (!canSubmit.value) {
    ElMessage.warning('请先作答')
    return
  }

  // 获取答案文本
  let answer = ''
  const q = currentQuestion.value
  if (!q) return

  if (q.question_type === 'short_answer') {
    answer = shortAnswerText.value.trim()
  } else if (q.question_type === 'choice' && selectedIndex.value !== null) {
    // Use the option letter (A/B/C/D) for comparison, not the full text
    answer = String.fromCharCode(65 + selectedIndex.value)
  } else if (q.question_type === 'true_false') {
    answer = selectedIndex.value === 0 ? '正确' : '错误'
  }

  if (!answer) {
    ElMessage.warning('请先作答')
    return
  }

  // 调用后端提交答案
  apiSubmitAnswer(recordId.value, q.id, answer)
    .then((res: { answered: number; status: string }) => {
      answeredCount.value = res.answered
      submitted.value = true
      saveCurrentAnswer()

      if (res.status === 'completed') {
        allAnswered.value = true
      }
    })
    .catch((err: any) => {
      ElMessage.error(err.message || '提交答案失败')
    })
}

function nextQuestion() {
  // 显示下一题
  if (currentIndex.value < totalCount.value - 1) {
    saveCurrentAnswer()
    currentIndex.value++
    restoreAnswer(currentIndex.value)

    // 如果该题还没加载，从后端获取
    if (!questions.value[currentIndex.value]) {
      loadNextQuestion()
    }
  }
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    saveCurrentAnswer()
    currentIndex.value--
    restoreAnswer(currentIndex.value)
  }
}

async function handleSubmitAll() {
  if (!recordId.value) return
  submitting.value = true
  try {
    const result = await submitAssessment(recordId.value)
    ElMessage.success('测评完成！')
    router.push(
      `/assessment/${recordId.value}/results?correct=${result.correct_answers}&total=${result.total_questions}&score=${Math.round(result.total_score)}`
    )
  } catch (err: any) {
    ElMessage.error(err.message || '交卷失败')
  } finally {
    submitting.value = false
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
    margin-top: 12px;
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

.short-answer-input {
  margin: 20px 0;
}

.assessment-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
}

.answered-hint {
  margin-top: 16px;
}
</style>

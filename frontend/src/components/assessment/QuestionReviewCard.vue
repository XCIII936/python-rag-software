<template>
  <div class="review-card" :class="{ 'review-wrong': item.is_correct === false, 'review-correct': item.is_correct === true }">
    <div class="review-header">
      <div class="review-header-left">
        <el-tag :type="typeTagType" size="small" effect="plain">{{ typeLabel }}</el-tag>
        <span class="review-index">第 {{ item.question_index + 1 }} 题</span>
      </div>
      <div class="review-header-right">
        <el-tag v-if="item.is_correct === true" type="success" size="small" effect="dark">
          <el-icon><CircleCheck /></el-icon> 正确
        </el-tag>
        <el-tag v-else-if="item.is_correct === false" type="danger" size="small" effect="dark">
          <el-icon><CircleClose /></el-icon> 错误
        </el-tag>
        <span class="review-score">{{ item.score ?? 0 }} 分</span>
      </div>
    </div>

    <div class="review-question">{{ item.question_content }}</div>

    <!-- 选择题选项列表 -->
    <div v-if="item.question_type === 'choice' && item.options && item.options.length" class="review-options">
      <div
        v-for="(opt, idx) in item.options"
        :key="idx"
        class="review-option-item"
        :class="{
          'opt-correct': isCorrectOption(idx),
          'opt-user-wrong': isUserWrongOption(idx),
        }"
      >
        <span class="opt-label">{{ String.fromCharCode(65 + idx) }}</span>
        <span class="opt-text">{{ opt }}</span>
        <el-icon v-if="isCorrectOption(idx)" class="opt-icon opt-icon-correct"><CircleCheck /></el-icon>
        <el-icon v-else-if="isUserWrongOption(idx)" class="opt-icon opt-icon-wrong"><CircleClose /></el-icon>
      </div>
    </div>

    <!-- 答案对比 -->
    <div class="review-answers">
      <div class="answer-row">
        <span class="answer-label">你的答案：</span>
        <span :class="['answer-value', item.is_correct === false ? 'answer-wrong-text' : 'answer-correct-text']">
          {{ item.user_answer || '（未作答）' }}
        </span>
      </div>
      <div v-if="item.is_correct === false" class="answer-row">
        <span class="answer-label">正确答案：</span>
        <span class="answer-value answer-correct-text">{{ item.correct_answer }}</span>
      </div>
    </div>

    <!-- AI 简评 -->
    <div v-if="item.ai_evaluation" class="review-ai-eval">
      <el-icon><ChatDotRound /></el-icon>
      <span>{{ item.ai_evaluation }}</span>
    </div>

    <!-- 详细纠正说明 -->
    <div v-if="item.explanation" class="review-explanation">
      <div class="explanation-title">
        <el-icon><Reading /></el-icon>
        <span>纠正与讲解</span>
      </div>
      <div class="explanation-content">{{ item.explanation }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheck, CircleClose, ChatDotRound, Reading } from '@element-plus/icons-vue'
import type { QuestionReviewItem } from '@/api/assessment'

const props = defineProps<{
  item: QuestionReviewItem
}>()

const typeLabel = computed(() => {
  switch (props.item.question_type) {
    case 'choice': return '选择题'
    case 'true_false': return '判断题'
    case 'short_answer': return '简答题'
    default: return props.item.question_type
  }
})

const typeTagType = computed(() => {
  switch (props.item.question_type) {
    case 'choice': return 'primary'
    case 'true_false': return 'warning'
    case 'short_answer': return 'success'
    default: return 'info'
  }
})

function isCorrectOption(idx: number): boolean {
  const letter = String.fromCharCode(65 + idx)
  return props.item.correct_answer?.trim().toUpperCase() === letter
}

function isUserWrongOption(idx: number): boolean {
  if (props.item.is_correct !== false) return false
  const letter = String.fromCharCode(65 + idx)
  return props.item.user_answer?.trim().toUpperCase() === letter && !isCorrectOption(idx)
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.review-card {
  border: 1px solid $border-light;
  border-radius: $border-radius-medium;
  padding: 16px 18px;
  margin-bottom: 16px;
  background: #fff;

  &.review-wrong {
    border-left: 4px solid $danger-color;
    background: #fef7f7;
  }

  &.review-correct {
    border-left: 4px solid $success-color;
  }
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.review-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.review-index {
  font-size: 13px;
  color: $text-secondary;
}

.review-header-right {
  display: flex;
  align-items: center;
  gap: 10px;

  .el-tag .el-icon {
    vertical-align: -2px;
    margin-right: 2px;
  }
}

.review-score {
  font-size: 14px;
  font-weight: 600;
  color: $text-primary;
}

.review-question {
  font-size: 15px;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.6;
  margin-bottom: 12px;
}

.review-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.review-option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid $border-lighter;
  font-size: 13px;
  color: $text-regular;

  &.opt-correct {
    border-color: $success-color;
    background: rgba(103, 194, 58, 0.08);
    color: $text-primary;
  }

  &.opt-user-wrong {
    border-color: $danger-color;
    background: rgba(245, 108, 108, 0.08);
    color: $text-primary;
  }
}

.opt-label {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: $bg-base;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.opt-text {
  flex: 1;
}

.opt-icon {
  flex-shrink: 0;
}

.opt-icon-correct {
  color: $success-color;
}

.opt-icon-wrong {
  color: $danger-color;
}

.review-answers {
  margin-bottom: 10px;
}

.answer-row {
  font-size: 13.5px;
  line-height: 1.8;
}

.answer-label {
  color: $text-secondary;
}

.answer-value {
  font-weight: 500;
}

.answer-wrong-text {
  color: $danger-color;
}

.answer-correct-text {
  color: $success-color;
}

.review-ai-eval {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: $text-regular;
  background: $bg-base;
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 8px;

  .el-icon {
    margin-top: 2px;
    flex-shrink: 0;
    color: $primary-color;
  }
}

.review-explanation {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 6px;
  padding: 10px 12px;
}

.explanation-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #d48806;
  margin-bottom: 6px;
}

.explanation-content {
  font-size: 13.5px;
  color: $text-regular;
  line-height: 1.7;
  white-space: pre-wrap;
}
</style>

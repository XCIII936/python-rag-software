<template>
  <div class="page-container">
    <div class="page-header">
      <h2>考核配置</h2>
    </div>

    <el-card shadow="never" v-loading="loading">
      <!-- 章节信息 -->
      <el-descriptions :column="2" border class="chapter-info">
        <el-descriptions-item label="章节" label-class-name="desc-label">
          {{ chapter?.title || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="已有题目数" label-class-name="desc-label">
          {{ configData.total_questions ?? '未配置' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="130px"
        label-position="top"
      >
        <!-- 知识点 -->
        <el-form-item label="考核知识点" prop="knowledgePoints" class="config-section">
          <div class="form-help">输入知识点后按回车添加，点击标签上的 × 可删除</div>
          <el-select
            v-model="form.knowledgePoints"
            multiple
            filterable
            allow-create
            default-first-option
            :reserve-keyword="false"
            placeholder="输入知识点按回车添加"
            style="width: 100%"
            class="knowledge-select"
            @keydown.enter.prevent
          >
            <el-option
              v-for="item in form.knowledgePoints"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>

        <!-- 题型分配 -->
        <el-form-item label="题型分配" prop="questionTypes" class="config-section">
          <div class="form-help">设置每种题型的题目数量，至少配置一种题型且总数≥1</div>
          <div class="question-types-grid">
            <div class="type-item">
              <span class="type-label">选择题</span>
              <el-input-number
                v-model="form.questionTypes.choice"
                :min="0"
                :max="20"
                size="small"
                controls-position="right"
              />
            </div>
            <div class="type-item">
              <span class="type-label">判断题</span>
              <el-input-number
                v-model="form.questionTypes.true_false"
                :min="0"
                :max="20"
                size="small"
                controls-position="right"
              />
            </div>
            <div class="type-item">
              <span class="type-label">简答题</span>
              <el-input-number
                v-model="form.questionTypes.short_answer"
                :min="0"
                :max="20"
                size="small"
                controls-position="right"
              />
            </div>
            <div class="type-total">
              共 <strong>{{ totalQuestions }}</strong> 题
            </div>
          </div>
        </el-form-item>

        <!-- 评价维度 -->
        <el-form-item label="评价维度" prop="evaluationDimensions" class="config-section">
          <div class="form-help">设置评分维度和权重，权重总和必须为 1.0</div>
          <div
            v-for="(dim, idx) in form.evaluationDimensions"
            :key="idx"
            class="dimension-row"
          >
            <el-input
              v-model="dim.name"
              placeholder="维度名称"
              size="small"
              style="width: 200px"
            />
            <span class="dimension-weight-label">权重</span>
            <el-input-number
              v-model="dim.weight"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="1"
              size="small"
              controls-position="right"
              style="width: 140px"
            />
            <el-button
              size="small"
              type="danger"
              link
              @click="removeDimension(idx)"
              :disabled="form.evaluationDimensions.length <= 1"
            >
              删除
            </el-button>
          </div>
          <div v-if="weightTotal !== 1.0 && form.evaluationDimensions.length > 0" class="weight-hint">
            权重总和为 {{ weightTotal.toFixed(1) }}，{{ weightTotal > 1.0 ? '超出 1.0' : '不足 1.0' }}
          </div>
          <el-button size="small" class="add-dim-btn" @click="addDimension">
            + 添加维度
          </el-button>
        </el-form-item>

        <!-- 及格分数 -->
        <el-form-item label="及格分数" prop="passingScore" class="config-section">
          <el-input-number
            v-model="form.passingScore"
            :min="0"
            :max="100"
            size="small"
            controls-position="right"
          />
          <span class="score-hint">分（默认 60）</span>
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave" size="large">
            保存配置
          </el-button>
          <el-button @click="router.back()" size="large">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getChapter } from '@/api/chapter'
import { getAssessmentConfig, saveAssessmentConfig } from '@/api/assessment'

interface Dimension {
  name: string
  weight: number
}

interface ConfigForm {
  knowledgePoints: string[]
  questionTypes: {
    choice: number
    true_false: number
    short_answer: number
  }
  evaluationDimensions: Dimension[]
  passingScore: number
}

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const saving = ref(false)
const formRef = ref<FormInstance>()
const chapter = ref<{ id: number; title: string } | null>(null)

const form = reactive<ConfigForm>({
  knowledgePoints: [],
  questionTypes: {
    choice: 2,
    true_false: 1,
    short_answer: 1,
  },
  evaluationDimensions: [
    { name: '知识掌握', weight: 0.4 },
    { name: '理解应用', weight: 0.4 },
    { name: '分析能力', weight: 0.2 },
  ],
  passingScore: 60,
})

const rules: FormRules = {
  knowledgePoints: [
    { required: true, message: '请至少添加一个知识点', trigger: 'change' },
  ],
  passingScore: [
    { required: true, message: '请设置及格分数', trigger: 'blur' },
  ],
}

const totalQuestions = computed(() => {
  return Object.values(form.questionTypes).reduce((a, b) => a + b, 0)
})

const weightTotal = computed(() => {
  return form.evaluationDimensions.reduce((s, d) => s + d.weight, 0)
})

function addDimension() {
  form.evaluationDimensions.push({ name: '', weight: 0.2 })
}

function removeDimension(idx: number) {
  if (form.evaluationDimensions.length > 1) {
    form.evaluationDimensions.splice(idx, 1)
  }
}

onMounted(async () => {
  const chapterId = Number(route.params.id)
  if (!chapterId) {
    ElMessage.error('无效的章节 ID')
    loading.value = false
    return
  }

  try {
    // 获取章节信息
    const ch = await getChapter(chapterId)
    chapter.value = { id: ch.id, title: ch.title }

    // 尝试获取已有配置（null = 尚未配置，不影响）
    const config = await getAssessmentConfig(chapterId)
    if (config) {
      const kp = config.knowledge_points
      if (typeof kp === 'string') {
        try { form.knowledgePoints = JSON.parse(kp) } catch { form.knowledgePoints = [] }
      } else if (Array.isArray(kp)) {
        form.knowledgePoints = kp
      }

      const qt = config.question_types
      if (typeof qt === 'string') {
        try {
          const parsed = JSON.parse(qt)
          form.questionTypes.choice = parsed.choice ?? 0
          form.questionTypes.true_false = parsed.true_false ?? 0
          form.questionTypes.short_answer = parsed.short_answer ?? 0
        } catch { /* keep defaults */ }
      } else if (qt && typeof qt === 'object') {
        form.questionTypes.choice = (qt as any).choice ?? 0
        form.questionTypes.true_false = (qt as any).true_false ?? 0
        form.questionTypes.short_answer = (qt as any).short_answer ?? 0
      }

      const dim = config.evaluation_dimensions
      if (typeof dim === 'string') {
        try {
          const parsed = JSON.parse(dim)
          if (Array.isArray(parsed) && parsed.length > 0) {
            form.evaluationDimensions = parsed
          }
        } catch { /* keep defaults */ }
      } else if (Array.isArray(dim) && dim.length > 0) {
        form.evaluationDimensions = dim as Dimension[]
      }

      if (config.passing_score != null) {
        form.passingScore = config.passing_score
      }
    }
    // config === null → 尚未配置，使用表单默认值
  } catch {
    ElMessage.error('获取章节信息失败')
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  if (!formRef.value || !chapter.value) return

  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请完善配置信息')
    return
  }

  if (totalQuestions.value < 1) {
    ElMessage.warning('请至少配置 1 道题目')
    return
  }

  if (Math.abs(weightTotal.value - 1.0) > 0.01) {
    ElMessage.warning('评价维度的权重总和必须等于 1.0')
    return
  }

  saving.value = true
  try {
    await saveAssessmentConfig({
      chapter_id: chapter.value.id,
      knowledge_points: form.knowledgePoints,
      question_types: {
        choice: form.questionTypes.choice,
        true_false: form.questionTypes.true_false,
        short_answer: form.questionTypes.short_answer,
      },
      evaluation_dimensions: form.evaluationDimensions.map(d => ({
        name: d.name,
        weight: d.weight,
      })),
      passing_score: form.passingScore,
    })
    ElMessage.success('考核配置保存成功')
    router.back()
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.chapter-info {
  margin-bottom: 8px;
}

.config-section {
  :deep(.el-form-item__label) {
    font-weight: 600;
    font-size: 15px;
    color: $text-primary;
  }
}

.form-help {
  font-size: 13px;
  color: $text-secondary;
  margin-bottom: 8px;
  line-height: 1.4;
}

.knowledge-select {
  :deep(.el-select__tags) {
    gap: 4px;
  }
}

.question-types-grid {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 20px;

  .type-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .type-label {
    font-size: 14px;
    color: $text-regular;
    white-space: nowrap;
  }

  .type-total {
    font-size: 14px;
    color: $text-secondary;
    padding-left: 12px;
    border-left: 1px solid $border-base;
  }
}

.dimension-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;

  .dimension-weight-label {
    font-size: 13px;
    color: $text-secondary;
  }
}

.weight-hint {
  font-size: 13px;
  color: $warning-color;
  margin-bottom: 8px;
}

.add-dim-btn {
  margin-top: 4px;
}

.score-hint {
  font-size: 13px;
  color: $text-secondary;
  margin-left: 8px;
}
</style>

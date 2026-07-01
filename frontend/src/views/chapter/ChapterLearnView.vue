<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ chapter?.title || '章节学习' }}</h2>
      <div class="header-actions" v-if="chapter">
        <el-button type="primary" @click="router.push(`/chapters/${chapter.id}/assessment`)">
          开始测评
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="18">
        <el-card shadow="never" v-loading="loading">
          <template v-if="chapter">
            <h3>{{ chapter.title }}</h3>
            <p class="chapter-description">{{ chapter.description }}</p>
            <el-divider />

            <!-- 文档列表 -->
            <div v-if="documents.length > 0" class="document-list">
              <div
                v-for="doc in documents"
                :key="doc.id"
                class="document-item"
                @click="selectDocument(doc)"
              >
                <el-icon><Document /></el-icon>
                <span class="doc-title">{{ doc.title }}</span>
                <el-tag v-if="doc.completed" size="small" type="success">已完成</el-tag>
              </div>
            </div>
            <el-empty v-else description="暂无学习文档" />
          </template>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="never">
          <template #header>
            <span>学习进度</span>
          </template>
          <div class="progress-info">
            <el-progress type="dashboard" :percentage="progressPercent" />
            <p class="progress-text">
              {{ completedCount }} / {{ documents.length }} 已完成
            </p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document } from '@element-plus/icons-vue'
import { getChapter, type Chapter } from '@/api/chapter'

const route = useRoute()
const router = useRouter()
const chapter = ref<Chapter | null>(null)
const loading = ref(true)
const documents = ref<any[]>([])
const completedCount = ref(0)
const progressPercent = computed(() => {
  if (documents.value.length === 0) return 0
  return Math.round((completedCount.value / documents.value.length) * 100)
})

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    const res = await getChapter(id)
    chapter.value = res.data
    // TODO: 获取文档列表
  } catch {
    // 错误已在 request.ts 中处理
  } finally {
    loading.value = false
  }
})

function selectDocument(doc: any) {
  // TODO: 实现文档查看
  console.log('选择文档:', doc)
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.chapter-description {
  color: $text-secondary;
  line-height: 1.8;
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid $border-lighter;
  border-radius: 8px;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    border-color: $primary-color;
    background-color: rgba(64, 158, 255, 0.03);
  }

  .doc-title {
    flex: 1;
    font-size: 14px;
    color: $text-primary;
  }
}

.progress-info {
  text-align: center;

  .progress-text {
    margin-top: 16px;
    color: $text-secondary;
    font-size: 14px;
  }
}
</style>

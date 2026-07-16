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
                <el-tag v-if="doc.file_type === 'md'" size="small" type="success" effect="plain">MD</el-tag>
                <el-tag v-if="doc.status === 'parsed'" size="small" type="success">已完成</el-tag>
                <el-button
                  size="small"
                  type="primary"
                  link
                  class="download-btn"
                  @click.stop="downloadDocument(doc)"
                >
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
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

    <!-- Markdown 预览弹窗 -->
    <el-dialog
      v-model="mdPreviewVisible"
      :title="mdPreviewTitle"
      width="720px"
      top="5vh"
      class="md-preview-dialog"
    >
      <div v-loading="mdLoading" class="md-preview-body markdown-body" v-html="mdPreviewHtml"></div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Download } from '@element-plus/icons-vue'
import { Marked } from 'marked'
import { getChapter, type Chapter } from '@/api/chapter'
import { getDocuments, type DocumentData } from '@/api/document'
import { getToken } from '@/utils/auth'

const marked = new Marked({ breaks: true, gfm: true })

const route = useRoute()
const router = useRouter()
const chapter = ref<Chapter | null>(null)
const loading = ref(true)
const documents = ref<DocumentData[]>([])
const completedCount = ref(0)
const progressPercent = computed(() => {
  if (documents.value.length === 0) return 0
  return Math.round((completedCount.value / documents.value.length) * 100)
})

// ── Markdown 预览弹窗状态 ──
const mdPreviewVisible = ref(false)
const mdPreviewTitle = ref('')
const mdPreviewHtml = ref('')
const mdLoading = ref(false)

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    const [ch, docs] = await Promise.all([
      getChapter(id),
      getDocuments(id),
    ])
    chapter.value = ch
    documents.value = docs
    // Documents with status === 'parsed' count as "completed"
    completedCount.value = docs.filter(d => d.status === 'parsed').length
  } catch {
    // 错误已在 request.ts 中处理
  } finally {
    loading.value = false
  }
})

async function selectDocument(doc: DocumentData) {
  const token = getToken()
  const fileUrl = `/api/v1/documents/${doc.id}/file?token=${token}`

  if (doc.file_type === 'pdf') {
    window.open(fileUrl, '_blank')
  } else if (doc.file_type === 'md' || doc.file_type === 'markdown') {
    mdPreviewTitle.value = doc.title
    mdPreviewVisible.value = true
    mdLoading.value = true
    mdPreviewHtml.value = ''
    try {
      const resp = await fetch(fileUrl)
      if (!resp.ok) throw new Error('获取文档内容失败')
      const text = await resp.text()
      mdPreviewHtml.value = marked.parse(text) as string
    } catch (err: any) {
      ElMessage.error(err.message || 'Markdown 预览失败')
      mdPreviewVisible.value = false
    } finally {
      mdLoading.value = false
    }
  } else {
    downloadDocument(doc)
  }
}

function downloadDocument(doc: DocumentData) {
  const token = getToken()
  const fileUrl = `/api/v1/documents/${doc.id}/file?token=${token}`
  const link = document.createElement('a')
  link.href = fileUrl
  link.download = doc.title || 'document'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success(`「${doc.title}」开始下载`)
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

  .download-btn {
    margin-left: auto;
    flex-shrink: 0;
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

.md-preview-body {
  max-height: 70vh;
  overflow-y: auto;
  line-height: 1.7;
  color: $text-regular;
  padding: 4px 8px;

  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    color: $text-primary;
    margin: 20px 0 10px;

    &:first-child {
      margin-top: 0;
    }
  }

  :deep(p) {
    margin: 10px 0;
  }

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;

    th, td {
      border: 1px solid $border-light;
      padding: 6px 10px;
      font-size: 13.5px;
    }

    th {
      background: $bg-base;
    }
  }

  :deep(pre) {
    background: #f5f5f5;
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
  }

  :deep(code) {
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9em;
  }

  :deep(pre code) {
    background: none;
    padding: 0;
  }

  :deep(ul), :deep(ol) {
    padding-left: 20px;
  }

  :deep(blockquote) {
    border-left: 3px solid $primary-color;
    padding-left: 12px;
    color: $text-secondary;
    margin: 8px 0;
  }
}
</style>

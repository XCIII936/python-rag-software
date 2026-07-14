<template>
  <div class="page-container">
    <div class="page-header">
      <h2>知识库</h2>
      <el-button v-if="authStore.isTeacher" type="primary" :icon="Upload" @click="openUploadDialog">
        上传文档
      </el-button>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" size="small">
        <el-form-item label="所属章节">
          <el-select v-model="filterChapterId" clearable placeholder="全部章节" @change="loadDocuments">
            <el-option label="全部章节" :value="null" />
            <el-option v-for="ch in chapters" :key="ch.id" :label="ch.title" :value="ch.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterStatus" clearable placeholder="全部状态" @change="loadDocuments">
            <el-option label="全部状态" :value="null" />
            <el-option label="待处理" value="pending" />
            <el-option label="解析中" value="parsing" />
            <el-option label="已完成" value="parsed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 文档列表 -->
    <el-card shadow="never">
      <el-table
        :data="filteredDocuments"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无文档，请点击「上传文档」添加"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="文档名称" min-width="200">
          <template #default="{ row }">
            <span :title="row.title">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chapter_title" label="所属章节" width="130">
          <template #default="{ row }">
            {{ row.chapter_title || (row.chapter_id ? `章节#${row.chapter_id}` : '未指定') }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="statusType(row.status)"
              size="small"
            >
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块数" width="70" align="center" />
        <el-table-column prop="created_at" label="上传时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'failed'"
              size="small"
              type="warning"
              link
              :loading="reprocessingId === row.id"
              @click="handleReprocess(row)"
            >
              重新处理
            </el-button>
            <el-button
              v-if="authStore.isTeacher"
              size="small"
              type="danger"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传弹窗 -->
    <el-dialog v-model="uploadVisible" title="上传文档" width="520px" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :file-list="fileList"
            :on-change="handleFileChange"
            :on-remove="() => { selectedFile = null }"
            accept=".pdf,.ppt,.pptx,.doc,.docx"
            drag
            class="upload-area"
          >
            <el-icon class="upload-icon" :size="40"><Upload /></el-icon>
            <div class="upload-text">
              将文件拖到此处，或<em>点击选择</em>
            </div>
            <template #tip>
              <div class="upload-tip">支持 PDF、PPT、DOCX 格式，单个文件不超过 50MB</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="所属章节">
          <el-select v-model="uploadChapterId" clearable placeholder="选择章节（可选）" style="width: 100%">
            <el-option v-for="ch in chapters" :key="ch.id" :label="ch.title" :value="ch.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          {{ uploading ? '上传中...' : '上传' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { getChapters, type Chapter } from '@/api/chapter'
import {
  getDocuments,
  uploadDocument,
  deleteDocument,
  reprocessDocument,
  type DocumentData,
} from '@/api/document'

const authStore = useAuthStore()

// ── State ──
const loading = ref(true)
const documents = ref<DocumentData[]>([])
const chapters = ref<Chapter[]>([])
const reprocessingId = ref<number | null>(null)

// Filters
const filterChapterId = ref<number | null>(null)
const filterStatus = ref<string | null>(null)

// Upload dialog
const uploadVisible = ref(false)
const uploading = ref(false)
const selectedFile = ref<File | null>(null)
const fileList = ref<any[]>([])
const uploadChapterId = ref<number | null>(null)
const uploadRef = ref<any>(null)

// ── Computed ──

const filteredDocuments = computed(() => {
  let list = documents.value
  if (filterChapterId.value) {
    list = list.filter(d => d.chapter_id === filterChapterId.value)
  }
  if (filterStatus.value) {
    list = list.filter(d => d.status === filterStatus.value)
  }
  return list
})

function statusType(status: string): string {
  switch (status) {
    case 'parsed': return 'success'
    case 'parsing': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case 'parsed': return '已完成'
    case 'parsing': return '解析中'
    case 'pending': return '待处理'
    case 'failed': return '失败'
    default: return status
  }
}

// ── Load ──

async function loadDocuments() {
  loading.value = true
  try {
    documents.value = await getDocuments()
  } catch {
    documents.value = []
  } finally {
    loading.value = false
  }
}

async function loadChapters() {
  try {
    chapters.value = await getChapters()
  } catch {
    chapters.value = []
  }
}

onMounted(async () => {
  await Promise.all([loadDocuments(), loadChapters()])
})

// ── Upload ──

function handleFileChange(uploadFile: any) {
  selectedFile.value = uploadFile.raw || null
}

function openUploadDialog() {
  selectedFile.value = null
  fileList.value = []
  uploadChapterId.value = null
  uploadVisible.value = true
}

async function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploading.value = true
  try {
    await uploadDocument(selectedFile.value, uploadChapterId.value || undefined)
    ElMessage.success('上传成功，正在后台解析文档...')
    uploadVisible.value = false
    await loadDocuments()
  } catch (err: any) {
    ElMessage.error(err.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

// ── Delete ──

async function handleDelete(row: DocumentData) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${row.title}」？\n删除后该文档的所有内容将从知识库中移除。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await deleteDocument(row.id)
    ElMessage.success('删除成功')
    await loadDocuments()
  } catch {
    // cancelled
  }
}

// ── Reprocess ──

async function handleReprocess(row: DocumentData) {
  reprocessingId.value = row.id
  try {
    await reprocessDocument(row.id)
    ElMessage.success('已开始重新处理')
    row.status = 'pending'
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  } finally {
    reprocessingId.value = null
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.filter-card {
  margin-bottom: 16px;
}

.upload-area {
  width: 100%;
}

.upload-icon {
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: $text-regular;

  em {
    color: $primary-color;
    font-style: normal;
  }
}

.upload-tip {
  font-size: 12px;
  color: $text-secondary;
  margin-top: 8px;
}
</style>

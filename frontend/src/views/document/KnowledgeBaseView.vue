<template>
  <div class="page-container">
    <div class="page-header">
      <h2>知识库</h2>
      <el-button v-if="authStore.isTeacher" type="primary" @click="openUploadDialog">
        <el-icon><Upload /></el-icon>上传文档
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="documents" v-loading="loading" stripe style="width: 100%" empty-text="暂无文档">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="文档名称" min-width="200" />
        <el-table-column prop="file_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type || '未知' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chapter_title" label="所属章节" width="150" />
        <el-table-column prop="created_at" label="上传时间" width="170" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link>查看</el-button>
            <el-button v-if="authStore.isTeacher" size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传弹窗 -->
    <el-dialog v-model="uploadVisible" title="上传文档" width="500px">
      <el-form label-width="80px">
        <el-form-item label="文档标题">
          <el-input v-model="uploadForm.title" placeholder="请输入文档标题" />
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            drag
            class="upload-area"
          >
            <el-icon class="upload-icon" :size="40"><Upload /></el-icon>
            <div class="upload-text">
              将文件拖到此处，或<em>点击选择</em>
            </div>
            <template #tip>
              <div class="upload-tip">支持 PDF、DOCX、TXT 格式</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const documents = ref<any[]>([])
const loading = ref(true)
const uploadVisible = ref(false)

const uploadForm = ref({
  title: '',
})

onMounted(async () => {
  try {
    // TODO: 接入后端 API 获取文档列表
    // 模拟空数据
    documents.value = []
  } catch { /* 已处理 */ } finally {
    loading.value = false
  }
})

function openUploadDialog() {
  uploadVisible.value = true
}

function handleDelete(row: any) {
  ElMessageBox.confirm(`确定删除「${row.title}」？`, '确认', { type: 'warning' })
    .then(() => ElMessage.success('删除成功'))
    .catch(() => {})
}
</script>

<style scoped lang="scss">
.upload-area {
  width: 100%;
}
.upload-icon {
  margin-bottom: 8px;
}
.upload-text {
  font-size: 14px;
  color: #606266;
  em {
    color: #409EFF;
    font-style: normal;
  }
}
.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
</style>

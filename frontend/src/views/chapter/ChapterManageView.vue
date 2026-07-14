<template>
  <div class="page-container">
    <div class="page-header">
      <h2>章节管理</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon>创建章节
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table
        :data="chapters"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无章节"
      >
        <el-table-column prop="order_index" label="排序" width="70" />
        <el-table-column prop="title" label="章节名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '已发布' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="document_count" label="文档数" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="success" link @click="router.push(`/admin/chapters/${row.id}/assessment-config`)">配置考核</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingChapter ? '编辑章节' : '创建章节'"
      width="500px"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入章节标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="已发布">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getChapters, createChapter, updateChapter, deleteChapter, type Chapter } from '@/api/chapter'

const chapters = ref<Chapter[]>([])
const loading = ref(true)
const dialogVisible = ref(false)
const editingChapter = ref<Chapter | null>(null)
const saving = ref(false)
const formRef = ref<FormInstance>()
const router = useRouter()

const formData = reactive({
  title: '',
  description: '',
  is_active: true,
})

const formRules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
}

onMounted(() => fetchChapters())

async function fetchChapters() {
  loading.value = true
  try {
    chapters.value = await getChapters()
  } catch { /* 已处理 */ } finally {
    loading.value = false
  }
}

function openDialog(chapter?: Chapter) {
  if (chapter) {
    editingChapter.value = chapter
    formData.title = chapter.title
    formData.description = chapter.description || ''
    formData.is_active = chapter.is_active ?? true
  } else {
    editingChapter.value = null
    formData.title = ''
    formData.description = ''
    formData.is_active = true
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    saving.value = true
    if (editingChapter.value) {
      await updateChapter(editingChapter.value.id, formData)
      ElMessage.success('更新成功')
    } else {
      await createChapter(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await fetchChapters()
  } catch { /* 已处理 */ } finally {
    saving.value = false
  }
}

async function handleDelete(chapter: Chapter) {
  try {
    await ElMessageBox.confirm(`确定删除「${chapter.title}」？`, '确认', { type: 'warning' })
    await deleteChapter(chapter.id)
    ElMessage.success('删除成功')
    await fetchChapters()
  } catch { /* 已处理 */ }
}

</script>

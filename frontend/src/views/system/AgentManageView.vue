<template>
  <div class="page-container">
    <div class="page-header">
      <h2>智能体管理</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>创建智能体
      </el-button>
    </div>

    <!-- 智能体列表 -->
    <el-card shadow="never">
      <el-table
        :data="agents"
        v-loading="loading"
        stripe
        style="width: 100%"
        empty-text="暂无智能体"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="150">
          <template #default="{ row }">
            <div class="agent-name">
              <el-icon :size="18"><Cpu /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              @click="router.push(`/system/agents/${row.id}`)"
            >
              查看
            </el-button>
            <el-button
              size="small"
              type="primary"
              link
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
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

    <!-- 创建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑智能体' : '创建智能体'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        v-loading="dialogLoading"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入智能体名称" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>

        <el-form-item label="模型" prop="model_name">
          <el-input v-model="formData.model_name" placeholder="例如: gpt-4o" />
        </el-form-item>

        <el-form-item label="系统提示词">
          <el-input
            v-model="formData.system_prompt"
            type="textarea"
            :rows="5"
            placeholder="请输入系统提示词"
          />
        </el-form-item>

        <el-form-item label="温度">
          <el-slider
            v-model="formData.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            show-input
            input-size="small"
          />
        </el-form-item>

        <el-form-item label="最大 Token">
          <el-input-number
            v-model="formData.max_tokens"
            :min="256"
            :max="32768"
            :step="256"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="formData.isActive"
            active-text="启用"
            inactive-text="停用"
          />
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
import { Plus, Cpu } from '@element-plus/icons-vue'
import { getAgents, createAgent, updateAgent, deleteAgent, type Agent } from '@/api/agent'

const router = useRouter()
const agents = ref<Agent[]>([])
const loading = ref(true)
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  name: '',
  description: '',
  model_name: 'gpt-4o',
  system_prompt: '',
  temperature: 0.7,
  max_tokens: 2048,
  isActive: true,
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
}

onMounted(() => {
  fetchAgents()
})

async function fetchAgents() {
  loading.value = true
  try {
    const res = await getAgents()
    agents.value = res.data
  } catch {
    // 错误已在 request.ts 中处理
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(agent: Agent) {
  isEditing.value = true
  editingId.value = agent.id
  formData.name = agent.name
  formData.description = agent.description
  formData.model_name = agent.model_name
  formData.system_prompt = agent.system_prompt
  formData.temperature = agent.temperature
  formData.max_tokens = agent.max_tokens
  formData.isActive = agent.status === 'active'
  dialogVisible.value = true
}

function resetForm() {
  formData.name = ''
  formData.description = ''
  formData.model_name = 'gpt-4o'
  formData.system_prompt = ''
  formData.temperature = 0.7
  formData.max_tokens = 2048
  formData.isActive = true
  formRef.value?.resetFields()
}

async function handleSave() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    saving.value = true

    const payload = {
      name: formData.name,
      description: formData.description || undefined,
      model_name: formData.model_name,
      system_prompt: formData.system_prompt || undefined,
      temperature: formData.temperature,
      max_tokens: formData.max_tokens,
      status: formData.isActive ? 'active' as const : 'inactive' as const,
    }

    if (isEditing.value && editingId.value) {
      await updateAgent(editingId.value, payload)
      ElMessage.success('智能体更新成功')
    } else {
      await createAgent(payload)
      ElMessage.success('智能体创建成功')
    }

    dialogVisible.value = false
    await fetchAgents()
  } catch (err: any) {
    if (err.message) {
      ElMessage.error(err.message)
    }
  } finally {
    saving.value = false
  }
}

async function handleDelete(agent: Agent) {
  try {
    await ElMessageBox.confirm(
      `确定要删除智能体「${agent.name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteAgent(agent.id)
    ElMessage.success('删除成功')
    await fetchAgents()
  } catch {
    // 用户取消或错误
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.agent-name {
  display: flex;
  align-items: center;
  gap: 8px;
  color: $primary-color;
}

.el-table {
  :deep(.el-table__empty-text) {
    padding: 40px 0;
  }
}
</style>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>智能体详情</h2>
      <div class="header-actions">
        <el-button @click="router.push('/system/agents')">返回列表</el-button>
        <el-button type="primary" @click="router.push(`/system/agents/${agentId}/invoke`)">
          调用智能体
        </el-button>
      </div>
    </div>

    <el-card shadow="never" v-loading="loading">
      <template v-if="agent">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="名称" :span="2">{{ agent.name }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ agent.description || '无' }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ agent.model_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="agent.status === 'active' ? 'success' : 'info'" size="small">
              {{ agent.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="温度">{{ agent.temperature }}</el-descriptions-item>
          <el-descriptions-item label="最大 Token">{{ agent.max_tokens }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ agent.created_at }}</el-descriptions-item>
          <el-descriptions-item label="更新时间" :span="2">{{ agent.updated_at }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <el-descriptions title="系统提示词" :column="1" border>
          <el-descriptions-item>
            <pre class="system-prompt">{{ agent.system_prompt || '无' }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAgent, type Agent } from '@/api/agent'

const route = useRoute()
const router = useRouter()
const agentId = Number(route.params.id)
const agent = ref<Agent | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getAgent(agentId)
    agent.value = res.data
  } catch {
    // 已处理
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.system-prompt {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  line-height: 1.6;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}
</style>

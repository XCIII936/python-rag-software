<template>
  <div class="page-container">
    <div class="page-header">
      <h2>调用智能体</h2>
      <el-button @click="router.push('/system/agents')">返回列表</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <span>{{ agent?.name || '智能体' }} - 对话</span>
          </template>

          <div class="chat-messages" ref="messagesRef">
            <template v-if="messages.length === 0">
              <div class="chat-empty">
                <el-icon :size="48" color="#c0c4cc"><ChatLineSquare /></el-icon>
                <p>在下方输入消息开始与智能体对话</p>
              </div>
            </template>

            <div
              v-for="(msg, index) in messages"
              :key="index"
              :class="['message', msg.role === 'user' ? 'message-user' : 'message-assistant']"
            >
              <div :class="msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'">
                <div v-if="msg.loading" class="loading-dots">
                  <span class="dot"></span><span class="dot"></span><span class="dot"></span>
                </div>
                <template v-else>
                  {{ msg.content }}
                </template>
              </div>
            </div>
          </div>

          <div class="chat-input">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              placeholder="输入消息..."
              :disabled="sending"
              @keydown.enter.exact.prevent="handleSend"
            />
            <el-button type="primary" :loading="sending" :disabled="!inputText.trim()" @click="handleSend">
              发送
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <span>智能体信息</span>
          </template>
          <div v-if="agent" class="agent-info">
            <p><strong>名称：</strong>{{ agent.name }}</p>
            <p><strong>模型：</strong>{{ agent.model_name }}</p>
            <p><strong>状态：</strong>
              <el-tag :type="agent.status === 'active' ? 'success' : 'info'" size="small">
                {{ agent.status === 'active' ? '启用' : '停用' }}
              </el-tag>
            </p>
            <el-divider />
            <p><strong>系统提示词：</strong></p>
            <pre class="agent-prompt">{{ agent.system_prompt || '无' }}</pre>
          </div>
          <div v-else-if="loading" v-loading="loading" style="height: 200px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatLineSquare } from '@element-plus/icons-vue'
import { getAgent, type Agent } from '@/api/agent'
import { createSSEConnection, type SSEResult } from '@/utils/sse'

interface ChatMsg {
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
}

const route = useRoute()
const router = useRouter()
const agentId = Number(route.params.id)
const agent = ref<Agent | null>(null)
const loading = ref(true)
const messages = ref<ChatMsg[]>([])
const inputText = ref('')
const sending = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
let currentSSE: SSEResult | null = null

onMounted(async () => {
  try {
    agent.value = await getAgent(agentId)
  } catch { /* 已处理 */ } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  currentSSE?.abort()
})

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''

  const idx = messages.value.length
  messages.value.push({ role: 'assistant', content: '', loading: true })
  sending.value = true
  scrollToBottom()

  try {
    currentSSE = createSSEConnection(
      `/agents/${agentId}/invoke`,
      { message: text },
      {
        onToken: (token: string) => {
          const msg = messages.value[idx]
          if (msg && msg.loading) {
            msg.loading = false
          }
          messages.value[idx] = {
            role: 'assistant',
            content: (messages.value[idx]?.content || '') + token,
          }
          scrollToBottom()
        },
        onDone: () => {
          sending.value = false
          currentSSE = null
          scrollToBottom()
        },
        onError: (error: string) => {
          messages.value[idx] = { role: 'assistant', content: `请求失败: ${error}` }
          sending.value = false
          currentSSE = null
        },
      }
    )
  } catch {
    messages.value[idx] = { role: 'assistant', content: '发送失败，请重试。' }
    sending.value = false
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.chat-messages {
  height: 400px;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: $text-secondary;
}

.message {
  max-width: 80%;
}

.message-user {
  align-self: flex-end;
}

.message-assistant {
  align-self: flex-start;
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid $border-lighter;

  .el-textarea {
    flex: 1;
  }
}

.loading-dots {
  display: flex;
  gap: 4px;
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: $text-secondary;
    animation: dot-bounce 1.4s infinite;
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.agent-info {
  font-size: 14px;
  line-height: 1.8;
  p { margin: 4px 0; }
}

.agent-prompt {
  margin: 0;
  white-space: pre-wrap;
  font-size: 12px;
  line-height: 1.6;
  background: $bg-base;
  padding: 8px;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
}
</style>

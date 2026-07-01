<template>
  <div class="chat-view">
    <div class="chat-messages" ref="messagesRef">
      <template v-if="messages.length === 0">
        <div class="chat-empty">
          <el-icon :size="48" color="#c0c4cc"><ChatLineSquare /></el-icon>
          <h3>学习助手</h3>
          <p>在下方输入您的问题，开始与 AI 助手的对话</p>
        </div>
      </template>

      <template v-else>
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['chat-message', msg.role === 'user' ? 'message-user' : 'message-assistant']"
        >
          <div class="message-avatar">
            <el-avatar
              :size="36"
              :icon="msg.role === 'user' ? UserFilled : Promotion"
              :style="msg.role === 'user' ? {} : { background: '#409EFF' }"
            />
          </div>
          <div class="message-content">
            <div :class="msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'">
              <div v-if="msg.loading" class="loading-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              <div v-else class="markdown-content" v-html="msg.content"></div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div class="chat-input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        placeholder="输入您的问题..."
        :disabled="sending"
        @keydown.enter.exact.prevent="handleSend"
      />
      <el-button
        type="primary"
        :icon="Promotion"
        :loading="sending"
        :disabled="!inputText.trim()"
        @click="handleSend"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ChatLineSquare, UserFilled, Promotion } from '@element-plus/icons-vue'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
}

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const messagesRef = ref<HTMLElement | null>(null)

onMounted(() => {
  // 加载欢迎消息
  messages.value.push({
    role: 'assistant',
    content: '你好！我是课程教学助手，可以帮你解答学习中的问题。请问有什么可以帮助你的？',
  })
})

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  // 添加加载中的助手消息
  const assistantIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', loading: true })
  sending.value = true
  scrollToBottom()

  try {
    // TODO: 接入后端 API
    // 模拟回复
    setTimeout(() => {
      messages.value[assistantIndex] = {
        role: 'assistant',
        content: `收到您的问题：「${text}」<br><br>这是一个模拟回复。请配置后端接口以实现真实的 AI 对话功能。`,
        loading: false,
      }
      sending.value = false
      scrollToBottom()
    }, 1000)
  } catch (err: any) {
    messages.value[assistantIndex] = {
      role: 'assistant',
      content: '抱歉，我遇到了一个错误，请稍后重试。',
      loading: false,
    }
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

.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: $text-secondary;

  h3 {
    margin: 16px 0 8px;
    font-size: 20px;
    color: $text-primary;
  }

  p {
    margin: 0;
    font-size: 14px;
  }
}

.chat-message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-assistant {
  align-self: flex-start;
}

.message-avatar {
  flex-shrink: 0;
}

.loading-dots {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 4px 0;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: $text-secondary;
    animation: dot-bounce 1.4s ease-in-out infinite;

    &:nth-child(1) { animation-delay: 0s; }
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid $border-lighter;
  background: #fff;
  align-items: flex-end;

  .el-textarea {
    flex: 1;
  }

  .el-button {
    height: 56px;
    padding: 0 24px;
  }
}
</style>

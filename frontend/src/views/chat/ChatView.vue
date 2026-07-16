<template>
  <div class="chat-layout">
    <!-- ── Sidebar: Session List ── -->
    <div class="chat-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <h3>会话历史</h3>
        <el-button type="primary" size="small" :icon="Plus" @click="handleNewSession">
          新对话
        </el-button>
      </div>

      <div class="sidebar-list" v-loading="loadingSessions">
        <div v-if="sessions.length === 0 && !loadingSessions" class="sidebar-empty">
          <el-icon :size="32" color="#c0c4cc"><Message /></el-icon>
          <p>暂无对话记录</p>
          <p class="sidebar-empty-hint">点击上方「新对话」开始</p>
        </div>

        <div
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: session.id === activeSessionId }]"
          @click="switchSession(session.id)"
        >
          <!-- Inline rename input -->
          <template v-if="renamingId === session.id">
            <el-input
              v-model="renameText"
              size="small"
              ref="renameInputRef"
              @keydown.enter.prevent="confirmRename(session.id)"
              @blur="confirmRename(session.id)"
              @click.stop
              clearable
            />
          </template>

          <!-- Normal session display -->
          <template v-else>
            <div class="session-info">
              <div class="session-title" :title="session.title || '新对话'">
                {{ session.title || '新对话' }}
              </div>
              <div class="session-meta">
                {{ session.message_count }} 条消息
                <template v-if="session.updated_at">
                  · {{ formatTime(session.updated_at) }}
                </template>
              </div>
            </div>
            <div class="session-actions" @click.stop>
              <el-tooltip content="重命名" :show-after="300">
                <el-button text size="small" :icon="Edit" @click="startRename(session)" />
              </el-tooltip>
              <el-tooltip content="删除" :show-after="300">
                <el-button
                  text
                  size="small"
                  type="danger"
                  :icon="Delete"
                  @click="handleDeleteClick(session.id, session.title)"
                />
              </el-tooltip>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ── Main Chat Area ── -->
    <div class="chat-main">
      <!-- Collapse toggle for sidebar (mobile) -->
      <div class="chat-sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
      </div>

      <!-- Messages -->
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
                :style="msg.role === 'user' ? { background: '#dcdfe6', color: '#606266' } : { background: '#409EFF' }"
              />
            </div>
            <div class="message-content">
              <div :class="msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'">
                <div v-if="msg.loading" class="loading-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
                <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 推荐资源 -->
      <div v-if="recommendations.length > 0" class="recommendation-section">
        <div class="recommendation-header">
          <el-icon><Reading /></el-icon>
          <span>推荐学习资料</span>
        </div>
        <div class="recommendation-list">
          <div
            v-for="(rec, idx) in recommendations"
            :key="idx"
            class="recommendation-card"
          >
            <div class="rec-type-tag">
              <el-tag
                :type="rec.resource_type === 'ppt_slide' ? 'warning' : rec.resource_type === 'pdf_page' ? 'primary' : rec.resource_type === 'markdown_section' ? 'success' : 'success'"
                size="small"
                effect="plain"
              >
                {{ rec.resource_type === 'ppt_slide' ? '课件' : rec.resource_type === 'pdf_page' ? 'PDF' : rec.resource_type === 'markdown_section' ? '文档' : '章节' }}
              </el-tag>
            </div>
            <div class="rec-title">{{ rec.title }}</div>
            <div class="rec-desc">{{ rec.description }}</div>
            <div v-if="rec.source_info?.source" class="rec-source">
              来源：{{ rec.source_info.source }}
              <template v-if="rec.source_info.page"> · 第 {{ rec.source_info.page }} 页</template>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
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
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import {
  ChatLineSquare, UserFilled, Promotion, Reading,
  Plus, Edit, Delete, Message, Fold, Expand,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Marked } from 'marked'
import {
  createSession,
  getSessions,
  getMessages,
  deleteSession,
  updateSession,
  type SessionData,
  type MessageData,
} from '@/api/chat'
import { createChatSSE, type RecommendationItem } from '@/utils/sse'

const marked = new Marked({
  breaks: true,
  gfm: true,
})

// ── Types ──

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  loading?: boolean
}

// ── Chat State ──

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const activeSessionId = ref<number | null>(null)
const recommendations = ref<RecommendationItem[]>([])
let currentSSE: { abort: () => void } | null = null

// ── Sidebar State ──

const sessions = ref<SessionData[]>([])
const loadingSessions = ref(false)
const sidebarCollapsed = ref(false)
const renamingId = ref<number | null>(null)
const renameText = ref('')
const renameInputRef = ref<HTMLInputElement | null>(null)

// ── Markdown ──

function renderMarkdown(text: string): string {
  if (!text) return ''
  try {
    return marked.parse(text) as string
  } catch {
    return text
  }
}

// ── Time formatting ──

function formatTime(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (diffDays === 1) {
      return '昨天'
    } else if (diffDays < 7) {
      return `${diffDays} 天前`
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    }
  } catch {
    return dateStr
  }
}

// ── Session Management ──

async function loadSessions() {
  loadingSessions.value = true
  try {
    sessions.value = await getSessions()
  } catch {
    // Silently fail — sessions will be empty
  } finally {
    loadingSessions.value = false
  }
}

async function handleNewSession() {
  try {
    // Abort any active SSE
    currentSSE?.abort()

    const session = await createSession()
    activeSessionId.value = session.id
    messages.value = []
    recommendations.value = []
    sending.value = false

    // Show welcome message
    messages.value.push({
      role: 'assistant',
      content: '你好！我是课程教学助手，可以帮你解答学习中的问题。请问有什么可以帮助你的？',
    })

    // Refresh session list and scroll to bottom
    await loadSessions()
    scrollToBottom()
  } catch (err: any) {
    ElMessage.error('创建对话失败：' + (err.message || '未知错误'))
  }
}

async function switchSession(sessionId: number) {
  if (sessionId === activeSessionId.value) return

  // Abort any active SSE
  currentSSE?.abort()
  sending.value = false

  activeSessionId.value = sessionId
  messages.value = []
  recommendations.value = []

  try {
    const history = await getMessages(sessionId)
    if (history.length > 0) {
      for (const msg of history) {
        messages.value.push({
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
        })
      }
    } else {
      messages.value.push({
        role: 'assistant',
        content: '你好！我是课程教学助手，可以帮你解答学习中的问题。请问有什么可以帮助你的？',
      })
    }
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '加载消息失败，请稍后重试。',
    })
  }

  scrollToBottom()
}

// ── Rename ──

function startRename(session: SessionData) {
  renamingId.value = session.id
  renameText.value = session.title || ''
  // Focus input on next tick
  nextTick(() => {
    const input = document.querySelector('.session-item.active .el-input__inner') as HTMLInputElement
    input?.focus()
    input?.select()
  })
}

async function confirmRename(sessionId: number) {
  const newTitle = renameText.value.trim()
  if (renamingId.value !== sessionId) return

  renamingId.value = null

  if (!newTitle) return

  try {
    const updated = await updateSession(sessionId, { title: newTitle })
    // Update in local list
    const idx = sessions.value.findIndex(s => s.id === sessionId)
    if (idx !== -1) {
      sessions.value[idx] = updated
    }
    ElMessage.success('重命名成功')
  } catch {
    ElMessage.error('重命名失败')
  }
}

// ── Delete ──

async function handleDeleteClick(sessionId: number, sessionTitle?: string) {
  try {
    await ElMessageBox.confirm(
      `确定删除对话「${sessionTitle || '新对话'}」？删除后不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await handleDelete(sessionId)
  } catch {
    // User cancelled — do nothing
  }
}

async function handleDelete(sessionId: number) {
  try {
    await deleteSession(sessionId)

    // Remove from local list immediately for instant feedback
    const idx = sessions.value.findIndex(s => s.id === sessionId)
    if (idx !== -1) {
      sessions.value.splice(idx, 1)
    }

    // If we deleted the active session, create a new one
    if (activeSessionId.value === sessionId) {
      activeSessionId.value = null
      messages.value = []
      recommendations.value = []
      sending.value = false
      await handleNewSession()
    }

    ElMessage.success('对话已删除')
  } catch (err: any) {
    ElMessage.error('删除失败：' + (err.message || '未知错误'))
    // Refresh list to restore state if deletion actually failed on backend
    await loadSessions()
  }
}

// ── Setup ──

onMounted(async () => {
  await loadSessions()

  // Auto-create or resume last session
  if (sessions.value.length > 0) {
    await switchSession(sessions.value[0].id)
  } else {
    await handleNewSession()
  }
})

onUnmounted(() => {
  currentSSE?.abort()
})

// ── Sending Messages ──

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || sending.value || !activeSessionId.value) return

  // Add user message
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  // Add loading assistant message
  const assistantIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', loading: true })
  sending.value = true
  scrollToBottom()

  try {
    let fullContent = ''
    recommendations.value = []

    currentSSE = createChatSSE(
      `/chat/sessions/${activeSessionId.value}/message`,
      { content: text },
      // onToken
      (token: string) => {
        fullContent += token
        messages.value[assistantIndex] = {
          role: 'assistant',
          content: fullContent,
        }
        scrollToBottom()
      },
      // onDone
      () => {
        messages.value[assistantIndex] = {
          role: 'assistant',
          content: fullContent,
        }
        sending.value = false
        currentSSE = null
        // Refresh session list to update title/message_count
        loadSessions()
        scrollToBottom()
      },
      // onError
      (error: string) => {
        console.error('SSE error:', error)
        if (!fullContent) {
          messages.value[assistantIndex] = {
            role: 'assistant',
            content: '抱歉，我遇到了一个错误，请稍后重试。',
          }
        }
        sending.value = false
        currentSSE = null
        scrollToBottom()
      },
      // onRecommendation
      (recs: RecommendationItem[]) => {
        recommendations.value = recs
        scrollToBottom()
      },
    )
  } catch (err: any) {
    messages.value[assistantIndex] = {
      role: 'assistant',
      content: '抱歉，我遇到了一个错误，请稍后重试。',
    }
    sending.value = false
    scrollToBottom()
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

// ── Layout ──

.chat-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

// ── Sidebar ──

.chat-sidebar {
  width: 280px;
  min-width: 280px;
  border-right: 1px solid $border-lighter;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  transition: width $transition-normal, min-width $transition-normal;

  &.collapsed {
    width: 0;
    min-width: 0;
    overflow: hidden;
    border-right: none;
  }
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid $border-lighter;
  flex-shrink: 0;

  h3 {
    margin: 0;
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-primary;
    white-space: nowrap;
  }
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  color: $text-secondary;

  p {
    margin: 8px 0 0;
    font-size: $font-size-sm;
  }

  .sidebar-empty-hint {
    font-size: $font-size-xs;
    color: $text-placeholder;
  }
}

// ── Session Item ──

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: $border-radius-medium;
  cursor: pointer;
  transition: background $transition-fast;
  margin-bottom: 2px;
  gap: 8px;

  &:hover {
    background: #f0f0f0;

    .session-actions {
      opacity: 1;
    }
  }

  &.active {
    background: #e6f0ff;

    .session-title {
      color: $primary-color;
      font-weight: 600;
    }
  }
}

.session-info {
  flex: 1;
  min-width: 0; // enable text-overflow
}

.session-title {
  font-size: $font-size-sm;
  color: $text-primary;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  font-size: $font-size-xs;
  color: $text-secondary;
  margin-top: 2px;
}

.session-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity $transition-fast;
  flex-shrink: 0;

  .el-button {
    font-size: 14px;
  }
}

// Ensure actions are visible on the active item
.session-item.active .session-actions {
  opacity: 1;
}

// ── Chat Main Area ──

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  position: relative;
}

.chat-sidebar-toggle {
  display: flex;
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #fff;
  border: 1px solid $border-lighter;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  color: $text-secondary;
  transition: all $transition-fast;

  &:hover {
    color: $primary-color;
    border-color: $primary-color;
  }
}

// ── Messages Area ──

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

// ── Chat Bubbles ──

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

.chat-bubble-user {
  background: $chat-bubble-user-bg;
  color: $chat-bubble-user-color;
  padding: 10px 14px;
  border-radius: 12px 4px 12px 12px;
  line-height: 1.6;
  font-size: $font-size-base;
}

.chat-bubble-assistant {
  background: $chat-bubble-assistant-bg;
  color: $chat-bubble-assistant-color;
  padding: 10px 14px;
  border-radius: 4px 12px 12px 12px;
  line-height: 1.6;
  font-size: $font-size-base;
}

// ── Markdown ──

.markdown-body {
  line-height: 1.7;
  word-break: break-word;

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

  :deep(p) {
    margin: 8px 0;
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

// ── Loading dots ──

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

// ── Input Area ──

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

// ── Recommendation Section ──

.recommendation-section {
  border-top: 1px solid $border-lighter;
  padding: 16px 20px;
  max-height: 260px;
  overflow-y: auto;
}

.recommendation-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: $font-size-sm;
  color: $text-secondary;
  margin-bottom: 12px;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recommendation-card {
  padding: 12px;
  border: 1px solid $border-light;
  border-radius: $border-radius-medium;
  transition: border-color $transition-fast;

  &:hover {
    border-color: $primary-color;
  }

  .rec-type-tag {
    margin-bottom: 4px;
  }

  .rec-title {
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-primary;
    margin: 4px 0;
  }

  .rec-desc {
    font-size: $font-size-sm;
    color: $text-regular;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .rec-source {
    font-size: $font-size-xs;
    color: $text-secondary;
    margin-top: 4px;
  }
}
</style>

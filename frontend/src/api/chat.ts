import request from './request'

export interface SessionData {
  id: number
  title: string
  message_count: number
  created_at: string
  updated_at?: string
}

export interface MessageData {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

/**
 * 创建新对话
 */
export function createSession(title?: string, chapterId?: number): Promise<SessionData> {
  return request.post('/chat/sessions', { title: title || '新对话', chapter_id: chapterId }).then(res => res.data)
}

/**
 * 获取对话列表
 */
export function getSessions(): Promise<SessionData[]> {
  return request.get('/chat/sessions').then(res => res.data)
}

/**
 * 获取对话历史
 */
export function getMessages(sessionId: number): Promise<MessageData[]> {
  return request.get(`/chat/sessions/${sessionId}/messages`).then(res => res.data)
}

/**
 * 更新对话（重命名）
 */
export function updateSession(sessionId: number, data: { title?: string }): Promise<SessionData> {
  return request.put(`/chat/sessions/${sessionId}`, data).then(res => res.data)
}

/**
 * 删除对话
 */
export function deleteSession(sessionId: number): Promise<{ message: string }> {
  return request.delete(`/chat/sessions/${sessionId}`).then(res => res.data)
}

import request from './request'

export interface DashboardStats {
  total_students: number
  total_chapters: number
  total_documents: number
  total_assessments: number
  recent_activity: ActivityItem[]
}

export interface ActivityItem {
  id: number
  user_id: number
  username: string
  action: string
  module: string
  detail: string
  created_at: string
}

export interface LlmConfig {
  model_name: string
  temperature: number
  max_tokens: number
  base_url: string
  provider: string
}

export interface LogQuery {
  level?: string
  module?: string
  page?: number
  page_size?: number
  start_time?: string
  end_time?: string
}

export interface LogItem {
  id: number
  level: string
  module: string
  action: string
  message: string
  username: string
  created_at: string
}

export interface LogResult {
  items: LogItem[]
  total: number
}

/**
 * 获取仪表盘统计数据
 */
export function getDashboardStats(): Promise<DashboardStats> {
  return request.get('/system/dashboard').then(res => res.data)
}

/**
 * 获取 LLM 配置
 */
export function getLlmConfig(): Promise<LlmConfig> {
  return request.get('/system/llm-config').then(res => res.data)
}

/**
 * 更新 LLM 配置
 */
export function updateLlmConfig(data: Partial<LlmConfig>): Promise<LlmConfig> {
  return request.put('/system/llm-config', data).then(res => res.data)
}

/**
 * 测试 LLM 连接（API Key 由系统环境变量提供）
 */
export function testLlmConnection(data?: Partial<LlmConfig>): Promise<{ success: boolean; message: string }> {
  return request.post('/system/llm-config/test', data || {}).then(res => res.data)
}

/**
 * 获取系统日志
 */
export function getLogs(params: LogQuery): Promise<LogResult> {
  return request.get('/system/logs', { params }).then(res => res.data)
}

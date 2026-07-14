import request from './request'

export interface Agent {
  id: number
  name: string
  description: string
  model_name: string
  system_prompt: string
  temperature: number
  max_tokens: number
  status: 'active' | 'inactive'
  created_at: string
  updated_at: string
}

export interface AgentCreate {
  name: string
  description?: string
  model_name?: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number
  status?: 'active' | 'inactive'
}

export interface AgentUpdate {
  name?: string
  description?: string
  model_name?: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number
  status?: 'active' | 'inactive'
}

export interface AgentInvokeData {
  message: string
  conversation_id?: string
}

export interface AgentInvokeResponse {
  response: string
  conversation_id: string
  tokens_used: number
}

/**
 * 获取智能体列表
 */
export function getAgents(params?: { status?: string }): Promise<Agent[]> {
  return request.get('/agents', { params }).then(res => res.data)
}

/**
 * 获取智能体详情
 */
export function getAgent(id: number): Promise<Agent> {
  return request.get(`/agents/${id}`).then(res => res.data)
}

/**
 * 创建智能体
 */
export function createAgent(data: AgentCreate): Promise<Agent> {
  return request.post('/agents', data).then(res => res.data)
}

/**
 * 更新智能体
 */
export function updateAgent(id: number, data: AgentUpdate): Promise<Agent> {
  return request.put(`/agents/${id}`, data).then(res => res.data)
}

/**
 * 删除智能体
 */
export function deleteAgent(id: number): Promise<{ message: string }> {
  return request.delete(`/agents/${id}`).then(res => res.data)
}

/**
 * 调用智能体
 */
export function invokeAgent(id: number, data: AgentInvokeData): Promise<AgentInvokeResponse> {
  return request.post(`/agents/${id}/invoke`, data).then(res => res.data)
}

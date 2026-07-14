import request from './request'

export interface Chapter {
  id: number
  title: string
  description: string
  order_index: number
  is_active: boolean
  created_at: string
}

export interface ChapterListDisplay {
  id: number
  title: string
  description: string
  order_index: number
  is_active: boolean
  document_count: number
  created_at: string
}

export interface ChapterCreate {
  title: string
  description?: string
  order_index?: number
}

export interface ChapterUpdate {
  title?: string
  description?: string
  order_index?: number
  is_active?: boolean
}

export interface ReorderData {
  chapter_ids: number[]
}

export interface ChapterProgress {
  chapter_id: number
  title: string
  order_index: number
  status: string
  best_score: number | null
}

/**
 * 获取章节列表
 */
export function getChapters(params?: { status?: string }): Promise<Chapter[]> {
  return request.get('/chapters').then(res => res.data)
}

/**
 * 获取章节详情
 */
export function getChapter(id: number): Promise<Chapter> {
  return request.get(`/chapters/${id}`).then(res => res.data)
}

/**
 * 创建章节
 */
export function createChapter(data: ChapterCreate): Promise<Chapter> {
  return request.post('/chapters', data).then(res => res.data)
}

/**
 * 更新章节
 */
export function updateChapter(id: number, data: ChapterUpdate): Promise<Chapter> {
  return request.put(`/chapters/${id}`, data).then(res => res.data)
}

/**
 * 删除章节
 */
export function deleteChapter(id: number): Promise<{ message: string }> {
  return request.delete(`/chapters/${id}`).then(res => res.data)
}

/**
 * 重新排序章节
 */
export function reorderChapters(data: ReorderData[]): Promise<{ message: string }> {
  return request.put('/chapters/reorder', { items: data }).then(res => res.data)
}

/**
 * 获取学习进度
 */
export function getProgress(): Promise<ChapterProgress[]> {
  return request.get('/chapters/progress').then(res => res.data)
}

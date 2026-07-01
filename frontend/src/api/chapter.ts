import request, { type ApiResponse } from './request'

export interface Chapter {
  id: number
  title: string
  description: string
  order: number
  status: 'draft' | 'published' | 'archived'
  document_count: number
  created_at: string
  updated_at: string
}

export interface ChapterCreate {
  title: string
  description?: string
  order?: number
  status?: 'draft' | 'published' | 'archived'
}

export interface ChapterUpdate {
  title?: string
  description?: string
  order?: number
  status?: 'draft' | 'published' | 'archived'
}

export interface ReorderData {
  id: number
  order: number
}

export interface ChapterProgress {
  chapter_id: number
  chapter_title: string
  total_documents: number
  completed_documents: number
  progress_percent: number
}

/**
 * 获取章节列表
 */
export function getChapters(params?: { status?: string }): Promise<ApiResponse<Chapter[]>> {
  return request.get('/chapters', { params }).then(res => res.data)
}

/**
 * 获取章节详情
 */
export function getChapter(id: number): Promise<ApiResponse<Chapter>> {
  return request.get(`/chapters/${id}`).then(res => res.data)
}

/**
 * 创建章节
 */
export function createChapter(data: ChapterCreate): Promise<ApiResponse<Chapter>> {
  return request.post('/chapters', data).then(res => res.data)
}

/**
 * 更新章节
 */
export function updateChapter(id: number, data: ChapterUpdate): Promise<ApiResponse<Chapter>> {
  return request.put(`/chapters/${id}`, data).then(res => res.data)
}

/**
 * 删除章节
 */
export function deleteChapter(id: number): Promise<ApiResponse<null>> {
  return request.delete(`/chapters/${id}`).then(res => res.data)
}

/**
 * 重新排序章节
 */
export function reorderChapters(data: ReorderData[]): Promise<ApiResponse<null>> {
  return request.put('/chapters/reorder', { items: data }).then(res => res.data)
}

/**
 * 获取学习进度
 */
export function getProgress(): Promise<ApiResponse<ChapterProgress[]>> {
  return request.get('/chapters/progress').then(res => res.data)
}

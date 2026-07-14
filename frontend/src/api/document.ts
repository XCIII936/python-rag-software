import request from './request'

export interface DocumentData {
  id: number
  chapter_id: number | null
  chapter_title: string | null
  title: string
  file_type: string
  file_size: number | null
  page_count: number | null
  status: string
  error_message: string | null
  chunk_count: number | null
  created_at: string
}

/**
 * 获取文档列表
 */
export function getDocuments(chapterId?: number): Promise<DocumentData[]> {
  const params = chapterId ? { chapter_id: chapterId } : {}
  return request.get('/documents', { params }).then(res => res.data)
}

/**
 * 获取单个文档
 */
export function getDocument(id: number): Promise<DocumentData> {
  return request.get(`/documents/${id}`).then(res => res.data)
}

/**
 * 上传文档
 */
export function uploadDocument(file: File, chapterId?: number): Promise<DocumentData> {
  const form = new FormData()
  form.append('file', file)
  if (chapterId !== undefined && chapterId !== null) {
    form.append('chapter_id', String(chapterId))
  }
  return request.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(res => res.data)
}

/**
 * 删除文档
 */
export function deleteDocument(id: number): Promise<{ message: string }> {
  return request.delete(`/documents/${id}`).then(res => res.data)
}

/**
 * 重新处理文档
 */
export function reprocessDocument(id: number): Promise<{ message: string }> {
  return request.post(`/documents/${id}/reprocess`).then(res => res.data)
}

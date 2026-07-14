import request from './request'

export interface QuestionData {
  id: number
  question_index: number
  question_type: 'choice' | 'true_false' | 'short_answer'
  question_content: string
  options: string | null  // JSON string
}

export interface StartResult {
  record_id: number
  total_questions: number
}

export interface AnswerResult {
  status: 'continue' | 'completed'
  next_question?: QuestionData
  answered: number
  total: number
  message?: string
}

export interface SubmitResult {
  record_id: number
  total_score: number
  correct_answers: number
  total_questions: number
  report_id: number | null
}

export interface ReportData {
  id: number
  record_id: number
  overall_score: number
  dimension_scores: any
  summary_comment: string | null
  review_suggestions: any
  strengths: any
  weaknesses: any
}

/**
 * 获取章节考核配置
 */
export function getAssessmentConfig(chapterId: number): Promise<AssessmentConfigData> {
  return request.get(`/assessment/configs/chapter/${chapterId}`).then(res => res.data)
}

/**
 * 保存章节考核配置
 */
export function saveAssessmentConfig(data: {
  chapter_id: number
  knowledge_points: string[]
  question_types: Record<string, number>
  evaluation_dimensions: { name: string; weight: number }[]
  passing_score?: number
}): Promise<AssessmentConfigData> {
  return request.post('/assessment/configs', data).then(res => res.data)
}

export interface AssessmentConfigData {
  id: number
  chapter_id: number
  knowledge_points: string[] | string
  question_types: Record<string, number> | string
  evaluation_dimensions: { name: string; weight: number }[] | string
  total_questions?: number
  passing_score?: number
}

/**
 * 开始测评
 */
export function startAssessment(chapterId: number): Promise<StartResult> {
  return request.post(`/assessment/start/${chapterId}`).then(res => res.data)
}

/**
 * 获取当前题目
 */
export function getCurrentQuestion(recordId: number): Promise<QuestionData | { message: string; status: string }> {
  return request.get(`/assessment/${recordId}/question`).then(res => res.data)
}

/**
 * 提交答案
 */
export function submitAnswer(recordId: number, questionId: number, answer: string): Promise<AnswerResult> {
  return request.post(`/assessment/${recordId}/answer`, { question_id: questionId, answer }).then(res => res.data)
}

/**
 * 交卷
 */
export function submitAssessment(recordId: number): Promise<SubmitResult> {
  return request.post(`/assessment/${recordId}/submit`).then(res => res.data)
}

/**
 * 获取测评报告
 */
export function getReport(recordId: number): Promise<ReportData> {
  return request.get(`/assessment/${recordId}/report`).then(res => res.data)
}

import { getToken } from './auth'

interface SSEHandlers {
  onToken?: (token: string) => void
  onContext?: (context: string) => void
  onRecommendation?: (recommendation: string) => void
  onError?: (error: string) => void
  onDone?: () => void
}

interface SSEResult {
  abort: () => void
}

/**
 * 创建 SSE 连接，使用 fetch + ReadableStream 解析 SSE 事件
 * @param url SSE 端点 URL（不含 baseURL）
 * @param body POST 请求体
 * @param handlers 事件处理器
 * @returns 包含 abort 方法的对象
 */
export function createSSEConnection(
  url: string,
  body: Record<string, any>,
  handlers: SSEHandlers
): SSEResult {
  const controller = new AbortController()

  const fetchUrl = `/api/v1${url}`

  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  fetch(fetchUrl, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text().catch(() => '未知错误')
        handlers.onError?.(`HTTP ${response.status}: ${errorText}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        handlers.onError?.('响应流不可读')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            // 处理缓冲区剩余内容
            processBuffer(buffer, handlers)
            handlers.onDone?.()
            break
          }

          buffer += decoder.decode(value, { stream: true })

          // 按行分割处理 SSE 数据
          const lines = buffer.split('\n')
          // 保留最后一个不完整的行
          buffer = lines.pop() || ''

          for (const line of lines) {
            processSSELine(line.trim(), handlers)
          }
        }
      } catch (err: any) {
        if (err.name === 'AbortError') {
          // 用户主动中止，不做处理
          return
        }
        handlers.onError?.(err.message || '流读取错误')
      }
    })
    .catch((err: any) => {
      if (err.name === 'AbortError') return
      handlers.onError?.(err.message || '请求失败')
    })

  return {
    abort: () => {
      controller.abort()
    },
  }
}

/**
 * 处理单个 SSE 行
 */
function processSSELine(line: string, handlers: SSEHandlers): void {
  if (!line || line.startsWith(':')) {
    // 注释行或空行，跳过
    return
  }

  // SSE 格式: "event: data\n" 或 "data: {}\n"
  if (line.startsWith('event:')) {
    // 事件类型行，不在单行处理
    return
  }

  if (line.startsWith('data:')) {
    const dataStr = line.slice(5).trim()
    if (!dataStr) return

    // SSE 结束标记
    if (dataStr === '[DONE]') {
      handlers.onDone?.()
      return
    }

    try {
      const data = JSON.parse(dataStr)

      if (data.type === 'token' || data.token) {
        handlers.onToken?.(data.token || data.content || '')
      } else if (data.type === 'context') {
        handlers.onContext?.(data.content || data.data || '')
      } else if (data.type === 'recommendation') {
        handlers.onRecommendation?.(data.content || data.data || '')
      } else if (data.type === 'error' || data.error) {
        handlers.onError?.(data.message || data.error || '未知错误')
      } else if (data.type === 'done') {
        handlers.onDone?.()
      } else if (data.content) {
        // 默认当 token 处理
        handlers.onToken?.(data.content)
      }
    } catch {
      // 非 JSON 数据，当纯文本 token 处理
      handlers.onToken?.(dataStr)
    }
    return
  }

  // 纯数据行（没有 data: 前缀），尝试解析 JSON
  try {
    const data = JSON.parse(line)
    if (data.token || data.content) {
      handlers.onToken?.(data.token || data.content)
    }
  } catch {
    // 忽略无法解析的行
  }
}

/**
 * 处理缓冲区中剩余的数据
 */
function processBuffer(buffer: string, handlers: SSEHandlers): void {
  if (!buffer.trim()) return
  const lines = buffer.split('\n')
  for (const line of lines) {
    processSSELine(line.trim(), handlers)
  }
}

/**
 * 创建流式聊天 SSE 连接（简化版，适用于对话场景）
 */
export function createChatSSE(
  url: string,
  body: Record<string, any>,
  onToken: (token: string) => void,
  onDone: () => void,
  onError?: (error: string) => void
): SSEResult {
  return createSSEConnection(url, body, {
    onToken,
    onDone,
    onError,
  })
}

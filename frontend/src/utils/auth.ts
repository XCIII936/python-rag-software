const TOKEN_KEY = 'course_teaching_agent_token'

/**
 * 获取存储的 token
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 存储 token
 */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 移除 token
 */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * 检查 token 是否过期（如果 token 是 JWT 格式）
 * 简单检查 payload 中的 exp 字段
 */
export function isTokenExpired(token: string): boolean {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return false
    const payload = JSON.parse(atob(parts[1]))
    if (payload.exp) {
      const now = Math.floor(Date.now() / 1000)
      return payload.exp < now
    }
    return false
  } catch {
    return false
  }
}

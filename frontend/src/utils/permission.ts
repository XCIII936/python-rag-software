import { useAuthStore } from '@/stores/auth'

/**
 * 检查当前用户是否具有指定角色
 * @param roles 允许的角色列表
 * @returns 是否具有权限
 */
export function hasRole(...roles: string[]): boolean {
  const authStore = useAuthStore()
  if (!authStore.user) return false
  return roles.includes(authStore.user.role)
}

/**
 * 检查当前用户是否为教师
 */
export function isTeacher(): boolean {
  return hasRole('teacher')
}

/**
 * 检查当前用户是否为管理员
 */
export function isAdmin(): boolean {
  return hasRole('admin') || hasRole('teacher')
}

/**
 * 检查当前用户是否为普通学生
 */
export function isStudent(): boolean {
  return hasRole('student')
}

/**
 * 检查当前用户是否已登录
 */
export function isAuthenticated(): boolean {
  const authStore = useAuthStore()
  return !!authStore.token && !!authStore.user
}

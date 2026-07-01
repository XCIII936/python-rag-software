import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  login as apiLogin,
  register as apiRegister,
  getProfile as apiGetProfile,
  updateProfile as apiUpdateProfile,
  type LoginData,
  type RegisterData,
  type UserProfile,
  type UpdateProfileData,
  type ChangePasswordData,
} from '@/api/auth'
import { setToken, removeToken, getToken } from '@/utils/auth'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', () => {
  // ========== State ==========
  const token = ref<string | null>(getToken())
  const user = ref<UserProfile | null>(null)
  const loading = ref(false)

  // ========== Getters ==========
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')
  const username = computed(() => user.value?.username || '')
  const userRole = computed(() => user.value?.role || '')

  // ========== Actions ==========

  /**
   * 登录
   */
  async function login(loginData: LoginData): Promise<void> {
    loading.value = true
    try {
      const res = await apiLogin(loginData)
      const { token: newToken, user: userData } = res.data
      token.value = newToken
      user.value = userData
      setToken(newToken)
      ElMessage.success('登录成功')
    } catch (err: any) {
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 注册
   */
  async function register(registerData: RegisterData): Promise<void> {
    loading.value = true
    try {
      const res = await apiRegister(registerData)
      const { token: newToken, user: userData } = res.data
      token.value = newToken
      user.value = userData
      setToken(newToken)
      ElMessage.success('注册成功')
    } catch (err: any) {
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 退出登录
   */
  function logout(): void {
    token.value = null
    user.value = null
    removeToken()
  }

  /**
   * 获取用户信息
   */
  async function fetchProfile(): Promise<void> {
    if (!token.value) return
    try {
      const res = await apiGetProfile()
      user.value = res.data
    } catch {
      // 如果获取失败但 token 存在，可能是 token 过期
      // 由请求拦截器处理 401 跳转
    }
  }

  /**
   * 更新个人信息
   */
  async function updateProfileData(data: UpdateProfileData): Promise<void> {
    try {
      const res = await apiUpdateProfile(data)
      user.value = res.data
      ElMessage.success('个人信息更新成功')
    } catch (err: any) {
      throw err
    }
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    isTeacher,
    isStudent,
    username,
    userRole,
    login,
    register,
    logout,
    fetchProfile,
    updateProfileData,
  }
})

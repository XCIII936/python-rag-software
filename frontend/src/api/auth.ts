import request from './request'

export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  password: string
  email: string
  role: 'student' | 'teacher'
}

export interface UserProfile {
  id: number
  username: string
  email: string
  role: 'student' | 'teacher'
  avatar: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginResult {
  access_token: string
  token_type: string
  user: UserProfile
}

export interface UpdateProfileData {
  email?: string
  avatar?: string
}

export interface ChangePasswordData {
  old_password: string
  new_password: string
}

/**
 * 登录
 */
export function login(data: LoginData): Promise<LoginResult> {
  return request.post('/auth/login', data).then(res => res.data)
}

/**
 * 注册
 */
export function register(data: RegisterData): Promise<LoginResult> {
  return request.post('/auth/register', data).then(res => res.data)
}

/**
 * 获取当前用户信息
 */
export function getProfile(): Promise<UserProfile> {
  return request.get('/auth/profile').then(res => res.data)
}

/**
 * 更新个人信息
 */
export function updateProfile(data: UpdateProfileData): Promise<UserProfile> {
  return request.put('/auth/profile', data).then(res => res.data)
}

/**
 * 修改密码
 */
export function changePassword(data: ChangePasswordData): Promise<{ message: string }> {
  return request.put('/auth/password', data).then(res => res.data)
}

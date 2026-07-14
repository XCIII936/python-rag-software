import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { getToken } from '@/utils/auth'

const routes: RouteRecordRaw[] = [
  // ========== 认证页面 (AuthLayout) ==========
  {
    path: '/auth',
    component: () => import('@/layouts/AuthLayout.vue'),
    redirect: '/auth/login',
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: { title: '登录', noAuth: true },
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/auth/RegisterView.vue'),
        meta: { title: '注册', noAuth: true },
      },
    ],
  },

  // ========== 主页面 (DefaultLayout) ==========
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '仪表盘', requiresAuth: true },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: { title: '个人信息', requiresAuth: true },
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/ChatView.vue'),
        meta: { title: '学习助手', requiresAuth: true },
      },
      // 章节相关
      {
        path: 'chapters',
        name: 'Chapters',
        component: () => import('@/views/chapter/ChapterListView.vue'),
        meta: { title: '章节列表', requiresAuth: true },
      },
      {
        path: 'chapters/:id/learn',
        name: 'ChapterLearn',
        component: () => import('@/views/chapter/ChapterLearnView.vue'),
        meta: { title: '章节学习', requiresAuth: true },
      },
      {
        path: 'chapters/:id/assessment',
        name: 'ChapterAssessment',
        component: () => import('@/views/assessment/AssessmentView.vue'),
        meta: { title: '章节测评', requiresAuth: true },
      },
      {
        path: 'assessment/:recordId/results',
        name: 'AssessmentResults',
        component: () => import('@/views/assessment/AssessmentResultsView.vue'),
        meta: { title: '测评结果', requiresAuth: true },
      },
      // 管理员 - 章节管理
      {
        path: 'admin/chapters',
        name: 'AdminChapters',
        component: () => import('@/views/chapter/ChapterManageView.vue'),
        meta: { title: '章节管理', requiresAuth: true, role: 'teacher' },
      },
      {
        path: 'admin/chapters/:id/assessment-config',
        name: 'AssessmentConfig',
        component: () => import('@/views/assessment/AssessmentConfigView.vue'),
        meta: { title: '考核配置', requiresAuth: true, role: 'teacher' },
      },
      // 知识库
      {
        path: 'knowledge-base',
        name: 'KnowledgeBase',
        component: () => import('@/views/document/KnowledgeBaseView.vue'),
        meta: { title: '知识库', requiresAuth: true },
      },
      // 系统管理 (教师)
      {
        path: 'system/llm-config',
        name: 'LlmConfig',
        component: () => import('@/views/system/LlmConfigView.vue'),
        meta: { title: 'LLM 配置', requiresAuth: true, role: 'teacher' },
      },
      {
        path: 'system/logs',
        name: 'SystemLogs',
        component: () => import('@/views/system/SystemLogsView.vue'),
        meta: { title: '系统日志', requiresAuth: true, role: 'teacher' },
      },
    ],
  },

  // ========== 404 ==========
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '404 - 页面未找到' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ========== 导航守卫 ==========
router.beforeEach((to, from, next) => {
  document.title = (to.meta.title as string) ? `${to.meta.title} - 课程教学助手` : '课程教学助手'

  const token = getToken()

  // 无需认证的页面直接通过
  if (to.meta.noAuth) {
    // 如果已登录且访问登录/注册页，重定向到仪表盘
    if (token && (to.name === 'Login' || to.name === 'Register')) {
      next({ name: 'Dashboard' })
    } else {
      next()
    }
    return
  }

  // 需要认证但没有 token
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // 角色权限检查
  const requiredRole = to.meta.role as string | undefined
  if (requiredRole) {
    const userRole = localStorage.getItem('user_role') || ''
    if (userRole !== requiredRole) {
      next({ name: 'Dashboard' })
      return
    }
  }

  next()
})

export default router

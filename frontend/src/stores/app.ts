import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getDashboardStats as apiGetDashboardStats,
  getLlmConfig as apiGetLlmConfig,
  updateLlmConfig as apiUpdateLlmConfig,
  type DashboardStats,
  type LlmConfig,
} from '@/api/system'
import { ElMessage } from 'element-plus'

export const useAppStore = defineStore('app', () => {
  // ========== State ==========
  const sidebarCollapsed = ref(false)
  const llmConfig = ref<LlmConfig | null>(null)
  const systemStats = ref<DashboardStats | null>(null)
  const loading = ref(false)

  // ========== Actions ==========

  /**
   * 切换侧边栏折叠状态
   */
  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /**
   * 设置侧边栏折叠状态
   */
  function setSidebarCollapsed(collapsed: boolean): void {
    sidebarCollapsed.value = collapsed
  }

  /**
   * 获取仪表盘统计数据
   */
  async function fetchDashboardStats(): Promise<void> {
    loading.value = true
    try {
      const res = await apiGetDashboardStats()
      systemStats.value = res.data
    } catch (err: any) {
      console.error('获取仪表盘数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取 LLM 配置
   */
  async function fetchLlmConfig(): Promise<void> {
    try {
      const res = await apiGetLlmConfig()
      llmConfig.value = res.data
    } catch (err: any) {
      console.error('获取 LLM 配置失败:', err)
    }
  }

  /**
   * 更新 LLM 配置
   */
  async function updateLlmConfigAction(data: Partial<LlmConfig>): Promise<void> {
    try {
      const res = await apiUpdateLlmConfig(data)
      llmConfig.value = res.data
      ElMessage.success('LLM 配置更新成功')
    } catch (err: any) {
      throw err
    }
  }

  return {
    sidebarCollapsed,
    llmConfig,
    systemStats,
    loading,
    toggleSidebar,
    setSidebarCollapsed,
    fetchDashboardStats,
    fetchLlmConfig,
    updateLlmConfigAction,
  }
})

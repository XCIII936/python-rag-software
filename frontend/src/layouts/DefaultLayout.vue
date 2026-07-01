<template>
  <el-container class="default-layout">
    <!-- 侧边栏 -->
    <el-aside
      :width="appStore.sidebarCollapsed ? '64px' : '220px'"
      class="layout-aside"
    >
      <div class="sidebar-logo" @click="router.push('/dashboard')">
        <el-icon :size="28" color="#409EFF">
          <Reading />
        </el-icon>
        <transition name="fade">
          <span v-show="!appStore.sidebarCollapsed" class="sidebar-title">课程教学助手</span>
        </transition>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="appStore.sidebarCollapsed"
        :router="true"
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        class="sidebar-menu"
      >
        <!-- 学生和教师都能看到的 -->
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>

        <el-menu-item index="/chat">
          <el-icon><ChatLineSquare /></el-icon>
          <template #title>学习助手</template>
        </el-menu-item>

        <el-menu-item index="/chapters">
          <el-icon><FolderOpened /></el-icon>
          <template #title>章节列表</template>
        </el-menu-item>

        <!-- 仅教师可见 -->
        <template v-if="authStore.isTeacher">
          <el-divider class="menu-divider" />
          <el-menu-item index="/admin/chapters">
            <el-icon><Management /></el-icon>
            <template #title>章节管理</template>
          </el-menu-item>

          <el-sub-menu index="system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/system/llm-config">
              <el-icon><Cpu /></el-icon>
              <template #title>LLM 配置</template>
            </el-menu-item>
            <el-menu-item index="/system/agents">
              <el-icon><User /></el-icon>
              <template #title>智能体管理</template>
            </el-menu-item>
            <el-menu-item index="/system/logs">
              <el-icon><Document /></el-icon>
              <template #title>系统日志</template>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>

    <!-- 主区域 -->
    <el-container class="layout-main-container">
      <!-- 顶部导航栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-button
            text
            class="collapse-btn"
            @click="appStore.toggleSidebar()"
          >
            <el-icon :size="20">
              <Fold v-if="!appStore.sidebarCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title as string }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-dropdown trigger="click" @command="handleDropdownCommand">
            <span class="user-dropdown">
              <el-avatar
                :size="32"
                :icon="UserFilled"
                :src="authStore.user?.avatar || undefined"
                class="user-avatar"
              />
              <span class="username">{{ authStore.username }}</span>
              <el-tag
                :type="authStore.isTeacher ? 'warning' : 'success'"
                size="small"
                class="role-tag"
              >
                {{ authStore.isTeacher ? '教师' : '学生' }}
              </el-tag>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人信息
                </el-dropdown-item>
                <el-dropdown-item command="dashboard">
                  <el-icon><Odometer /></el-icon>仪表盘
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主要内容区 -->
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import {
  Reading,
  Odometer,
  ChatLineSquare,
  FolderOpened,
  Management,
  Setting,
  Cpu,
  User as UserIcon,
  Document,
  Fold,
  Expand,
  UserFilled,
  ArrowDown,
  SwitchButton,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const activeMenu = computed(() => {
  const path = route.path
  // 子路由高亮父菜单
  if (path.startsWith('/chapters/')) {
    return '/chapters'
  }
  if (path.startsWith('/system/')) {
    return path
  }
  return path
})

function handleDropdownCommand(command: string) {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'dashboard':
      router.push('/dashboard')
      break
    case 'logout':
      authStore.logout()
      router.push('/auth/login')
      break
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.default-layout {
  height: 100vh;
  overflow: hidden;
}

.layout-aside {
  background-color: #1d1e1f;
  transition: width $transition-normal;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  height: $header-height;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding: 0 16px;
  flex-shrink: 0;

  .sidebar-title {
    color: #ffffff;
    font-size: $font-size-md;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
  }
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: none;
  padding-top: 4px;

  .el-menu-item,
  .el-sub-menu__title {
    white-space: nowrap;
  }
}

.menu-divider {
  margin: 8px 16px;
  border-color: rgba(255, 255, 255, 0.05);
}

// ========== 头部 ==========
.layout-main-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.layout-header {
  height: $header-height !important;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #ffffff;
  border-bottom: 1px solid $border-lighter;
  box-shadow: $shadow-sm;
  flex-shrink: 0;
  z-index: $z-header;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .header-right {
    display: flex;
    align-items: center;
  }
}

.collapse-btn {
  padding: 8px;
  font-size: 16px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background-color $transition-fast;

  &:hover {
    background-color: $bg-base;
  }

  .username {
    font-size: $font-size-base;
    color: $text-primary;
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .role-tag {
    margin-left: 4px;
  }

  .dropdown-icon {
    font-size: 12px;
    color: $text-secondary;
  }
}

// ========== 主内容 ==========
.layout-main {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  background-color: $bg-page;
}

// ========== 过渡动画 ==========
.fade-enter-active,
.fade-leave-active {
  transition: opacity $transition-fast;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-header">
        <div class="auth-logo">
          <el-icon :size="40" color="#409EFF">
            <Reading />
          </el-icon>
        </div>
        <h1 class="auth-title">课程教学助手</h1>
        <p class="auth-subtitle">智能学习平台</p>
      </div>
      <el-card class="auth-card" shadow="medium">
        <router-view />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Reading } from '@element-plus/icons-vue'
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.auth-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-container {
  width: 100%;
  max-width: 420px;
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
}

.auth-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 18px;
  margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.auth-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.auth-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  letter-spacing: 2px;
}

.auth-card {
  border-radius: 12px;
  overflow: hidden;
  :deep(.el-card__body) {
    padding: 32px;
  }
}
</style>

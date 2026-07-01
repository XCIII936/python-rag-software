<template>
  <div class="login-view">
    <h2 class="form-title">登录</h2>
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="0"
      size="large"
      @keyup.enter="handleLogin"
    >
      <el-form-item prop="username">
        <el-input
          v-model="formData.username"
          placeholder="用户名"
          :prefix-icon="User"
          clearable
        />
      </el-form-item>

      <el-form-item prop="password">
        <el-input
          v-model="formData.password"
          type="password"
          placeholder="密码"
          :prefix-icon="Lock"
          show-password
          clearable
        />
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          :loading="authStore.loading"
          class="submit-btn"
          @click="handleLogin"
        >
          {{ authStore.loading ? '登录中...' : '登录' }}
        </el-button>
      </el-form-item>
    </el-form>

    <div class="form-footer">
      <span>还没有账号？</span>
      <router-link to="/auth/register">立即注册</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()

const formData = reactive({
  username: '',
  password: '',
})

const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度为 2-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为 6-100 个字符', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    await authStore.login(formData)
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.push(redirect)
  } catch (err: any) {
    if (err.message) {
      ElMessage.error(err.message)
    }
  }
}
</script>

<style scoped lang="scss">
.login-view {
  .form-title {
    text-align: center;
    margin: 0 0 24px;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }

  .submit-btn {
    width: 100%;
    margin-top: 8px;
  }

  .form-footer {
    text-align: center;
    margin-top: 16px;
    font-size: 14px;
    color: #909399;

    a {
      margin-left: 4px;
    }
  }
}
</style>

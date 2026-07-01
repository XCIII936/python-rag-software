<template>
  <div class="register-view">
    <h2 class="form-title">注册</h2>
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="0"
      size="large"
      @keyup.enter="handleRegister"
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

      <el-form-item prop="confirmPassword">
        <el-input
          v-model="formData.confirmPassword"
          type="password"
          placeholder="确认密码"
          :prefix-icon="Lock"
          show-password
          clearable
        />
      </el-form-item>

      <el-form-item prop="email">
        <el-input
          v-model="formData.email"
          placeholder="邮箱"
          :prefix-icon="Message"
          clearable
        />
      </el-form-item>

      <el-form-item prop="role">
        <el-radio-group v-model="formData.role" class="role-selector">
          <el-radio-button value="student">学生</el-radio-button>
          <el-radio-button value="teacher">教师</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          :loading="authStore.loading"
          class="submit-btn"
          @click="handleRegister"
        >
          {{ authStore.loading ? '注册中...' : '注册' }}
        </el-button>
      </el-form-item>
    </el-form>

    <div class="form-footer">
      <span>已有账号？</span>
      <router-link to="/auth/login">立即登录</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()

const formData = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  role: 'student' as 'student' | 'teacher',
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== formData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度为 2-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为 6-100 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' },
  ],
}

async function handleRegister() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    await authStore.register({
      username: formData.username,
      password: formData.password,
      email: formData.email,
      role: formData.role,
    })
    router.push('/dashboard')
  } catch (err: any) {
    if (err.message) {
      ElMessage.error(err.message)
    }
  }
}
</script>

<style scoped lang="scss">
.register-view {
  .form-title {
    text-align: center;
    margin: 0 0 24px;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }

  .role-selector {
    display: flex;
    width: 100%;

    :deep(.el-radio-button) {
      flex: 1;
      .el-radio-button__inner {
        width: 100%;
        justify-content: center;
      }
    }
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

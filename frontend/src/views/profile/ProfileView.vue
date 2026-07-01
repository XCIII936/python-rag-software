<template>
  <div class="page-container">
    <div class="page-header">
      <h2>个人信息</h2>
    </div>

    <el-row :gutter="20">
      <!-- 基本信息 -->
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
              <el-button
                :type="isEditing ? 'primary' : 'default'"
                size="small"
                @click="toggleEdit"
              >
                {{ isEditing ? '保存' : '编辑' }}
              </el-button>
            </div>
          </template>

          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="100px"
            :disabled="!isEditing"
          >
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>

            <el-form-item label="角色">
              <el-tag :type="authStore.isTeacher ? 'warning' : 'success'">
                {{ authStore.isTeacher ? '教师' : '学生' }}
              </el-tag>
            </el-form-item>

            <el-form-item label="注册时间">
              <span class="text-secondary">{{ authStore.user?.created_at }}</span>
            </el-form-item>

            <el-form-item label="最近更新">
              <span class="text-secondary">{{ authStore.user?.updated_at }}</span>
            </el-form-item>

            <el-form-item v-if="isEditing">
              <el-button type="primary" @click="saveProfile">保存修改</el-button>
              <el-button @click="cancelEdit">取消</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 修改密码 -->
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <span>修改密码</span>
          </template>

          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="0"
          >
            <el-form-item prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="当前密码"
                show-password
              />
            </el-form-item>

            <el-form-item prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="新密码"
                show-password
              />
            </el-form-item>

            <el-form-item prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="确认新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="changingPassword"
                @click="handleChangePassword"
              >
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { changePassword } from '@/api/auth'

const authStore = useAuthStore()
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const isEditing = ref(false)
const changingPassword = ref(false)

// 个人资料表单
const profileForm = reactive({
  username: authStore.user?.username || '',
  email: authStore.user?.email || '',
})

const profileRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
}

// 密码表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirmPwd = (_rule: any, value: string, callback: any) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为 6-100 个字符', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' },
  ],
}

function toggleEdit() {
  if (isEditing.value) {
    saveProfile()
  } else {
    isEditing.value = true
  }
}

function cancelEdit() {
  isEditing.value = false
  profileForm.email = authStore.user?.email || ''
}

async function saveProfile() {
  if (!profileFormRef.value) return
  try {
    await profileFormRef.value.validate()
    await authStore.updateProfileData({ email: profileForm.email })
    isEditing.value = false
  } catch {
    // 错误已在 store 或表单验证中处理
  }
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return
  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true
    await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (err: any) {
    if (err.message) {
      ElMessage.error(err.message)
    }
  } finally {
    changingPassword.value = false
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.text-secondary {
  color: $text-secondary;
  font-size: $font-size-base;
}
</style>

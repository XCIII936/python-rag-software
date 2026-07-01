<template>
  <div class="page-container">
    <div class="page-header">
      <h2>LLM 配置</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <span>模型配置</span>
          </template>

          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="120px"
            label-position="left"
            v-loading="loading"
          >
            <el-form-item label="API Key" prop="api_key">
              <el-input
                v-model="formData.api_key"
                type="password"
                placeholder="请输入 API Key"
                show-password
                clearable
              />
            </el-form-item>

            <el-form-item label="模型名称" prop="model_name">
              <el-input
                v-model="formData.model_name"
                placeholder="例如: gpt-4o, claude-3-opus"
                clearable
              />
            </el-form-item>

            <el-form-item label="Base URL" prop="base_url">
              <el-input
                v-model="formData.base_url"
                placeholder="例如: https://api.openai.com/v1"
                clearable
              />
            </el-form-item>

            <el-form-item label="温度" prop="temperature">
              <div class="slider-wrapper">
                <el-slider
                  v-model="formData.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  show-input
                  input-size="small"
                />
                <span class="slider-hint">较低值使输出更确定，较高值使输出更随机</span>
              </div>
            </el-form-item>

            <el-form-item label="最大 Token" prop="max_tokens">
              <el-input-number
                v-model="formData.max_tokens"
                :min="256"
                :max="32768"
                :step="256"
              />
            </el-form-item>

            <el-form-item>
              <div class="form-actions">
                <el-button
                  type="primary"
                  :loading="saving"
                  @click="handleSave"
                >
                  保存配置
                </el-button>
                <el-button
                  :loading="testing"
                  @click="handleTest"
                >
                  测试连接
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <span>配置说明</span>
          </template>
          <div class="help-content">
            <h4>API Key</h4>
            <p>您的 LLM 服务提供商提供的 API 密钥，将安全加密存储。</p>

            <h4>模型名称</h4>
            <p>要使用的具体模型标识符，例如 gpt-4o、claude-3-opus-20240229 等。</p>

            <h4>Base URL</h4>
            <p>API 端点的基础 URL。对于 OpenAI 兼容接口，填写其 API 地址。</p>

            <h4>温度 (Temperature)</h4>
            <p>控制输出的随机性。范围为 0-2，默认 1.0。较低值更适合需要确定性的任务。</p>

            <h4>最大 Token</h4>
            <p>每次生成的最大 token 数量。较大的值允许更长的回复，但会消耗更多资源。</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { getLlmConfig, updateLlmConfig, testLlmConnection } from '@/api/system'

const formRef = ref<FormInstance>()
const loading = ref(true)
const saving = ref(false)
const testing = ref(false)

const formData = reactive({
  api_key: '',
  model_name: '',
  temperature: 0.7,
  max_tokens: 2048,
  base_url: '',
})

const formRules: FormRules = {
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
}

onMounted(async () => {
  try {
    const res = await getLlmConfig()
    const config = res.data
    formData.api_key = config.api_key || ''
    formData.model_name = config.model_name || 'gpt-4o'
    formData.temperature = config.temperature ?? 0.7
    formData.max_tokens = config.max_tokens || 2048
    formData.base_url = config.base_url || ''
  } catch {
    // 默认值已设置
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    saving.value = true
    await updateLlmConfig({
      api_key: formData.api_key,
      model_name: formData.model_name,
      temperature: formData.temperature,
      max_tokens: formData.max_tokens,
      base_url: formData.base_url,
    })
    ElMessage.success('配置保存成功')
  } catch (err: any) {
    if (err.message) {
      ElMessage.error(err.message)
    }
  } finally {
    saving.value = false
  }
}

async function handleTest() {
  testing.value = true
  try {
    const res = await testLlmConnection({
      api_key: formData.api_key,
      model_name: formData.model_name,
      temperature: formData.temperature,
      max_tokens: formData.max_tokens,
      base_url: formData.base_url,
    })
    if (res.data.success) {
      ElMessage.success('连接测试成功：' + (res.data.message || ''))
    } else {
      ElMessage.warning('连接测试返回：' + (res.data.message || '未知结果'))
    }
  } catch (err: any) {
    // 错误已在 request.ts 中处理
  } finally {
    testing.value = false
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.slider-wrapper {
  width: 100%;

  .slider-hint {
    display: block;
    font-size: $font-size-xs;
    color: $text-secondary;
    margin-top: 4px;
  }
}

.form-actions {
  display: flex;
  gap: 12px;
}

.help-content {
  font-size: $font-size-sm;
  color: $text-regular;
  line-height: 1.8;

  h4 {
    color: $text-primary;
    margin: 16px 0 4px;
    font-size: $font-size-base;

    &:first-child {
      margin-top: 0;
    }
  }

  p {
    margin: 0 0 8px;
    color: $text-secondary;
  }
}
</style>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>LLM 配置</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>模型切换</span>
              <el-tag type="info" size="small">API Key 从系统环境变量读取</el-tag>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="formData"
            label-width="120px"
            label-position="left"
            v-loading="loading"
          >
            <el-form-item label="供应商" prop="provider">
              <el-select v-model="formData.provider" style="width: 100%" @change="onProviderChange">
                <el-option label="DashScope (通义千问)" value="dashscope" />
                <el-option label="OpenAI 兼容" value="openai" />
                <el-option label="阿里云百炼 (DeepSeek 等)" value="bailian" />
              </el-select>
            </el-form-item>

            <el-form-item label="模型名称" prop="model_name">
              <el-select
                v-model="formData.model_name"
                style="width: 100%"
                placeholder="选择或输入模型名称"
                allow-create
                filterable
                clearable
              >
                <el-option-group
                  v-if="formData.provider === 'dashscope'"
                  label="DashScope 通义千问"
                >
                  <el-option
                    v-for="m in dashscopeModels"
                    :key="m.value"
                    :label="m.label"
                    :value="m.value"
                  />
                </el-option-group>
                <el-option-group v-else-if="formData.provider === 'bailian'" label="阿里云百炼">
                  <el-option
                    v-for="m in bailianModels"
                    :key="m.value"
                    :label="m.label"
                    :value="m.value"
                  />
                </el-option-group>
                <el-option-group v-else label="OpenAI 兼容">
                  <el-option
                    v-for="m in openaiModels"
                    :key="m.value"
                    :label="m.label"
                    :value="m.value"
                  />
                </el-option-group>
              </el-select>
            </el-form-item>

            <el-form-item label="Base URL" prop="base_url" v-if="formData.provider !== 'dashscope'">
              <el-input
                v-model="formData.base_url"
                placeholder="例如: https://api.deepseek.com/v1"
                clearable
              />
            </el-form-item>

            <el-divider content-position="left">高级参数</el-divider>

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
            <p>API Key 从系统环境变量 <code>ali-qwen3-max-api</code> 读取，无需在页面中输入。</p>

            <h4>供应商说明</h4>
            <p><b>DashScope</b>：通过阿里云百炼原生 SDK 调用通义千问 Qwen 系列模型。</p>
            <p><b>阿里云百炼</b>：通过兼容 OpenAI 的 API 调用 DeepSeek 等第三方模型，Base URL 自动填充，API Key 共用系统变量。</p>
            <p><b>OpenAI 兼容</b>：通用 OpenAI 格式 API，可接入任何兼容服务。</p>

            <h4>模型名称</h4>
            <p>支持从下拉列表选择或手动输入自定义模型名称。</p>

            <h4>Base URL</h4>
            <p>DashScope 模式无需填写。阿里云百炼/OpenAI 兼容模式需要填写 API 端点地址。</p>

            <h4>温度 (Temperature)</h4>
            <p>控制输出的随机性。范围为 0-2，较低值更适合需要确定性的任务。</p>

            <h4>最大 Token</h4>
            <p>每次生成的最大 token 数量。较大的值允许更长的回复。</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, watch } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { getLlmConfig, updateLlmConfig, testLlmConnection } from '@/api/system'

const formRef = ref<FormInstance>()
const loading = ref(true)
const saving = ref(false)
const testing = ref(false)

const dashscopeModels = [
  { label: '通义千问-Max (qwen-max)', value: 'qwen-max' },
  { label: '通义千问-Plus (qwen-plus)', value: 'qwen-plus' },
  { label: '通义千问-Turbo (qwen-turbo)', value: 'qwen-turbo' },
  { label: '通义千问3-Max (qwen3-max)', value: 'qwen3-max' },
  { label: '通义千问2.5-72B (qwen2.5-72b-instruct)', value: 'qwen2.5-72b-instruct' },
  { label: '通义千问2.5-14B (qwen2.5-14b-instruct)', value: 'qwen2.5-14b-instruct' },
  { label: '通义千问2.5-7B (qwen2.5-7b-instruct)', value: 'qwen2.5-7b-instruct' },
]

// OpenAI 兼容接口模型
const openaiModels = [
  { label: 'DeepSeek V3 (deepseek-chat)', value: 'deepseek-chat' },
  { label: 'DeepSeek R1 (deepseek-reasoner)', value: 'deepseek-reasoner' },
]

// 阿里云百炼（通过 DashScope 兼容模式调用的第三方模型）
const bailianModels = [
  { label: 'DeepSeek V4-Pro (deepseek-v4-pro)', value: 'deepseek-v4-pro' },
  { label: 'DeepSeek V4 (deepseek-v4)', value: 'deepseek-v4' },
  { label: 'DeepSeek V3 (deepseek-chat)', value: 'deepseek-chat' },
  { label: 'DeepSeek R1 (deepseek-reasoner)', value: 'deepseek-reasoner' },
  { label: '通义千问-Max (qwen-max)', value: 'qwen-max' },
  { label: '通义千问3-Max (qwen3-max)', value: 'qwen3-max' },
]

const formData = reactive({
  provider: 'dashscope' as string,
  model_name: '',
  temperature: 0.7,
  max_tokens: 2048,
  base_url: '',
})

onMounted(async () => {
  try {
    const config = await getLlmConfig()
    formData.provider = config.provider || 'dashscope'
    formData.model_name = config.model_name || 'qwen3-max'
    formData.temperature = config.temperature ?? 0.7
    formData.max_tokens = config.max_tokens || 2048
    formData.base_url = config.base_url || ''
  } catch {
    // 默认值已设置
  } finally {
    loading.value = false
  }
})

function onProviderChange(val: string) {
  // Reset model and base_url based on provider
  if (val === 'dashscope') {
    formData.base_url = ''
    formData.model_name = dashscopeModels[0]?.value || 'qwen3-max'
  } else if (val === 'bailian') {
    // 阿里云百炼兼容模式 — 自动填充 base_url，API Key 沿用系统变量
    formData.base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    formData.model_name = bailianModels[0]?.value || 'deepseek-v4-pro'
  } else if (val === 'openai') {
    formData.base_url = ''
    formData.model_name = openaiModels[0]?.value || 'deepseek-chat'
  }
}

async function handleSave() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    saving.value = true
    await updateLlmConfig({
      model_name: formData.model_name,
      provider: formData.provider,
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
      model_name: formData.model_name,
      provider: formData.provider,
      temperature: formData.temperature,
      max_tokens: formData.max_tokens,
      base_url: formData.base_url,
    })
    if (res.success) {
      ElMessage.success('连接测试成功：' + (res.message || ''))
    } else {
      ElMessage.warning('连接测试返回：' + (res.message || '未知结果'))
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

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

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

  code {
    font-size: $font-size-xs;
    background: #f5f7fa;
    padding: 1px 6px;
    border-radius: 3px;
    color: $primary-color;
  }
}
</style>

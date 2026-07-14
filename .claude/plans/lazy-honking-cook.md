# 课程教学智能体 — 补充实现计划

## 项目现状速览

**完成度**: ~90% 后端 / ~95% 前端视图结构  
**核心工作流** (RAG Chat, Assessment pipeline, Auth, CRUD) 均已完成。  
**未完成项**: 2个 Bug + 4个缺失功能 + 1个数据模型不匹配。

---

## 发现的问题清单

### 关键 Bug

| # | 位置 | 问题 | 影响 |
|---|------|------|------|
| B1 | `backend/app/services/assessment/answer_evaluator.py:58` | `_evaluate_short_answer()` 内引用未定义变量 `llm_kwargs`，父函数 `evaluate_answers()` 没有查询 `LlmConfig` 也没有传参 | 简答题评分必报 `NameError` |
| B2 | `frontend/src/stores/app.ts:42,56,68` | API 函数已解包 `res.data`，store 内又访问 `.data`，导致实际值为 `undefined` | Dashboard stats / LLM config store 数据为 null |
| B3 | `backend/app/main.py` | `agents` router 未 import 也未注册 | `/api/v1/agents/*` 全部返回 404 |

### 缺失功能

| # | 位置 | 问题 | 优先级 |
|---|------|------|--------|
| F1 | `frontend/src/views/system/AgentInvokeView.vue` | 使用 `setTimeout` 模拟回复，`// TODO: 接入后端 API` | **高** (验收指标-智能体完整性) |
| | `backend/app/api/v1/agents.py` | 缺少 `POST /agents/{id}/invoke` SSE 端点 | |
| F2 | `frontend/src/views/chapter/ChapterLearnView.vue:93` | `selectDocument()` 是 stub: `// TODO: 实现文档在线预览` | **高** (验收指标-功能完整性) |
| F3 | `frontend/src/router/index.ts` | `beforeEach` 未检查 `meta.role`，学生可访问教师路由 | **中** (前端权限缺失) |
| | `frontend/src/stores/auth.ts` | 未持久化 `role` 到 localStorage | |
| F4 | `frontend/src/views/chapter/ChapterListView.vue` | 未显示学生章节进度(completed/pending/to_learn) | **中** (需求明确要求考核路线图) |

### 数据模型不匹配

| # | 位置 | 问题 | 优先级 |
|---|------|------|--------|
| M1 | `frontend/src/views/chapter/ChapterManageView.vue` | 用 `status`(draft/published/archived) 和 `order`，后端只有 `is_active`(bool) 和 `order_index` | **高** (创建/编辑章节数据错误) |

---

> **设计决策确认**:
> - 文档预览: PDF 新标签页打开, PPT/Word 下载 (不嵌入 PDF.js)
> - Agent Invoke temperature/max_tokens: 使用 LLM 全局配置 (不修改 stream_chat 签名)
> - 章节拖拽排序: **延后处理**, 本轮不实现

## 执行方案

### Phase 1: 修复 Bug (3项)

#### Task 1: 注册 agents router (B3)
**文件**: `backend/app/main.py`
- 在第16行 import 块添加 `agents`
- 在第125行后添加 `app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])`

#### Task 2: 修复 answer_evaluator llm_kwargs (B1)
**文件**: `backend/app/services/assessment/answer_evaluator.py`
- 在 `evaluate_answers()` 函数内 (line 98 前)，仿照 `report_generator.py:186-191` 查询 `LlmConfig`:
  ```python
  llm_config = db.query(LlmConfig).filter(LlmConfig.is_active == True).first()
  llm_kwargs = {
      "provider": llm_config.provider if llm_config else "dashscope",
      "base_url": llm_config.base_url if llm_config else None,
      "model": llm_config.model_name if llm_config else None,
  }
  ```
- 在 `_evaluate_short_answer()` 签名添加 `llm_kwargs: dict` 参数
- 调用处传入 `llm_kwargs=llm_kwargs`

#### Task 3: 修复 stores/app.ts 双重解包 (B2)
**文件**: `frontend/src/stores/app.ts`
- line 42: `systemStats.value = res.data` → `systemStats.value = res`
- line 56: `llmConfig.value = res.data` → `llmConfig.value = res`
- line 68: `llmConfig.value = res.data` → `llmConfig.value = res`

---

### Phase 2: 实现 Agent Invoke (F1)

#### Task 4: 后端添加 SSE invoke 端点
**文件**: `backend/app/api/v1/agents.py` + `backend/app/schemas/agent.py`

**新 Schema** (agent.py):
```python
class AgentInvokeRequest(BaseModel):
    message: str = Field(..., min_length=1)
```

**新端点** (agents.py) — 仿照 `chat.py` SSE 模式:
```python
@router.post("/{agent_id}/invoke")
async def invoke_agent(agent_id, data, db, current_user):
    # 1. 查 AgentConfig, 校验 active
    # 2. 查 LlmConfig 获取 provider/base_url/model
    # 3. 用 agent.system_prompt + user message 构造 messages
    # 4. stream_chat() 流式返回
    # 5. SSE 事件: token / error / done
```

关键区别 chat.py:
- 无 RAG context 步骤
- 无 recommendation 步骤
- system_prompt 来自 `agent.system_prompt`
- model/temperature/max_tokens 来自 agent 配置

> **注意**: `stream_chat()` 当前不支持 temperature/max_tokens 参数。对于 agent invoke，直接用 LLM config 的默认值，不额外覆盖。

#### Task 5: 前端接入 SSE
**文件**: `frontend/src/views/system/AgentInvokeView.vue`

- 参照 `ChatView.vue` 的 SSE 模式，使用 `createSSEConnection` (已在 `utils/sse.ts`)
- 替换 `setTimeout` 为真实 `POST /api/v1/agents/{id}/invoke` 的 SSE 流
- 消息格式: `{ message: text }`
- 事件处理:
  - `token`: 追加到当前 assistant message
  - `done`: 结束流，移除 loading
  - `error`: 显示错误信息

---

### Phase 3: 权限与进度 (F3, F4)

#### Task 6: Router 角色守卫
**文件**: `frontend/src/stores/auth.ts` + `frontend/src/router/index.ts`

1. 在 `auth.ts` login/register action 成功后将 `user.role` 存入 localStorage (key: `user_role`)
2. 在 `auth.ts` logout action 清除 `user_role`
3. 在 `router/index.ts` `beforeEach` 中添加角色检查:
```typescript
// 在 line 141 (next() 之前)
const requiredRole = to.meta.role as string | undefined
if (requiredRole) {
  const userRole = localStorage.getItem('user_role')
  if (userRole !== requiredRole) {
    next({ name: 'Dashboard' })
    return
  }
}
```

#### Task 7: 章节进度展示
**文件**: `frontend/src/views/chapter/ChapterListView.vue`

- Import `getProgress` from `@/api/chapter`
- 在 `onMounted` 中额外加载 `getProgress()` 构建 `progressMap: Record<number, {status, best_score}>`
- 每张章节卡片的 footer 区域添加进度图标:
  - `completed` → ✅ "已完成"
  - `pending` → ⏳ "进行中"  
  - `to_learn`/无记录 → ○ "待学习"
- 有 `best_score` 时显示分数

---

### Phase 4: 文档预览与章节管理修复 (F2, M1)

#### Task 8: 文档预览
**文件**: `backend/app/api/v1/documents.py` + `frontend/src/views/chapter/ChapterLearnView.vue`

**后端** — 添加安全文件服务端点:
```python
@router.get("/{document_id}/file")
def get_document_file(document_id, db, current_user):
    doc = db.query(...).filter(...).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(...)
    return FileResponse(doc.file_path, filename=doc.title)
```

**前端** — 实现 `selectDocument()`:
- PDF: 用 `window.open(url, '_blank')` 在新标签页打开 (浏览器原生支持)
- PPT/Word: 用 `download` 属性触发下载
- 可选增强: 用 `<el-dialog fullscreen>` + `<iframe>` 内嵌 PDF

> 注: file_type 从文档元数据获取。不需要额外安装前端 PDF 库 — 浏览器原生支持 PDF 渲染。

#### Task 9: 修复 ChapterManageView 数据模型
**文件**: `frontend/src/views/chapter/ChapterManageView.vue`

需要替换以下内容:

1. **表格列**: `prop="order"` → `prop="order_index"`
2. **表格列**: `prop="status"` → 用 `is_active` 计算
3. **状态函数**: 
   ```typescript
   function getStatusLabel(isActive: boolean): string {
     return isActive ? '已发布' : '已归档'
   }
   function getStatusType(isActive: boolean): string {
     return isActive ? 'success' : 'info'
   }
   ```
4. **表单**: `status` 下拉框 → `is_active` 开关 (`el-switch`)
5. **`openDialog`**: `chapter.status` → `chapter.is_active`
6. **`formData`**: `status` → `is_active: boolean`

---

## 验证方案

### 后端验证
```bash
# 1. 确认 agents router 注册
curl http://localhost:8000/api/v1/agents -H "Authorization: Bearer <token>"
# 期望: [] (空列表)

# 2. 测试 agent invoke SSE
curl -N http://localhost:8000/api/v1/agents/1/invoke \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'
# 期望: SSE 流式 token 输出

# 3. 测试评估流程 (含简答题)
POST /api/v1/assessment/start/{chapterId}
# 答题 → 提交 → 获取报告
# 期望: 简答题正常评分，无 NameError
```

### 前端验证
1. **Agent Invoke**: 选择智能体 → 发送消息 → 看到流式回复
2. **文档预览**: 章节学习页 → 点击 PDF → 新标签页打开 → PPT/Word 触发下载
3. **角色守卫**: 学生登录 → 手动访问 `/system/llm-config` → 重定向到 `/dashboard`
4. **章节进度**: 完成测评后 → 章节列表页显示 ✓ 和分数
5. **章节管理**: 创建/编辑章节 → 正确显示 is_active(已发布/已归档) 和排序

---

## 涉及文件汇总

| 文件 | 修改内容 |
|------|----------|
| `backend/app/main.py` | 注册 agents router |
| `backend/app/api/v1/agents.py` | 新增 `POST /{id}/invoke` SSE 端点 |
| `backend/app/schemas/agent.py` | 新增 `AgentInvokeRequest` |
| `backend/app/services/assessment/answer_evaluator.py` | 修复 `llm_kwargs` 未定义 |
| `backend/app/api/v1/documents.py` | 新增 `GET /{id}/file` 文件服务端点 |
| `frontend/src/stores/app.ts` | 移除双重 `.data` 解包 |
| `frontend/src/stores/auth.ts` | 持久化 `role` 到 localStorage |
| `frontend/src/router/index.ts` | 添加 `meta.role` 守卫检查 |
| `frontend/src/views/system/AgentInvokeView.vue` | 替换 setTimeout 为 SSE |
| `frontend/src/views/chapter/ChapterListView.vue` | 显示章节进度 |
| `frontend/src/views/chapter/ChapterLearnView.vue` | 实现文档预览 |
| `frontend/src/views/chapter/ChapterManageView.vue` | 修复 status→is_active, order→order_index |

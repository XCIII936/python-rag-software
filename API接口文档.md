# API 接口文档

> **项目**: 软件工程课程智能教学助手（Course Agent）
> **技术栈**: FastAPI + SQLAlchemy + Milvus + DashScope/DeepSeek LLM
> **接口前缀**: `/api/v1`

---

## 目录

1. [系统架构概览](#1-系统架构概览)
2. [用户认证模块](#2-用户认证模块-auth)
3. [章节管理模块](#3-章节管理模块-chapters)
4. [知识库文档模块](#4-知识库文档模块-documents)
5. [RAG 智能问答模块](#5-rag-智能问答模块-chat)
6. [AI 考核测评模块](#6-ai-考核测评模块-assessment)
7. [智能体管理模块](#7-智能体管理模块-agents)
8. [系统管理模块](#8-系统管理模块-system)

---

## 1. 系统架构概览

```
frontend (Vue 3 + Element Plus)
    │
    ▼  HTTP REST / SSE 流式
backend (FastAPI)
    │
    ├── api/v1/          ← 路由层（接口定义）
    ├── services/        ← 业务逻辑层
    │   ├── assessment/    AI 出题、AI 批改、AI 报告生成
    │   ├── rag/           Milvus 向量检索、Embedding
    │   ├── llm/           DashScope / DeepSeek 调用（流式+同步）
    │   ├── document_parse/ PDF/PPT/Word/Markdown 解析
    │   └── recommendation/ 学习资源推荐
    ├── models/          ← 数据模型（SQLAlchemy ORM）
    ├── schemas/         ← 请求/响应模型（Pydantic）
    └── crud/            ← 数据访问层
```

**核心数据流**:

```
文档上传 → 解析(PDF/PPT/Word/MD) → 文本分块 → Embedding向量化 → Milvus索引
                                                                      │
学生提问 ────────────────────────────── RAG检索 ────────────────────────┘
    │                                                                  
    ▼                                                                  
LLM 流式回答 (SSE) ← 课程知识 + 检索上下文                                
    │                                                                  
    ▼                                                                  
推荐相关学习资料                                                          

教师配置考核 → 学生开始考核 → AI生成题目 → 逐题作答 → 交卷 → AI批改 → AI生成报告
```

---

## 2. 用户认证模块 (auth)

> **文件**: `backend/app/api/v1/auth.py`
> **路由前缀**: `/api/v1/auth`

### 2.1 用户注册

```
POST /api/v1/auth/register
```

**代码** (`auth.py:27-57`):

```python
@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and return JWT token."""
    if user_crud.get_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if data.email:
        existing = user_crud.get_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        email=data.email,
        role=data.role,  # "teacher" | "student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
```

### 2.2 用户登录

```
POST /api/v1/auth/login
```

**代码** (`auth.py:60-80`):

```python
@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = user_crud.get_by_username(db, data.username)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    user.last_login_at = datetime.utcnow()
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
```

### 2.3 其他认证接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/profile` | 获取个人信息 | 登录用户 |
| `PUT` | `/profile` | 更新个人信息 | 登录用户 |
| `PUT` | `/password` | 修改密码 | 登录用户 |

**依赖注入** (`backend/app/core/dependencies.py`):
```python
def get_current_user(...):   # 解析 JWT，返回当前用户
def require_teacher(...):    # 要求教师角色，否则 403
def require_student(...):    # 要求学生角色，否则 403
```

---

## 3. 章节管理模块 (chapters)

> **文件**: `backend/app/api/v1/chapters.py`
> **路由前缀**: `/api/v1/chapters`

### 3.1 章节列表

```
GET /api/v1/chapters
```

**代码** (`chapters.py:28-40`):

```python
@router.get("", response_model=List[ChapterResponse])
def list_chapters(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    chapters = (
        db.query(Chapter)
        .filter(Chapter.is_active == True)
        .order_by(Chapter.order_index.asc())
        .all()
    )
    return [_chapter_response(c, db) for c in chapters]
```

### 3.2 章节 CRUD

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/chapters` | 章节列表 | 登录用户 |
| `GET` | `/chapters/{id}` | 章节详情 | 登录用户 |
| `POST` | `/chapters` | 创建章节 | 教师 |
| `PUT` | `/chapters/{id}` | 更新章节 | 教师 |
| `DELETE` | `/chapters/{id}` | 删除章节（软删除） | 教师 |
| `PUT` | `/chapters/reorder` | 调整章节排序 | 教师 |
| `GET` | `/chapters/progress` | 学生学习进度 | 登录用户 |

---

## 4. 知识库文档模块 (documents)

> **文件**: `backend/app/api/v1/documents.py`
> **路由前缀**: `/api/v1/documents`

### 4.1 文档上传（核心功能）

```
POST /api/v1/documents/upload
```

**流程**: 上传 → 保存文件 → 后台异步处理（解析 → 分块 → 向量化 → 存入 Milvus）

**代码** (`documents.py:255-286`):

```python
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    chapter_id: int = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    validate_file_upload(file)
    file_path, file_name, file_size, file_hash = save_upload_file(file, "documents")

    doc = KnowledgeBaseDocument(
        chapter_id=chapter_id, title=file.filename,
        file_type=get_file_extension(file.filename).lstrip("."),
        file_path=file_path, file_size=file_size, file_hash=file_hash,
        status="pending", uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 触发后台处理：解析 → 分块 → 向量化 → Milvus
    if background_tasks:
        background_tasks.add_task(process_and_index_document, doc.id)

    return _enrich_doc_response(doc, db)
```

### 4.2 后台文档处理流程

> **文件**: `backend/app/api/v1/documents.py:35-240`

```
                         ┌──────────────────┐
文档上传                   │  status: pending  │
     │                   └────────┬─────────┘
     ▼                            │
┌─────────────┐                   ▼
│ 文件类型判断  │          ┌──────────────┐
│ .pdf .pptx   │          │ status: parsing│
│ .docx .md    │          └──────┬───────┘
└──────┬──────┘                 │
       │                        ▼
       ▼                 ┌──────────────┐
┌──────────────┐         │  文本分块      │
│ 对应解析器    │         │ chunk_size=500│
│ pdf_parser   │         │ overlap=50    │
│ ppt_parser   │         └──────┬───────┘
│ word_parser  │                │
│ md_parser    │                ▼
└──────┬──────┘         ┌──────────────┐
       │                │ DashScope     │
       ▼                │ Embedding     │
  文本提取              │ (1536维)      │
       │                └──────┬───────┘
       │                       │
       │                       ▼
       │                ┌──────────────┐
       │                │  存入 Milvus   │
       │                │ 向量数据库     │
       │                └──────┬───────┘
       │                       │
       ▼                       ▼
┌──────────────────────────────────────┐
│          status: parsed              │
│          chunk_count: N              │
└──────────────────────────────────────┘
```

**解析器位置**:
| 文件类型 | 解析器 | 位置 |
|----------|--------|------|
| PDF | `pdf_parser.py` | `backend/app/services/document_parse/` |
| PPT/PPTX | `ppt_parser.py` | `backend/app/services/document_parse/` |
| Word | `word_parser.py` | `backend/app/services/document_parse/` |
| Markdown | `markdown_parser.py` | `backend/app/services/document_parse/` |

**中文分块器** (`backend/app/services/rag/text_splitter.py`):
- 基于 `RecursiveCharacterTextSplitter`，中文标点感知
- 默认 `chunk_size=500`, `chunk_overlap=50`

### 4.3 文档管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `POST` | `/upload` | 上传文档（后台异步处理） | 教师 |
| `GET` | `` | 文档列表（支持 chapter_id 过滤） | 登录用户 |
| `GET` | `/{id}` | 文档详情 | 教师 |
| `GET` | `/{id}/file` | 文件下载/预览 | 登录用户 |
| `DELETE` | `/{id}` | 删除文档及文件 | 教师 |
| `POST` | `/{id}/reprocess` | 重新处理文档 | 教师 |

---

## 5. RAG 智能问答模块 (chat)

> **文件**: `backend/app/api/v1/chat.py`
> **路由前缀**: `/api/v1/chat`

### 5.1 核心：SSE 流式问答（RAG 增强）

```
POST /api/v1/chat/sessions/{session_id}/message
```

这是整个项目最核心的接口，实现 **RAG (检索增强生成)** 的完整流程。

**处理流程**:

```
用户提问
    │
    ├── ① 保存用户消息到数据库
    │
    ├── ② RAG 检索 (rag_chain.py → query_knowledge_base)
    │      ├── Milvus 向量相似度搜索
    │      ├── 按 chapter_id 过滤（可选）
    │      └── 格式化检索结果为上下文
    │
    ├── ③ 构建 System Prompt
    │      ├── 基础：课程教学助手角色提示
    │      └── 附加：检索到的课程资料上下文
    │
    ├── ④ LLM 流式生成 (dashscope_client.py → stream_chat)
    │      ├── 支持 DashScope / DeepSeek / OpenAI 兼容
    │      └── SSE (Server-Sent Events) 流式返回
    │
    ├── ⑤ 学习资源推荐 (recommender.py → recommend_resources)
    │      ├── 基于问答内容 + Milvus 检索
    │      └── 去重、排序后返回
    │
    └── ⑥ 保存 AI 回复到数据库
```

**SSE 事件类型** (`chat.py:296-341`):

| type | 内容 | 说明 |
|------|------|------|
| `context` | "已检索到相关课程内容..." | RAG 检索状态通知 |
| `token` | 文本片段 | LLM 流式生成的每个输出块 |
| `recommendation` | JSON 列表 | 推荐的学习资源 |
| `error` | 错误信息 | 处理失败时的提示 |
| `done` | — | 流式传输结束标记 |

**前端 SSE 消费** (`frontend/src/utils/sse.ts`):

```typescript
// 前端通过 EventSource 或 fetch + ReadableStream 接收 SSE 事件
// 根据 event.type 分别处理：
//   context  → 显示检索状态提示
//   token    → 逐字渲染 AI 回复
//   recommendation → 展示推荐资源卡片
//   done     → 停止接收，完成对话轮次
```

### 5.2 检索增强策略

**代码** (`chat.py:61-126`):

```python
def _build_system_message(db, user_question, chapter_id=None):
    """构建 System Prompt：基础提示词 + RAG 上下文"""

    # 1. 优先使用 RAG：从 Milvus 检索相关文档片段
    rag_context = query_knowledge_base(user_question, chapter_id=chapter_id)
    if rag_context:
        return base_prompt + "\n## 课程参考资料\n" + rag_context, True

    # 2. 降级策略：如果 Milvus 不可用，使用章节描述
    chapters = db.query(Chapter).filter(Chapter.is_active == True).all()
    if chapters:
        return base_prompt + "\n## 课程概览\n" + chapter_descriptions, True

    # 3. 无上下文：只用基础提示词
    return base_prompt, False
```

**向量检索** (`backend/app/services/rag/rag_chain.py:75-128`):

```python
def query_knowledge_base(question, chapter_id=None, top_k=5):
    """在 Milvus 中搜索与问题语义相似的文档片段"""
    vectorstore = _get_milvus_collection()  # LangChain Milvus 封装
    search_expr = f"chapter_id == {chapter_id}" if chapter_id else None
    docs = vectorstore.similarity_search(query=question, k=top_k, expr=search_expr)
    # 格式化结果 → "【来源 - 页码】\n内容片段"
    return formatted_context
```

### 5.3 对话管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `POST` | `/chat/sessions` | 创建新对话 | 登录用户 |
| `GET` | `/chat/sessions` | 对话列表 | 登录用户 |
| `GET` | `/chat/sessions/{id}/messages` | 历史消息 | 登录用户 |
| `PUT` | `/chat/sessions/{id}` | 重命名对话 | 登录用户 |
| `DELETE` | `/chat/sessions/{id}` | 删除对话 | 登录用户 |
| `POST` | `/chat/sessions/{id}/message` | **发送消息 (SSE流式)** | 登录用户 |

---

## 6. AI 考核测评模块 (assessment)

> **文件**: `backend/app/api/v1/assessment.py`
> **路由前缀**: `/api/v1/assessment`

这是项目的第二大核心模块，完整流程如下：

```
教师配置考核 → 学生开始考核 → AI生成题目 → 逐题作答 → 交卷 → AI批改 → AI生成报告
```

### 6.1 考核配置 (教师)

```
GET  /api/v1/assessment/configs/chapter/{chapter_id}
POST /api/v1/assessment/configs
```

**代码** (`assessment.py:54-103`):

```python
@router.post("/configs", response_model=AssessmentConfigResponse)
def create_or_update_config(data: AssessmentConfigCreate, db, current_user=require_teacher):
    """教师为章节配置考核参数"""
    # data 包含:
    #   - chapter_id: 章节 ID
    #   - knowledge_points: ["知识点1", "知识点2", ...]
    #   - question_types: {"choice": 3, "true_false": 2, "short_answer": 2}
    #   - evaluation_dimensions: [{"name": "基础知识", "weight": 40}, ...]
    #   - passing_score: 60
    config = ChapterAssessmentConfig(...)
    config.total_questions = sum(question_types.values())
    db.add(config)
    db.commit()
```

### 6.2 开始考核（AI 生成题目）

```
POST /api/v1/assessment/start/{chapter_id}
```

**流程**: 读取考核配置 → LLM 生成题目 → 创建考核记录 → 保存题目 → 返回第一题

**代码** (`assessment.py:108-167`):

```python
@router.post("/start/{chapter_id}")
def start_assessment(chapter_id, db, current_user):
    config = db.query(ChapterAssessmentConfig).filter(...).first()
    if not config:
        raise HTTPException(400, detail="该章节尚未配置考核题目")

    # 调用 LLM 生成题目（核心）
    questions_data = generate_questions(config, chapter_id, db)

    # 创建考核记录
    record = AssessmentRecord(
        user_id=current_user.id, chapter_id=chapter_id,
        config_id=config.id, status="in_progress",
        total_questions=len(questions_data),
    )
    db.add(record)
    db.commit()

    # 保存每道题目
    for i, q in enumerate(questions_data):
        question = AssessmentQuestion(
            record_id=record.id, question_index=i,
            question_type=q["type"], question_content=q["question"],
            options=json.dumps(q.get("options", [])),
            correct_answer=q.get("correct_answer"),
        )
        db.add(question)
    db.commit()
    return {"record_id": record.id, "total_questions": len(questions_data)}
```

### 6.3 AI 题目生成器

> **文件**: `backend/app/services/assessment/question_generator.py`

**流程**:

```
读取章节信息 + 知识点 + 题型配置
    │
    ▼
构建 Prompt (question_generator.py:23-98)
    │   ├── System: "你是一位专业的课程考核出题专家..."
    │   └── User:   章节标题 + 知识点 + 题型数量
    │
    ▼
LLM 生成 (同步调用 chat())
    │   ├── 最大重试 3 次
    │   └── 自动清理 JSON 格式（markdown fence）
    │
    ▼
验证题目 (_validate_question)
    │   ├── choice:    必须有 4 个选项和正确答案
    │   ├── true_false: 正确答案为 "正确"/"错误"
    │   └── short_answer: 必须有参考答案
    │
    ▼
返回题目列表
```

**三种题型**:
| 题型 | type | 判分方式 | 分数 |
|------|------|----------|------|
| 选择题 | `choice` | 选项字母直接比对 | 0 或 100 |
| 判断题 | `true_false` | 正确/错误比对 | 0 或 100 |
| 简答题 | `short_answer` | LLM 评分 0-100 | 连续分数 |

### 6.4 逐题作答

```
GET  /api/v1/assessment/{record_id}/question    获取当前未答题
POST /api/v1/assessment/{record_id}/answer      提交单题答案
```

**提交答案** (`assessment.py:196-248`):

```python
@router.post("/{record_id}/answer")
def submit_answer(record_id, data: AnswerSubmit, db, current_user):
    """提交一题答案，返回下一题或完成状态"""
    question.user_answer = data.answer
    record.answered_questions += 1
    db.commit()

    # 检查是否全部答完
    remaining = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.record_id == record_id,
        AssessmentQuestion.user_answer.is_(None),
    ).count()

    if remaining == 0:
        return {"status": "completed", "message": "所有题目已作答，请提交"}
    else:
        next_q = get_next_unanswered_question(record_id)
        return {"status": "continue", "next_question": next_q}
```

### 6.5 交卷批改（AI 评卷）

```
POST /api/v1/assessment/{record_id}/submit
```

**流程**: 获取所有题目 → AI 逐题批改 → 计算总分 → AI 生成报告 → 更新学习进度

**代码** (`assessment.py:251-304`):

```python
@router.post("/{record_id}/submit")
def submit_assessment(record_id, db, current_user):
    questions = db.query(AssessmentQuestion).filter(
        AssessmentQuestion.record_id == record_id
    ).all()

    # ① AI 逐题批改
    evaluate_answers(questions, db)

    # ② 计算总分
    total_score = sum(float(q.score) for q in questions) / len(questions)
    correct_count = sum(1 for q in questions if q.is_correct)

    record.total_score = total_score
    record.correct_answers = correct_count
    record.status = "completed"
    db.commit()

    # ③ AI 生成评估报告
    report = generate_report(record, questions, db)

    # ④ 更新章节学习进度
    progress.best_score = total_score
    progress.status = "completed"
    db.commit()
    return {"record_id": record_id, "total_score": total_score, "report_id": report.id}
```

### 6.6 AI 答案批改器

> **文件**: `backend/app/services/assessment/answer_evaluator.py`

**选择题/判断题** — 直接字符串比对，错误时 LLM 生成纠错解释:

```python
if question_type in ("choice", "true_false"):
    is_correct = normalize(user_answer) == normalize(correct_answer)
    question.score = 100.0 if is_correct else 0.0
    if not is_correct:
        question.explanation = _generate_objective_explanation(...)  # LLM 解释为何错
```

**简答题** — LLM 评分 0-100 + 详细纠错:

```python
elif question_type == "short_answer":
    score, is_correct, feedback, explanation = _evaluate_short_answer(
        question_content, correct_answer, user_answer, llm_kwargs
    )
    # is_correct: score >= 60 即为通过
    # explanation: 指出遗漏/错误 + 完整参考答案讲解
```

### 6.7 AI 报告生成器

> **文件**: `backend/app/services/assessment/report_generator.py`

```
各题得分 + 维度权重
    │
    ▼
计算维度分数 (_calculate_dimension_scores)
    ├── "基础知识" → 选择题 + 判断题得分
    └── "分析评价" → 简答题得分
    │
    ▼
LLM 生成报告内容
    ├── summary_comment:   总体评语
    ├── review_suggestions: 复习建议列表
    ├── strengths:          优势列表
    └── weaknesses:         不足列表
    │
    ▼
保存 AssessmentReport → 返回
```

### 6.8 考核相关接口总览

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/assessment/configs/chapter/{id}` | 获取考核配置 | 登录用户 |
| `POST` | `/assessment/configs` | 创建/更新考核配置 | 教师 |
| `POST` | `/assessment/start/{chapter_id}` | **开始考核 (AI出题)** | 登录用户 |
| `GET` | `/assessment/{record_id}/question` | 获取当前题目 | 本人 |
| `POST` | `/assessment/{record_id}/answer` | 提交单题答案 | 本人 |
| `POST` | `/assessment/{record_id}/submit` | **交卷 (AI批改+报告)** | 本人 |
| `GET` | `/assessment/{record_id}/report` | 查看评估报告 | 本人 |
| `GET` | `/assessment/{record_id}/review` | 逐题回顾（含纠错） | 本人 |
| `GET` | `/assessment/history` | 考核历史记录 | 登录用户 |

---

## 7. 智能体管理模块 (agents)

> **文件**: `backend/app/api/v1/agents.py`
> **路由前缀**: `/api/v1/agents`

允许教师创建和管理自定义 AI 智能体，每个智能体有独立的 system prompt。

### 7.1 智能体调用（SSE 流式）

```
POST /api/v1/agents/{agent_id}/invoke
```

**代码** (`agents.py:96-146`):

```python
@router.post("/{agent_id}/invoke")
async def invoke_agent(agent_id, data: AgentInvokeRequest, db, current_user):
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    if not agent.is_active:
        raise HTTPException(400, detail="智能体已停用")

    # 使用智能体的 system_prompt + 用户消息调用 LLM
    messages = [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": data.message},
    ]

    async def generate():
        async for chunk in stream_chat(messages=messages, ...):
            if chunk:
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 7.2 智能体管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/agents` | 智能体列表 | 登录用户 |
| `POST` | `/agents` | 创建智能体 | 教师 |
| `GET` | `/agents/{id}` | 智能体详情 | 登录用户 |
| `PUT` | `/agents/{id}` | 更新智能体 | 教师 |
| `DELETE` | `/agents/{id}` | 删除智能体 | 教师 |
| `POST` | `/agents/{id}/invoke` | **调用智能体 (SSE流式)** | 登录用户 |

---

## 8. 系统管理模块 (system)

> **文件**: `backend/app/api/v1/system.py`
> **路由前缀**: `/api/v1/system`

### 8.1 控制台仪表盘

```
GET /api/v1/system/dashboard
```

返回系统统计数据：

```python
@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db, current_user):
    return DashboardStats(
        total_students=...,      # 学生总数
        total_chapters=...,      # 活跃章节数
        total_documents=...,     # 文档总数
        total_assessments=...,   # 考核总数
        total_chat_sessions=..., # 对话总数
        recent_activity=[...],   # 最近 10 条活动日志
    )
```

### 8.2 LLM 配置管理

```
GET  /api/v1/system/llm-config
PUT  /api/v1/system/llm-config
POST /api/v1/system/llm-config/test
```

支持切换 LLM 提供商（DashScope / DeepSeek / OpenAI 兼容），运行时生效。

### 8.3 系统管理接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/system/dashboard` | 控制台统计 | 登录用户 |
| `GET` | `/system/llm-config` | 获取 LLM 配置 | 教师 |
| `PUT` | `/system/llm-config` | 更新 LLM 配置 | 教师 |
| `POST` | `/system/llm-config/test` | 测试 LLM 连接 | 教师 |
| `GET` | `/system/logs` | 系统日志（分页+筛选） | 教师 |

---

## 附录

### A. LLM 客户端

> **文件**: `backend/app/services/llm/dashscope_client.py`

```python
# 同步调用（用于题目生成、答案批改、报告生成）
chat(messages, provider, model, api_key, base_url) -> str

# 异步流式调用（用于智能问答、智能体调用）
stream_chat(messages, provider, model, api_key, base_url) -> AsyncGenerator[str]

# 文本向量化（用于文档索引和 RAG 检索）
get_embedding(text, api_key) -> List[float]  # 1536 维
```

支持的提供商：
| provider | 默认 endpoint | 模式 |
|----------|--------------|------|
| `dashscope` | DashScope SDK 原生 | 流式 + 同步 |
| `openai` / `deepseek` | `https://api.deepseek.com/v1` | httpx 流式 |
| `bailian` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | httpx 流式 |

### B. 数据库模型

> **文件**: `backend/app/models/`

| 模型 | 表名 | 说明 |
|------|------|------|
| `User` | users | 用户（教师/学生） |
| `Chapter` | chapters | 课程章节 |
| `KnowledgeBaseDocument` | knowledge_base_documents | 知识库文档 |
| `ChapterAssessmentConfig` | chapter_assessment_configs | 考核配置 |
| `AssessmentRecord` | assessment_records | 考核记录 |
| `AssessmentQuestion` | assessment_questions | 考核题目 |
| `AssessmentReport` | assessment_reports | 考核报告 |
| `ChatSession` | chat_sessions | 对话会话 |
| `ChatMessage` | chat_messages | 对话消息 |
| `ChapterProgress` | chapter_progress | 学习进度 |
| `AgentConfig` | agent_configs | 智能体配置 |
| `LlmConfig` | llm_configs | LLM 配置 |
| `SystemLog` | system_logs | 系统日志 |

### C. 前端 API 调用层

> **文件**: `frontend/src/api/`

| 文件 | 对应模块 |
|------|----------|
| `auth.ts` | 认证 |
| `chapter.ts` | 章节 |
| `document.ts` | 文档 |
| `chat.ts` | 对话 |
| `assessment.ts` | 考核 |
| `agent.ts` | 智能体 |
| `system.ts` | 系统 |

### D. 前端视图

> **文件**: `frontend/src/views/`

| 视图 | 文件 | 核心功能 |
|------|------|----------|
| 控制台 | `dashboard/DashboardView.vue` | 统计概览 |
| 章节列表 | `chapter/ChapterListView.vue` | 浏览章节+进度 |
| 章节学习 | `chapter/ChapterLearnView.vue` | 文档预览 |
| 章节管理 | `chapter/ChapterManageView.vue` | 教师管理章节 |
| 知识库 | `document/KnowledgeBaseView.vue` | 文档上传/管理 |
| 智能对话 | `chat/ChatView.vue` | RAG 问答 (SSE) |
| 考核配置 | `assessment/AssessmentConfigView.vue` | 教师配置考核 |
| 考核答题 | `assessment/AssessmentView.vue` | 学生答题界面 |
| 考核结果 | `assessment/AssessmentResultsView.vue` | 报告+逐题回顾 |
| 智能体管理 | `system/AgentManageView.vue` | 智能体 CRUD |
| LLM 配置 | `system/LlmConfigView.vue` | 模型切换配置 |

# 课程教学智能体系统 (Course Teaching Agent)

基于 **Vue 3 + FastAPI + Qwen3-Max** 的 AI 课程教学助手，为《软件工程》课程提供智能问答、资源推荐和章节考核功能。

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| **AI 对话** | SSE 流式对话，支持 Qwen3-Max / DeepSeek 双模型切换 |
| **RAG 知识库** | 上传 PDF/PPT/Word 文档，自动解析并构建向量检索 |
| **资源推荐** | 对话完成后基于语义搜索推荐相关课程资料 |
| **章节考核** | AI 智能出题（选择/判断/简答），自动评分并生成报告 |
| **角色权限** | 教师/学生双角色，教师管理内容，学生学习与考核 |

---

## 🚀 快速启动

### 方式一：开发模式（推荐）

#### 前置条件

- Python 3.11+
- Node.js 20+
- Milvus 2.4+（可选，不影响核心功能）

#### 1. 配置后端

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY
```

安装依赖并初始化：

```bash
pip install -r requirements.txt
python scripts/init_db.py   # 创建数据库 + 管理员账号
```

启动后端：

```bash
uvicorn app.main:app --reload --port 8000
```

#### 2. 配置前端

```bash
cd frontend
npm install
npm run dev
```

#### 3. 访问

浏览器打开 `http://localhost:5173`

默认管理员：`admin` / `admin123`

---

### 方式二：Docker 部署

#### 前置条件

- Docker & Docker Compose

#### 启动

```bash
# 复制环境变量模板并填入 API Key
cp backend/.env.example backend/.env
# 编辑 backend/.env 中的 DASHSCOPE_API_KEY

# 一键启动（含 Milvus 向量数据库）
docker compose up -d --build
```

#### 访问

浏览器打开 `http://localhost:8080`

---

## 🏗️ 项目结构

```
course-teaching-agent/
├── frontend/                     # Vue 3 + Element Plus + TypeScript
│   ├── src/
│   │   ├── api/                  # API 调用层
│   │   ├── assets/               # 样式文件
│   │   ├── layouts/              # 布局组件
│   │   ├── router/               # 路由 + 权限守卫
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── utils/                # SSE 客户端、Token 管理
│   │   └── views/                # 页面组件
│   ├── nginx.conf                # 生产环境 Nginx 配置
│   └── Dockerfile
│
├── backend/                      # FastAPI + SQLAlchemy + SQLite
│   ├── app/
│   │   ├── api/v1/               # 路由层（7 个模块）
│   │   ├── core/                 # 配置、安全、依赖注入
│   │   ├── crud/                 # CRUD 操作
│   │   ├── db/                   # 数据库引擎
│   │   ├── models/               # ORM 模型（14 张表）
│   │   ├── schemas/              # Pydantic 模型
│   │   ├── services/
│   │   │   ├── llm/              # LLM 客户端（Qwen + DeepSeek）
│   │   │   ├── rag/              # RAG 向量检索
│   │   │   ├── assessment/       # 出题、评分、报告
│   │   │   ├── recommendation/   # 资源推荐
│   │   │   └── document_parse/   # PDF/PPT/Word 解析
│   │   └── utils/                # 日志、文件工具
│   └── Dockerfile
│
├── docker-compose.yml            # 全栈编排（含 Milvus）
└── README.md
```

---

## 🧭 页面导航

| 路径 | 页面 | 权限 |
|------|------|------|
| `/auth/login` | 登录 | 公开 |
| `/auth/register` | 注册 | 公开 |
| `/dashboard` | 仪表盘 | 登录 |
| `/profile` | 个人信息 | 登录 |
| `/chat` | AI 对话（SSE 流式） | 登录 |
| `/chapters` | 章节列表 | 学生 |
| `/chapters/:id/learn` | 章节学习 | 学生 |
| `/chapters/:id/assessment` | 章节考核 | 学生 |
| `/assessment/:recordId/results` | 考核报告 | 学生 |
| `/admin/chapters` | 章节管理 | 教师 |
| `/knowledge-base` | 知识库管理 | 教师 |
| `/system/llm-config` | 模型配置（切换 Qwen/DeepSeek） | 教师 |
| `/system/agents` | 智能体管理 | 教师 |
| `/system/logs` | 系统日志 | 教师 |

---

## 🔌 API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/login` | 登录 |
| POST | `/api/v1/auth/register` | 注册 |
| GET | `/api/v1/chapters` | 章节列表 |
| POST | `/api/v1/chat/sessions` | 创建对话 |
| POST | `/api/v1/chat/sessions/{id}/message` | SSE 流式对话 |
| POST | `/api/v1/assessment/start/{chapter_id}` | 开始考核 |
| POST | `/api/v1/assessment/{id}/submit` | 交卷 |
| GET | `/api/v1/assessment/{id}/report` | 获取报告 |
| PUT | `/api/v1/system/llm-config` | 更新模型配置 |
| GET | `/api/v1/system/logs` | 系统日志 |
| POST | `/api/v1/documents/upload` | 上传文档 |

---

## 🧪 测试流程

**端到端验证：**

1. 注册/登录 → 进入仪表盘
2. 教师：创建章节 → 上传知识库文档 → 配置考核参数
3. 学生：进入章节学习 → AI 对话提问（验证流式输出）→ 查看推荐资源
4. 学生：参加章节考核 → 答题 → 查看评价报告
5. 教师：系统日志查看 → 模型切换测试

---

## ⚙️ 技术栈

**前端：** Vue 3 + Element Plus + TypeScript + Pinia + Vite 5
**后端：** FastAPI + SQLAlchemy 2.0 + SQLite + Python 3.11
**AI：** DashScope (Qwen3-Max) + DeepSeek (OpenAI 兼容)
**向量检索：** Milvus 2.4 + LangChain
**容器化：** Docker + Docker Compose + Nginx

---

## 📝 许可证

MIT

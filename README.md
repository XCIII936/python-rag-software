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

### 方式一：Docker 部署（推荐 ✅）

#### 前置条件

- Docker & Docker Compose

#### 1. 配置 API Key

```bash
# 方式 A：设置系统环境变量（推荐，docker-compose.yml 会自动读取）
# Linux/macOS:
export DASHSCOPE_API_KEY="your-api-key-here"

# Windows PowerShell:
$env:DASHSCOPE_API_KEY="your-api-key-here"

# 方式 B：复制模板文件并编辑
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 DASHSCOPE_API_KEY=sk-xxx
```

#### 2. 一键启动

```bash
docker compose up -d --build
```

首次启动会：
- 拉取 etcd / MinIO / Milvus / Python / Nginx 镜像
- 自动创建数据库表并导入种子数据（管理员账号 / 8 章课程资料 / 考核配置）
- 等待所有服务就绪（约 30 秒）

#### 3. 访问

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:8080 |
| 后端 API | http://localhost:8000 |
| API 文档 (Swagger) | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/api/v1/health |

默认管理员：`admin` / `admin123`

#### 4. 停止

```bash
docker compose down
```

---

### 方式二：开发模式

#### 前置条件

- Python 3.11+
- Node.js 20+
- Milvus 2.4+（可选，可通过 Docker 单独启动）

#### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m scripts.init_db      # 创建数据库 + 管理员账号
uvicorn app.main:app --reload --port 8000
```

#### 2. 启动前端

```bash
cd frontend
npm install
npm run dev                     # 访问 http://localhost:5173
```

前端 Vite 开发服务器会自动代理 `/api` 请求到后端 8000 端口。

---

## 🏗️ 项目结构

```
course-teaching-agent/
├── frontend/                     # Vue 3 + Element Plus + TypeScript
│   ├── src/
│   │   ├── api/                  # API 调用层（8 个模块）
│   │   ├── assets/               # 全局样式文件
│   │   ├── components/           # 公共组件（雷达图/题目回顾）
│   │   ├── layouts/              # 布局组件（Auth/Default）
│   │   ├── router/               # 路由配置 + JWT 权限守卫
│   │   ├── stores/               # Pinia 状态管理
│   │   ├── utils/                # SSE 客户端、Token 管理
│   │   └── views/                # 页面组件（18 个视图）
│   ├── nginx.conf                # Nginx 配置（SSE + SPA 回退）
│   └── Dockerfile
│
├── backend/                      # FastAPI + SQLAlchemy + SQLite
│   ├── app/
│   │   ├── api/v1/               # 路由层（7 模块：auth/chat/chapters/
│   │   │                         #   assessment/documents/agents/system）
│   │   ├── core/                 # 配置（config）、安全（JWT）、依赖注入
│   │   ├── crud/                 # CRUD 操作层
│   │   ├── db/                   # SQLAlchemy 引擎 + Session
│   │   ├── models/               # ORM 模型（14 张表）
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   ├── services/             # 核心服务层
│   │   │   ├── llm/              # LLM 客户端（DashScope + OpenAI 兼容）
│   │   │   ├── rag/              # RAG 检索链 + 文本分块
│   │   │   ├── assessment/       # 出题 / 评分 / 报告生成
│   │   │   ├── recommendation/   # 资源推荐
│   │   │   └── document_parse/   # PDF / PPT / Word / Markdown 解析
│   │   └── utils/                # 日志、文件工具
│   ├── scripts/init_db.py        # 数据库初始化 + 种子数据
│   ├── uploads/                  # 上传文档存储
│   ├── requirements.txt
│   └── Dockerfile
│
├── course_materials/             # 《软件工程》8 章课程资料（Markdown）
├── diagrams/                     # PlantUML 架构图（4 张）
├── docker-compose.yml            # 全栈编排（5 服务）
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

---

## 📦 成果文件清单

| 类别 | 文件 | 说明 |
|------|------|------|
| 前端源码 | `frontend/` | Vue 3 + Element Plus（40个源文件） |
| 后端源码 | `backend/app/` | FastAPI + SQLAlchemy（64个源文件） |
| 数据库 | `backend/course_teaching_agent.db` | SQLite 数据库（含种子数据） |
| 数据库脚本 | `backend/scripts/init_db.py` | 建表 + 种子数据 |
| 课程设计报告 | `课程教学智能体系统-课程设计报告.docx` | 含系统设计/功能说明/数据结构设计/API文档/部署说明 |
| 部署配置 | `docker-compose.yml` | 5 服务编排 |
| 部署配置 | `backend/Dockerfile`、`frontend/Dockerfile` | 容器构建文件 |
| 架构图 | `diagrams/` | PlantUML 图（架构/部署/数据流/ER） |
| 项目说明 | `README.md` | 本文档 |

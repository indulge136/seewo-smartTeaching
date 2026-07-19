# AI 智能作业批改系统项目说明

## 项目概述

本项目是一个面向中小学场景的 AI 智能作业批改系统，当前采用前后端分离架构。

系统核心流程为：学生或教师在前端上传作业图片，后端接收 JPG/PNG 图片后调用阿里云 DashScope Qwen-VL 多模态模型进行作业图片解析，再通过 ReAct 范式的批改 Agent 执行作业感知、智能判分和诊断分析，最终将结构化结果返回前端渲染。

当前项目已经实现：

- Vue 3 前端首页与 AI 批改工作台
- 学生端登录弹窗与后端登录校验
- 作业图片选择、拖拽上传、重新选择、移除
- FastAPI 后端基础接口
- Qwen-VL 图片解析调用配置
- ReAct Agent 基础流程
- 作业感知、推理判分、诊断分析 Skill
- MySQL 初始化表结构
- Docker Compose 中间件与 API 编排
- 前后端测试用例

## 技术栈

### 前端

- Vue 3
- TypeScript
- Vite
- Vitest
- Vue Test Utils
- jsdom
- pnpm 8.15.9

### 后端

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic
- python-multipart
- mysql-connector-python

当前已经设计并接入的 Skill：

- `HomeworkPerceptionSkill`：作业图片感知与结构化解析
- `ReasoningSkill`：数学、物理、推理、计算题判分
- `HomeworkDiagnosisSkill`：错因、知识点、能力标签与学生画像增量分析
- `ObjectiveSkill`：客观题判分占位
- `RubricSkill`：作文、简答、开放题 Rubric 判分占位
- `VisionSkill`：图文混合、几何图、电路图等视觉推理题占位

### 数据库与中间件

- MySQL 8.4：核心业务数据、用户、学生档案、登录审计等
- Redis 7.4：缓存、队列等后续扩展预留
- MinIO：文件对象存储预留
- Neo4j 5.22：知识图谱预留
- Qdrant 1.10：向量数据库预留
- Docker Compose：本地开发环境编排

### 测试与验证

- 前端：Vitest + Vue Test Utils
- 后端：pytest
- 构建验证：Vite build

## 项目目录结构

```text
seewo-smartTeaching/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── grading/
│   │   ├── llm/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── security.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   └── mysql/
│       └── init/
│           └── 001_core_schema.sql
├── front/
│   ├── src/
│   │   ├── __tests__/
│   │   ├── assets/
│   │   ├── App.vue
│   │   ├── content.ts
│   │   ├── main.ts
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── skills/
│   ├── homework-diagnosis/
│   ├── homework-objective-grading/
│   ├── homework-perception/
│   ├── homework-reasoning-grading/
│   ├── homework-rubric-grading/
│   └── homework-vision-grading/
├── test/
│   ├── chinese/
│   ├── english/
│   └── math/
├── docker-compose.yml
├── README.md
```

## 目录说明

### `backend/`

后端服务目录，使用 FastAPI 编写，负责登录校验、作业图片上传、AI 模型调用、Agent 调度和结构化结果返回。

#### `backend/app/main.py`

FastAPI 应用入口，只负责创建应用、配置 CORS、中间件和注册路由。

#### `backend/app/routes/`

后端路由层。

- `auth.py`：学生端登录接口
- `grading.py`：作业上传与 AI 批改接口

#### `backend/app/agents/`

Agent 编排层。

- `homework_react.py`：ReAct 范式作业批改 Agent，负责串联作业感知、判分和诊断三个阶段。

当前 Agent 流程：

1. 调用 `HomeworkPerceptionSkill` 解析图片，生成 `trusted_question`
2. 根据题型和学科路由到对应判分 Skill
3. 调用 `HomeworkDiagnosisSkill` 输出错因、知识点、能力标签和学生画像增量

#### `backend/app/grading/`

批改相关通用能力。

- `skills.py`：Skill 加载、Skill 路由、Skill 指令拼接
- `normalization.py`：模型输出归一化，兼容字符串列表和对象列表
- `validation.py`：上传图片类型校验
- `json_utils.py`：从模型响应中提取 JSON

#### `backend/app/llm/`

大模型调用封装。

- `qwen_vl.py`：调用 DashScope Qwen-VL OpenAI-compatible 接口

支持的环境变量：

- `DASHSCOPE_API_KEY`
- `QWEN_VL_API_KEY`
- `QWEN_VL_MODEL`
- `QWEN_VL_ENDPOINT`

#### `backend/app/services/`

业务服务层。

- `homework_analysis.py`：封装作业图片分析入口，目前会实例化并运行 `HomeworkReActAgent`

#### `backend/app/schemas.py`

Pydantic 数据模型定义，包括：

- 登录请求与响应
- `TrustedQuestion`
- `PerceptionStage`
- `GradingStage`
- `DiagnosisStage`
- `HomeworkAnalysisResponse`

#### `backend/app/database.py`

MySQL 连接管理。

#### `backend/app/security.py`

密码哈希与基础安全工具。

#### `backend/tests/`

后端测试目录，覆盖：

- 上传文件类型校验
- API Key 缺失错误
- Qwen-VL 上游错误透传
- Skill 加载
- ReAct Agent 三阶段流程
- 模型输出归一化兼容逻辑

### `front/`

前端项目目录，使用 Vue 3 + Vite + TypeScript 实现。


#### `front/src/styles.css`

全局样式文件，包含首页、工作台、上传区、判分区、诊断卡片等样式。

#### `front/src/content.ts`

首页导航和核心数据文案配置。

#### `front/src/main.ts`

Vue 应用入口。

#### `front/src/__tests__/`

前端测试目录，覆盖：

- 首页首屏渲染
- AI 批改导航
- 图片上传
- 拖拽上传
- 文件类型拦截
- 登录接口调用
- 后端三阶段结果渲染
- 题干与学生作答分块
- 正确/错误两种诊断模式

### `database/`

数据库初始化目录。

#### `database/mysql/init/001_core_schema.sql`

MySQL 初始化 SQL，包含用户、学生画像、登录审计、班级等基础表结构和学生测试账号初始化数据。

### `skills/`

Agent Skill 定义目录，是当前项目内 Skill 的主要来源。

每个 Skill 目录下的 `SKILL.md` 描述该阶段的输入、输出、边界和约束。

当前重点 Skill：

- `homework-perception/SKILL.md`
- `homework-reasoning-grading/SKILL.md`
- `homework-diagnosis/SKILL.md`

部分占位 Skill 目录用于后续扩展：

- `homework-objective-grading/`
- `homework-rubric-grading/`
- `homework-vision-grading/`

### `docs/`

项目设计、计划和过程文档目录。

### `test/`

本地测试样例图片目录，按学科分组：

- `test/math/`
- `test/english/`
- `test/chinese/`

### `docker-compose.yml`

Docker Compose 编排文件，包含：

- `mysql`
- `api`
- `redis`
- `minio`
- `neo4j`
- `qdrant`

## 前后端分离架构

项目采用前后端分离：

- 前端运行在 Vite 开发服务器，默认端口通常为 `5173`
- 后端运行在 FastAPI/Uvicorn，默认端口为 `8000`
- 前端通过 `/api/...` 请求后端
- Vite 代理负责将前端开发环境的 API 请求转发到后端

## 核心业务流程

### 学生登录

1. 前端点击“学生登录”
2. 输入账号密码
3. 请求 `/api/auth/student-login`
4. 后端校验 MySQL 中的用户信息
5. 登录成功后关闭弹窗

测试账号：

```text
账号：student
密码：123
```

### AI 作业批改

1. 用户进入 AI 批改工作台
2. 上传 JPG/PNG 作业图片
3. 点击“上传解析”或“开始批改”
4. 前端提交 `FormData` 到 `/api/grading/analyze-homework`
5. 后端校验文件类型
6. 后端读取图片字节
7. 后端调用 ReAct Agent
8. Agent 根据题型选择判分 Skill
9.  Agent 生成诊断结果
10. 后端归一化输出
11. 前端右侧渲染题目理解、评语、诊断和教师复核区域

## 启动方式

### 启动后端与数据库

```powershell
cd .\seewo-smartTeaching
docker compose up -d mysql api
```

### 启动所有中间件

```powershell
docker compose up -d mysql redis minio neo4j qdrant api
```

### 启动前端

```powershell
cd .\seewo-smartTeaching\front
npx pnpm@8.15.9 install
npx pnpm@8.15.9 dev
```

默认访问：

```text
http://localhost:5173/
```

### 查看容器状态

```powershell
docker compose ps
```

### 查看 API 日志

```powershell
docker compose logs -f api
```

## 当前功能状态

### 已完成

- Vue 前端主体页面
- 首页首屏
- AI 批改工作台
- 学生登录弹窗
- 后端登录接口
- MySQL 初始化表结构
- Docker Compose 编排
- 图片上传与拖拽
- Qwen-VL 配置
- ReAct Agent 基础链路
- Perception、Reasoning、Diagnosis 三阶段
- 后端返回结果在前端右侧真实渲染
- 答对/答错两种诊断模式
- 题干与学生作答分块展示

### 待完善

- 教师端完整业务流程
- 学生端首页与个人中心
- 文件对象存储接入 MinIO
- 批改记录持久化
- 班级、作业、题目、错题集完整数据模型
- LangChain / LangGraph 深度接入
- RAG 知识库与题库推荐
- 多学科 Rubric 评分细则
- 用户权限体系
- 生产环境部署配置

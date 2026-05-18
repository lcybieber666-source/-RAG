# MedicalRAG

一个面向医疗人员使用场景的医疗知识问答 RAG 系统。项目围绕药物配伍禁忌、临床知识问答等高价值医疗知识场景展开，提供从知识库构建、查询理解、检索召回、重排序到答案生成的完整链路，既包含可运行的工程实现，也体现了 RAG 系统中常见的关键技术点。

本项目不是通用聊天机器人，而是一个偏专业问答系统：

- 服务对象：医生、护士、药师等医疗从业人员
- 核心目标：提高专业问题命中率，降低纯大模型幻觉回答风险
- 典型问题：药物配伍禁忌、输注注意事项、临床用药兼容性、专业资料检索

## 项目亮点

- 采用 `FAQ 检索 + RAG 检索增强生成` 的双通路方案
- 支持医疗文档知识库构建，包括 PDF、Word、PPT、图片、Markdown 等类型
- 使用 `BERT 微调模型` 做查询意图分类，区分通用问题与专业咨询
- 引入 `Query 增强/改写` 思路，通过策略路由选择不同检索方式
- 使用 `Milvus + BGE-M3` 实现稠密向量与稀疏向量混合检索
- 使用 `BGE Reranker` 对候选上下文进行重排序，提升召回质量
- 后端采用 `FastAPI`，前端采用 `Vue 3 + TypeScript + Vite`
- 提供 `Docker Compose` 一键启动基础服务能力

## 系统定位

这个项目实现的是一个医疗知识问答型 RAG 系统，而不是简单的“把文档喂给大模型”。

在这套系统里：

- 高频、明确、答案稳定的问题优先走 FAQ 检索
- 复杂、专业、需要上下文支撑的问题走 RAG 流程
- 对专业问题先做意图判断，再做检索策略选择
- 检索阶段既考虑语义相似度，也考虑关键词命中
- 生成阶段把检索到的上下文交给模型组织答案

这样的设计更适合医疗问答场景，因为很多问题既要求召回准确，也要求回答过程尽量可控。

## RAG 核心链路

### 1. 知识库构建

知识库构建代码主要位于：

- `integrated_qa_system/rag_qa/core/document_processor.py`
- `integrated_qa_system/rag_qa/core/vector_store.py`
- `docker/bootstrap_app_data.py`

系统支持把医疗资料目录中的文档解析为统一的 `Document` 对象，并写入向量库。当前实现支持：

- `.txt`
- `.pdf`
- `.docx`
- `.ppt`
- `.pptx`
- `.jpg`
- `.png`
- `.md`

知识库构建流程如下：

1. 遍历知识库目录，按文件类型选择加载器
2. 为文档补充元数据，例如 `source`、`file_path`、`timestamp`
3. 先做父块切分，再做子块切分
4. 为每个子块保留 `parent_id` 和 `parent_content`
5. 使用 `BGE-M3` 生成稠密向量与稀疏向量
6. 将文本、向量、父块信息和来源信息写入 Milvus

这里采用“父块-子块”两级切分思路：

- 子块用于提高检索命中率
- 父块用于在生成阶段提供更完整的上下文

这是一种比较典型、也比较实用的 RAG 知识库组织方式。

### 2. FAQ 直达检索

高频 FAQ 数据存放于：

- `integrated_qa_system/mysql_qa/data/药物配伍禁忌问答.csv`

系统会在初始化阶段把 FAQ 导入 MySQL，并基于 `BM25` 做问题匹配。对于命中度高的问题，可以直接返回结果，减少不必要的生成调用，提升响应速度和稳定性。

这一路特别适合：

- 固定答案类问题
- 药物配伍禁忌类明确问答
- 高频重复咨询问题

### 3. BERT 微调与查询意图分类

查询分类核心代码位于：

- `integrated_qa_system/rag_qa/core/query_classifier.py`
- `others/classify_data/model_generic_1000.json`

项目中使用 `bert-base-chinese` 做二分类微调，将用户问题划分为：

- `通用知识`
- `专业咨询`

它的作用不是直接回答问题，而是作为 RAG 流程的入口控制器：

- 如果是通用知识问题，可以直接交给大模型回答
- 如果是专业咨询问题，则进入医疗知识库检索与生成链路

这一步的价值在于：

- 降低所有问题都走重型 RAG 流程的成本
- 把系统资源优先留给真正需要专业知识支撑的问题
- 让问答链路更符合实际业务场景

### 4. Query 增强与改写

专业问题不会一律“原问题直接检索”，项目中实现了一个策略选择器，根据问题特点动态选择不同的查询增强方式。

相关代码位于：

- `integrated_qa_system/rag_qa/core/strategy_selector.py`
- `integrated_qa_system/rag_qa/core/rag_system.py`
- `integrated_qa_system/rag_qa/core/prompts.py`

当前支持的策略包括：

- `直接检索`
- `假设问题检索（HyDE）`
- `子查询检索`
- `回溯问题检索`

可以把它理解为一种面向 RAG 的 Query 改写/增强机制：

- `HyDE`：先让模型生成一个假设答案，再用假设答案去检索
- `子查询检索`：把复杂问题拆成多个更简单的小问题分别检索
- `回溯问题检索`：把复杂问题改写成更基础、更容易召回的问题
- `直接检索`：适合意图明确、实体明确的问题

对于医疗知识问答来说，这类策略很重要，因为很多临床问题天然具有以下特征：

- 术语复杂
- 限定条件多
- 问题中包含多个药物或多个判断维度
- 用户表达未必完全标准化

### 5. 混合检索

混合检索核心代码位于：

- `integrated_qa_system/rag_qa/core/vector_store.py`

系统使用 `BGE-M3` 同时生成：

- 稠密向量
- 稀疏向量

并在 Milvus 中建立双索引，检索时通过 `WeightedRanker` 融合两路结果：

- 稠密向量负责语义相似度
- 稀疏向量负责关键词与术语匹配

这种设计相比单纯语义检索更适合医疗场景，因为医疗问答对专有名词、药物名称、配伍对象、剂型等关键词通常非常敏感。

### 6. 重排序

检索召回后，系统不会直接把结果喂给大模型，而是先做 rerank。

当前项目使用：

- `bge-reranker-large`

做法是：

1. 先从 Milvus 中召回候选子块
2. 聚合得到去重后的父块
3. 组成 `query + 文档` 对
4. 用 `CrossEncoder` 重新计算相关性分数
5. 按分数排序后保留前 `M` 个上下文块

这一步能够明显提升最终上下文质量，是整个 RAG 效果的关键一环。

### 7. 答案生成

RAG 生成逻辑主要位于：

- `integrated_qa_system/rag_qa/core/rag_system.py`
- `integrated_qa_system/rag_qa/core/prompts.py`

系统会将最终筛选后的上下文拼接到 Prompt 中，再交给大模型生成回答。对于未命中上下文或相关度不足的情况，也保留了兜底逻辑。

在医疗场景下，这样的设计比“无脑让大模型回答”更稳妥，因为它尽量把回答建立在检索到的知识基础上。

## 技术栈

### 后端

- FastAPI
- Uvicorn
- PyMySQL
- Redis
- Milvus
- LangChain
- OpenAI Compatible API / DashScope
- Transformers
- Sentence Transformers

### 前端

- Vue 3
- TypeScript
- Vite
- Pinia
- Vue Router

### 检索与模型

- BM25
- BERT (`bert-base-chinese`) 微调分类
- BGE-M3 Embedding
- BGE Reranker

## 项目结构

```text
Rag_Item/
├── Backend/                         # FastAPI 后端
├── frontend/                        # Vue 前端
├── docker/                          # Docker 构建与初始化脚本
├── tests/                           # 测试代码
├── integrated_qa_system/
│   ├── base/                        # 配置与日志
│   ├── mysql_qa/                    # FAQ 检索链路
│   └── rag_qa/
│       ├── core/                    # RAG 核心逻辑
│       ├── edu_document_loaders/    # 文档加载器
│       ├── edu_text_spliter/        # 文本切分器
│       ├── data/                    # 知识库原始文档目录
│       ├── models/                  # 本地模型目录
│       └── rag_assesment/           # RAG 评估相关代码
├── new_main.py                      # 问答系统入口整合逻辑
├── docker-compose.yml               # 一键启动依赖服务
└── requirements.txt
```

## 快速开始

### 方式一：Docker 启动后端依赖与服务

1. 复制环境变量模板

```bash
copy docker\.env.example .env
```

2. 根据实际情况修改 `.env`

至少建议检查这些配置：

- `DASHSCOPE_API_KEY`
- `MYSQL_ROOT_PASSWORD`
- `REDIS_PASSWORD`
- `MILVUS_COLLECTION_NAME`
- `AUTH_SECRET_KEY`

3. 启动服务

```bash
docker compose up --build -d
```

启动后主要服务包括：

- MySQL
- Redis
- Milvus
- bootstrap 初始化任务
- FastAPI 后端

后端默认地址：

- `http://127.0.0.1:8080`

健康检查接口：

```bash
curl http://127.0.0.1:8080/health
```

### 方式二：本地开发运行

#### 后端

```bash
pip install -r requirements.txt
python Backend/main.py
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

## 后端接口概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/create_session` | 创建新会话 |
| POST | `/api/query` | 非流式问答 |
| WS | `/api/stream` | 流式问答 |
| GET | `/api/history/{session_id}` | 获取历史记录 |
| DELETE | `/api/history/{session_id}` | 清空历史记录 |
| GET | `/health` | 健康检查 |
| GET | `/api/sources` | 获取可选来源分类 |

## 适用场景

- 药物配伍禁忌问答
- 临床知识辅助检索
- 医疗培训资料问答
- 医护人员内部知识问答系统原型
- 医疗垂直领域 RAG 课程/毕设/项目展示

## 注意事项

### 1. 本仓库默认不包含大体积本地模型权重

由于 GitHub 文件大小限制，仓库当前没有提交以下大体积资源：

- `integrated_qa_system/rag_qa/models/`
- `integrated_qa_system/rag_qa/core/bert_results/`
- `integrated_qa_system/rag_qa/data/ai_data/`

这意味着你在新环境中运行时，需要自行准备：

- BERT 分类模型或重新训练得到的权重
- BGE-M3 与 reranker 本地模型
- 医疗知识库原始文档

### 2. 配置中的密钥请务必自行替换

请不要直接在生产环境中使用仓库内的默认配置。尤其是：

- `integrated_qa_system/config.ini`
- `.env`

里面涉及数据库、Redis、模型接口等配置，真实部署前应替换为自己的安全配置。

### 3. 这是辅助问答系统，不应替代临床决策

本项目定位是医疗知识辅助问答，适合服务医疗人员的信息获取与知识检索场景，不应用作最终临床诊疗依据。对于高风险问题，仍应结合药典、院内规范、药师审核和临床判断使用。

## 后续可扩展方向

- 增加医疗术语标准化与实体归一化
- 增加检索结果置信度阈值控制
- 增加答案引用片段与可追溯出处
- 增加更细粒度的医疗意图分类
- 增加知识库增量更新与后台管理界面
- 引入评测集，对召回率、重排效果和最终答案质量做持续评估

## 说明

如果你正在做课程设计、毕设、RAG 项目展示或医疗垂直知识问答方向的实验，这个项目的价值不只是“能跑起来”，更在于它把一个医疗 RAG 系统中比较关键的几类知识点都串到了同一套工程里：

- 知识库构建
- BERT 微调
- Query 改写/增强
- 混合检索
- 重排序
- 检索增强生成

这也是它最适合被写进 README 的地方。

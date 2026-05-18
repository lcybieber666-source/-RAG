# 前端修改与翻译对照文档

## 1. 概述
本文档记录了为适配现有后端服务而进行的前端修改，以及界面文本的中英文翻译对照表。

## 2. 前端修改记录

### 2.1 状态管理 (Stores)
- **Chat Store (`src/stores/chat.ts`)**:
  - 实现了 WebSocket 连接管理，连接到 `ws://localhost:8000/api/stream`。
  - 添加了 `session_id` 的生成和管理逻辑，确保与后端会话机制兼容。
  - 实现了流式响应的处理逻辑，支持 `start`, `token`, `end`, `error` 消息类型。

- **History Store (`src/stores/history.ts`)**:
  - 采用本地存储 (`localStorage`) 管理会话列表，以适配后端缺少全局会话列表接口的情况。
  - 实现了会话的添加、更新和删除功能。

### 2.2 视图与组件 (Views & Components)
- **Chat View (`src/views/ChatView.vue`)**:
  - 集成了 `axios` 用于获取特定会话的历史记录 (`/api/history/{session_id}`)。
  - 实现了路由参数监听，自动加载或切换会话。
  - 将后端返回的历史记录格式 (`[{question, answer}]`) 转换为前端消息格式。

- **Input Bar (`src/components/chat/InputBar.vue`)**:
  - 添加了输入验证和加载状态禁用。
  - 界面文本完全汉化。

- **Sidebar (`src/components/layout/AppSidebar.vue`)**:
  - 集成了历史记录展示和操作。
  - 界面文本完全汉化。

- **Settings (`src/views/SettingsView.vue`)**:
  - 实现了外观设置（深色模式）和 AI 模型配置。
  - 界面文本完全汉化。

## 3. 翻译对照表

### 3.1 导航与通用
| 英文原文 | 中文翻译 | 位置 |
|---------|---------|------|
| New Chat | 新建对话 | 侧边栏 |
| No history | 暂无历史 | 侧边栏 |
| Light Mode | 明亮模式 | 侧边栏/设置 |
| Dark Mode | 深色模式 | 侧边栏/设置 |
| Settings | 设置 | 侧边栏/设置 |
| Welcome to Vue QnA | 欢迎使用Vue问答助手 | 消息列表 |
| Ask me anything... | 输入问题开始对话。 | 消息列表 |

### 3.2 聊天界面
| 英文原文 | 中文翻译 | 位置 |
|---------|---------|------|
| Type a message... | 输入消息... | 输入框 |
| AI can make mistakes... | AI可能会犯错，请核对重要信息。 | 输入框底部 |
| You | 你 | 消息气泡 |
| Assistant | 助手 | 消息气泡 |

### 3.3 设置页面
| 英文原文 | 中文翻译 | 位置 |
|---------|---------|------|
| Manage your application... | 管理应用偏好和AI配置。 | 设置页标题下 |
| Appearance | 外观 | 设置页 |
| Switch between light... | 在明亮和深色主题之间切换。 | 设置页 |
| AI Model | AI模型 | 设置页 |
| Select Model | 选择模型 | 设置页 |
| GPT-3.5 Turbo (Fast) | GPT-3.5 Turbo (快速) | 模型选择 |
| GPT-4 (Powerful) | GPT-4 (强大) | 模型选择 |
| Claude 3 Opus (Reasoning)| Claude 3 Opus (推理) | 模型选择 |
| Response Preference | 回答偏好 | 设置页 |
| Response Length | 回答长度 | 设置页 |
| Brief | 简洁 | 长度选项 |
| Standard | 标准 | 长度选项 |
| Detailed | 详细 | 长度选项 |

## 4. 后端接口适配说明
由于后端未提供获取所有会话列表的接口 (`/api/sessions`)，前端采用了**混合模式**：
1. **会话列表**：在前端 `localStorage` 中维护，存储会话 ID、标题和最后一条消息。
2. **会话详情**：通过后端 `/api/history/{session_id}` 接口获取完整历史记录。
3. **消息发送**：通过 WebSocket `/api/stream` 实时发送和接收。

这种方案在不修改后端代码的前提下，实现了完整的历史记录管理功能。

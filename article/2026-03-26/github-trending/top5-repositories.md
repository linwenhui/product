# GitHub Trending Top 5 - 2026 年 3 月 26 日

数据来源：GitHub Trending (https://github.com/trending)

---

## 1. mvanhorn/last30days-skill

**语言**: Python | **Stars**: 7,800 | **Forks**: 724 | **今日增长**: 1,341 stars

### 用途场景

**核心功能**: AI 代理技能，跨多个社交平台进行话题研究

**主要用途**:
- 跨 Reddit、X/Twitter、Bluesky、YouTube、TikTok、Instagram、Hacker News、Polymarket 预测市场进行并行搜索
- 生成带有真实引用的综合性研究报告
- 发现最新的 prompt 技术和工具最佳实践
- 品牌/产品的社区情绪分析
- 预测市场分析和赔率追踪

**解决的问题**: 帮助用户跟上社区实际讨论、投票和公开表态的内容，填补官方文档与真实社区知识之间的差距

**关键技术**: Python 后端、Node.js 22+ (Twitter GraphQL)、ScrapeCreators API、Claude AI、SQLite

---

## 2. bytedance/deer-flow

**语言**: Python | **Stars**: 46,398 | **Forks**: 5,494 | **今日增长**: 3,787 stars

### 用途场景

**核心功能**: 开源 SuperAgent 框架，编排子代理、内存系统和沙盒执行环境

**主要用途**:
- 研究自动化和深度信息收集
- 自动化报告和演示文稿生成
- 内容工作流自动化
- 数据管道编排
- 仪表板和网页创建
- 复杂多步骤任务协调

**解决的问题**: 填补基础 AI 助手与生产级代理系统之间的差距，为代理提供文件系统、内存、执行沙盒和工具访问等基础设施

**关键技术**: LangGraph、LangChain、Python 3.12+、Node.js 22+、Docker、Kubernetes、FastAPI、React

---

## 3. BerriAI/litellm

**语言**: Python | **Stars**: 40,688 | **Forks**: 6,717 | **今日增长**: 301 stars

### 用途场景

**核心功能**: 统一的 Python SDK 和 AI 网关，支持 100+ LLM 提供商的标准化接口

**主要用途**:
- 多 LLM 提供商统一管理 (Bedrock、Azure、OpenAI、VertexAI、Anthropic、Groq 等)
- 集中式 AI 网关部署，支持多租户访问控制和支出管理
- 模型切换无需更改应用代码
- 代理调用 (A2A 协议)
- 模型上下文协议 (MCP) 工具集成

**解决的问题**: 消除 LLM 提供商碎片化，简化跨提供商的身份验证、成本追踪和日志记录

**关键技术**: Python SDK、FastAPI、OpenAI API 兼容层、Docker、支持 100+ LLM 提供商

**知名用户**: Stripe、Google ADK、Greptile、OpenHands、Netflix、OpenAI Agents SDK

---

## 4. pascalorg/editor

**语言**: TypeScript | **Stars**: 6,878 | **Forks**: 900 | **今日增长**: 2,353 stars

### 用途场景

**核心功能**: 基于 Web 的 3D 建筑设计应用程序

**主要用途**:
- 建筑设计和可视化
- 室内空间规划与家具/装置布置
- 多层建筑文档和审查
- 与利益相关者共享设计概念
- 无需桌面 CAD 软件的浏览器端 3D 编辑

**解决的问题**:
- 无需安装桌面 CAD 软件，在浏览器中提供 3D 编辑功能
- 支持建筑项目的共享和实时查看
- 提供多视角和层级视图进行全面设计审查
- 通过空间网格碰撞检测防止无效放置

**关键技术**: React 19、Next.js 16、Three.js、React Three Fiber、WebGPU、Zustand、three-bvh-csg、Turborepo、Bun

---

## 5. ruvnet/ruflo

**语言**: TypeScript | **Stars**: 26,264 | **Forks**: 2,843 | **今日增长**: 1,174 stars

### 用途场景

**核心功能**: 企业级 AI 代理编排框架，将 Claude Code 转换为强大的开发平台

**主要用途**:
- 多阶段代码审查 (专业代理协作)
- 大型代码库的复杂重构
- 安全审计与协调分析
- 自动化测试和质量保证管道
- DevOps 自动化和基础设施管理
- 文档生成和知识库构建

**解决的问题**:
- 消除手动多代理编排，实现智能路由
- 通过 WASM 转换和智能任务路由降低 LLM API 成本 (30-50%)
- 通过持久化向量内存和知识图谱保留学习模式
- 防止代理在复杂任务中目标漂移
- 支持在容错集群中管理无限代理

**关键技术**: Node.js、WebAssembly (Rust 内核)、PostgreSQL + RuVector、ONNX Runtime、TensorFlow.js、Raft/BFT 共识算法、SQLite

---

## 总结

本周 Trending Top 5 呈现出明显的 **AI 代理基础设施** 趋势：

| 仓库 | 类别 | 核心能力 |
|------|------|----------|
| last30days-skill | 研究工具 | 跨平台社交媒体的 AI 驱动研究 |
| deer-flow | 代理编排 | SuperAgent 沙盒执行框架 |
| litellm | LLM 网关 | 100+ 模型统一 API |
| editor | 3D 设计 | WebGPU 建筑可视化 |
| ruflo | 代理平台 | 多代理 Swarm 编排 |

**趋势观察**: 5 个中有 4 个直接与 AI 代理/LLM 相关，表明代理基础设施是当前开发者关注的热点领域。

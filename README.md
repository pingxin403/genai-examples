# 🧪 GenAI Engineering 配套代码示例

> 《生成式AI工程全栈》系列文章的配套代码仓库
> 
> 仓库地址：https://github.com/pingxin403/genai-examples

## 项目简介

本仓库包含《GenAI Engineering》系列 **112篇文章** 的配套代码示例，覆盖 **14大模块**，从入门到架构师的完整 AI 工程化实践。

每个示例目录包含：
- `README.md`：示例说明、运行环境、依赖安装、运行命令
- 示例代码文件（Python 为主，部分使用 Java/TypeScript）

## 使用说明

1. 每个示例目录包含独立的 `README.md`，说明运行方式和依赖
2. 代码语言以 Python 为主，部分示例使用 Java/TypeScript
3. 建议按模块顺序学习，循序渐进
4. 示例优先提供最小可运行版本（MVP），再补充生产化增强方案

---

## 目录

### 01-入门篇：AI工程化思维（8篇）

- [01-crud-vs-ai](01-入门篇/01-crud-vs-ai/) - 写CRUD和写AI应用到底有什么不一样
- [02-llm-capability](01-入门篇/02-llm-capability/) - 别啥都上AI！一张图看懂LLM的能力边界
- [03-ai-nightmares](01-入门篇/03-ai-nightmares/) - AI工程师的四大噩梦：幻觉、延迟、成本、评估
- [04-ai-roi](01-入门篇/04-ai-roi/) - 老板问"AI值不值"？这是我算ROI的Excel模板
- [05-ai-architecture](01-入门篇/05-ai-architecture/) - 一张图看懂AI应用架构：从用户请求到大模型
- [06-ai-iteration](01-入门篇/06-ai-iteration/) - AI应用怎么迭代？和传统CI/CD完全不一样
- [07-probabilistic-design](01-入门篇/07-probabilistic-design/) - 概率性系统的设计哲学：接受不完美，但可控
- [08-first-ai-project](01-入门篇/08-first-ai-project/) - 我的第一个AI项目复盘：从Demo到线上只差这5步

### 02-Prompt工程篇：和LLM对话是一门系统工程（8篇）

- [09-prompt-evolution](02-Prompt工程篇/09-prompt-evolution/) - 从零样本到思维链：Prompt工程进化的四个阶段
- [10-token-saving](02-Prompt工程篇/10-token-saving/) - 上下文窗口爆了？这是5种省Token的实战技巧
- [11-function-calling](02-Prompt工程篇/11-function-calling/) - 函数调用（Function Calling）的工程化落地
- [12-structured-output](02-Prompt工程篇/12-structured-output/) - 别让AI乱说话！输出结构化控制的3层防线
- [13-prompt-management](02-Prompt工程篇/13-prompt-management/) - 系统提示词的企业级管理：版本化、A/B测试、灰度
- [14-streaming](02-Prompt工程篇/14-streaming/) - 流式响应：SSE/WebSocket前后端联调实战
- [15-prompt-injection](02-Prompt工程篇/15-prompt-injection/) - 提示词注入攻击：你的AI系统可能正在裸奔
- [16-prompt-performance](02-Prompt工程篇/16-prompt-performance/) - Prompt性能分析：一个Prompt吃掉多少Token

### 03-RAG深度篇：企业知识库的搜索引擎+大脑（12篇）

- [17-rag-evolution](03-RAG深度篇/17-rag-evolution/) - RAG进化史：从Naive到Modular
- [18-doc-parsing](03-RAG深度篇/18-doc-parsing/) - 非结构化数据"洗"成向量：文档解析的5个坑
- [19-chunking](03-RAG深度篇/19-chunking/) - 分块（Chunking）的艺术：语义边界vs固定大小
- [20-embedding-eval](03-RAG深度篇/20-embedding-eval/) - Embedding模型怎么选？7款主流模型横向评测
- [21-hybrid-search](03-RAG深度篇/21-hybrid-search/) - 混合搜索：向量+关键词，1+1>2的融合之道
- [22-vector-db](03-RAG深度篇/22-vector-db/) - 向量数据库选型：Chroma/PGVector/Milvus/Qdrant对比
- [23-rerank](03-RAG深度篇/23-rerank/) - Rerank精排：如何把Top 100变Top 10还不掉精度
- [24-knowledge-sync](03-RAG深度篇/24-knowledge-sync/) - 知识更新了，向量库咋同步？CDC+版本控制方案
- [25-rag-evaluation](03-RAG深度篇/25-rag-evaluation/) - RAG效果怎么评估？召回率、忠实度、有用性全量化
- [26-rag-pipeline](03-RAG深度篇/26-rag-pipeline/) - 生产级RAG Pipeline：从知识摄入到推理的全链路
- [27-multimodal-rag](03-RAG深度篇/27-multimodal-rag/) - 多模态RAG：当图片、表格也成为检索对象
- [28-rag-performance](03-RAG深度篇/28-rag-performance/) - RAG性能优化：从2秒到200毫秒的优化之路

### 04-Agent智能体篇：从问答到做事（10篇）

- [29-agent-paradigms](04-Agent智能体篇/29-agent-paradigms/) - Agent三大范式：ReAct、Plan-and-Execute、Multi-Agent
- [30-langgraph](04-Agent智能体篇/30-langgraph/) - LangGraph实战：把业务流程画成状态图
- [31-tool-calling-security](04-Agent智能体篇/31-tool-calling-security/) - 工具调用（Tool Calling）的安全边界设计
- [32-agent-memory](04-Agent智能体篇/32-agent-memory/) - Agent的记忆：短时/长时/语义记忆怎么管
- [33-agent-observability](04-Agent智能体篇/33-agent-observability/) - 看得见的Agent：如何追踪它为什么这么做
- [34-agent-safety](04-Agent智能体篇/34-agent-safety/) - Agent防失控：死循环、工具滥用、天价账单
- [35-multi-agent](04-Agent智能体篇/35-multi-agent/) - Multi-Agent协作：主管+专员+质检的团队模式
- [36-agent-performance](04-Agent智能体篇/36-agent-performance/) - Agent性能剖析：延迟累积、Token爆炸怎么破
- [37-react-pattern](04-Agent智能体篇/37-react-pattern/) - ReAct模式深度拆解：思考-行动-观察的循环控制
- [38-agent-autonomy](04-Agent智能体篇/38-agent-autonomy/) - 从Copilot到Autopilot：Agent自主度提升的5个阶段

### 05-MCP与智能体通信篇：让Agent学会调用工具（6篇）

- [39-mcp-intro](05-MCP与智能体通信篇/39-mcp-intro/) - MCP协议解密：模型上下文协议到底解决了什么问题
- [40-mcp-server](05-MCP与智能体通信篇/40-mcp-server/) - MCP Server实现：把内部API包装成Agent能懂的工具
- [41-mcp-client](05-MCP与智能体通信篇/41-mcp-client/) - MCP Client集成：让Agent动态发现和调用工具
- [42-mcp-security](05-MCP与智能体通信篇/42-mcp-security/) - MCP安全模型：跨系统调用时，身份怎么传
- [43-mcp-vs-api](05-MCP与智能体通信篇/43-mcp-vs-api/) - MCP vs 传统API：什么时候该用谁
- [44-skills-engineering](05-MCP与智能体通信篇/44-skills-engineering/) - Skills工程化：把企业能力抽象成Agent技能

### 06-模型工程与微调篇：当通用模型不够用时（8篇）

- [45-finetune-decision](06-模型工程与微调篇/45-finetune-decision/) - 微调决策框架：什么时候RAG不够，必须微调
- [46-finetune-data](06-模型工程与微调篇/46-finetune-data/) - 微调数据工程：高质量指令数据的洗法
- [47-lora-qlora](06-模型工程与微调篇/47-lora-qlora/) - LoRA/QLoRA实战：消费级显卡也能微调大模型
- [48-model-versioning](06-模型工程与微调篇/48-model-versioning/) - 模型版本管理：底座模型升级，应用会崩吗
- [49-semantic-cache](06-模型工程与微调篇/49-semantic-cache/) - 语义缓存：当重复请求命中相同Prompt时
- [50-inference-optimization](06-模型工程与微调篇/50-inference-optimization/) - 推理优化：首Token时间、吞吐量、延迟怎么平衡
- [51-rlhf](06-模型工程与微调篇/51-rlhf/) - RLHF工程化：人类反馈如何变成模型能力
- [52-model-serving](06-模型工程与微调篇/52-model-serving/) - 模型运维：vLLM/TGI/TensorRT-LLM部署对比

### 07-AI可观测性篇：不止看日志更要看思考（8篇）

- [53-ai-golden-signals](07-AI可观测性篇/53-ai-golden-signals/) - AI黄金信号：除了延迟/错误，还要看什么
- [54-llm-tracing](07-AI可观测性篇/54-llm-tracing/) - LLM调用追踪：把Prompt和Completion打进Trace
- [55-feedback-loop](07-AI可观测性篇/55-feedback-loop/) - 用户反馈闭环：点赞/点踩数据如何变成评估集
- [56-ai-alerting](07-AI可观测性篇/56-ai-alerting/) - AI告警设计：幻觉率>5%？成本突增？该告警了
- [57-ab-testing](07-AI可观测性篇/57-ab-testing/) - A/B测试：Prompt版本、RAG策略如何科学对比
- [58-cost-attribution](07-AI可观测性篇/58-cost-attribution/) - 成本拆分：每个用户的每次对话花了多少钱
- [59-decision-observability](07-AI可观测性篇/59-decision-observability/) - 决策可观测性：Agent的思考过程也能追踪
- [60-model-degradation](07-AI可观测性篇/60-model-degradation/) - 模型退化检测：线上效果突然变差，怎么发现

### 08-AI安全与合规篇：AI系统的护城河（8篇）

- [61-ai-security](08-AI安全与合规篇/61-ai-security/) - AI安全三道防线：输入过滤+输出检测+敏感词库
- [62-rag-auth](08-AI安全与合规篇/62-rag-auth/) - 私有知识安全：RAG系统的权限怎么和Auth集成
- [63-content-compliance](08-AI安全与合规篇/63-content-compliance/) - 生成内容合规：版权风险、幻觉免责怎么搞
- [64-output-signing](08-AI安全与合规篇/64-output-signing/) - 模型输出签名：如何证明结果来自你的系统
- [65-multi-tenancy](08-AI安全与合规篇/65-multi-tenancy/) - 多租户隔离：不同客户的知识在向量库怎么隔离
- [66-data-sovereignty](08-AI安全与合规篇/66-data-sovereignty/) - 数据主权：跨境知识检索的合规方案
- [67-red-team](08-AI安全与合规篇/67-red-team/) - 红蓝对抗：如何模拟提示词注入攻击
- [68-ai-audit](08-AI安全与合规篇/68-ai-audit/) - AI审计：记录谁、在什么时候、问了AI什么

### 09-AI平台工程篇：为组织提供AI能力中台（8篇）

- [69-ai-gateway](09-AI平台工程篇/69-ai-gateway/) - AI Gateway：统一的模型接入、路由、降级层
- [70-prompt-platform](09-AI平台工程篇/70-prompt-platform/) - Prompt管理平台：提示词的Git+CI/CD+灰度
- [71-rag-as-service](09-AI平台工程篇/71-rag-as-service/) - 知识库即服务：为10个业务线提供统一RAG能力
- [72-ai-scaffold](09-AI平台工程篇/72-ai-scaffold/) - AI应用脚手架：3天搭一个LLM应用的内部模板
- [73-llm-eval-platform](09-AI平台工程篇/73-llm-eval-platform/) - LLM评测平台：离线评估+在线监控+回归测试
- [74-cost-dashboard](09-AI平台工程篇/74-cost-dashboard/) - AI成本控制面板：实时看Token消耗、预算预警
- [75-model-routing](09-AI平台工程篇/75-model-routing/) - 模型路由策略：按场景、按成本、按延迟自动调度
- [76-knowledge-governance](09-AI平台工程篇/76-knowledge-governance/) - AI知识库治理：文档过期、质量评估、更新流程

### 10-实战项目篇：完整案例拿来即用（8篇）

- [77-smart-customer-service](10-实战项目篇/77-smart-customer-service/) - 智能客服从0到1：RAG+工作流+人工兜底全实现
- [78-code-assistant](10-实战项目篇/78-code-assistant/) - 代码生成助手：上下文管理+代码安全审查
- [79-knowledge-qa](10-实战项目篇/79-knowledge-qa/) - 内部知识问答：多源数据融合+权限过滤+引用溯源
- [80-content-moderation](10-实战项目篇/80-content-moderation/) - AI内容审核：多模态+规则引擎+人工复审
- [81-data-analysis-agent](10-实战项目篇/81-data-analysis-agent/) - 数据分析Agent：NL2SQL+工具调用+可视化
- [82-doc-processing](10-实战项目篇/82-doc-processing/) - 文档智能处理：OCR+表格识别+RAG的流水线
- [83-recruitment-agent](10-实战项目篇/83-recruitment-agent/) - 招聘助手Agent：简历解析+匹配+面试邀约
- [84-sales-bot](10-实战项目篇/84-sales-bot/) - 销售赋能Bot：客户问答+竞品分析+话术建议

### 11-生态与工具篇：主流技术栈全景对比（8篇）

- [85-framework-comparison](11-生态与工具篇/85-framework-comparison/) - AI应用框架三国杀：LangChain vs LlamaIndex vs Haystack
- [86-agent-framework](11-生态与工具篇/86-agent-framework/) - Agent框架擂台：LangGraph vs AutoGen vs CrewAI
- [87-vector-db-ecosystem](11-生态与工具篇/87-vector-db-ecosystem/) - 向量数据库生态：14款主流方案怎么选
- [88-llm-deployment](11-生态与工具篇/88-llm-deployment/) - LLM部署方案：vLLM/TGI/TensorRT-LLM/Ollama对比
- [89-embedding-benchmark](11-生态与工具篇/89-embedding-benchmark/) - Embedding模型评测：7款模型在5个领域的表现
- [90-gateway-comparison](11-生态与工具篇/90-gateway-comparison/) - AI Gateway对比：LiteLLM/自研/云厂商怎么选
- [91-observability-tools](11-生态与工具篇/91-observability-tools/) - 可观测性工具：Datadog AI vs 自建OTel扩展
- [92-security-tools](11-生态与工具篇/92-security-tools/) - AI安全工具：Lakera/Guardrails/NeMo Guardrails评测

### 12-避坑指南篇：前人踩过的坑你别再踩（8篇）

- [93-rag-pitfalls](12-避坑指南篇/93-rag-pitfalls/) - RAG落地十大坑：分块不当、检索失败、上下文污染
- [94-agent-failures](12-避坑指南篇/94-agent-failures/) - Agent失控实录：死循环、工具滥用、天价账单
- [95-prompt-chaos](12-避坑指南篇/95-prompt-chaos/) - Prompt管理混乱：线上效果一夜变差，找不到原因
- [96-poc-to-production](12-避坑指南篇/96-poc-to-production/) - AI项目从POC到生产：为什么Demo很美好，上线就失败
- [97-token-cost](12-避坑指南篇/97-token-cost/) - Token成本失控：一个月烧掉10万的惨痛经历
- [98-permission-leak](12-避坑指南篇/98-permission-leak/) - 权限泄露事故：RAG系统把A公司的文档给了B公司
- [99-model-upgrade](12-避坑指南篇/99-model-upgrade/) - 模型升级兼容性：换了个底座，一半功能废了
- [100-eval-bias](12-避坑指南篇/100-eval-bias/) - 评估偏差：离线指标好看，线上用户不买账

### 13-专家视野篇：战略思考与前沿洞察（6篇）

- [101-ai-tech-debt](13-专家视野篇/101-ai-tech-debt/) - AI工程化的技术债：哪些智能会变成未来的负担
- [102-ai-autonomy-levels](13-专家视野篇/102-ai-autonomy-levels/) - 从Copilot到Autopilot：AI自主化的五个等级
- [103-ai-economics](13-专家视野篇/103-ai-economics/) - AI成本经济学：算力、Token、人力的平衡艺术
- [104-ai-org-evolution](13-专家视野篇/104-ai-org-evolution/) - AI组织演进：从项目组到卓越中心的四个阶段
- [105-tech-selection](13-专家视野篇/105-tech-selection/) - 技术选型框架：如何为未来5年选择AI技术栈
- [106-industry-standards](13-专家视野篇/106-industry-standards/) - 参与行业标准：MCP、OpenAI规范对未来的影响

### 14-面试与成长篇：通往AI架构师之路（6篇）

- [107-interview-questions](14-面试与成长篇/107-interview-questions/) - AI工程化高频面试题：从RAG到Agent的50问
- [108-interview-stories](14-面试与成长篇/108-interview-stories/) - 大厂AI面试实录：我被问倒的3个灵魂问题
- [109-skill-tree](14-面试与成长篇/109-skill-tree/) - AI工程师技能树：从调参侠到架构师的跃迁
- [110-open-source](14-面试与成长篇/110-open-source/) - 如何参与开源AI项目？LangChain/LlamaIndex贡献指南
- [111-ai-transition](14-面试与成长篇/111-ai-transition/) - 我的AI转型之路：从后端到AI工程化的心路历程
- [112-ai-architect](14-面试与成长篇/112-ai-architect/) - AI架构师的核心能力：不是技术，而是判断力

---

## 配套文章

所有技术文章：[GenAI Engineering 系列文章](../GenAI/)

## 约定

- 目录命名与文章编号保持一致，便于追踪
- 示例优先提供最小可运行版本（MVP），再补充生产化增强方案
- 所有说明文档使用中文，技术术语保留英文原文

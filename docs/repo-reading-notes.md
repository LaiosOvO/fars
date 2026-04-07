# FARS 参考仓库阅读笔记

日期：2026-04-08  
目标：给后续开发提供“读过哪些仓库、应借哪些点、不要照搬哪些点”的笔记

---

## 1. `AgentLaboratory`

- 本地路径：`/Users/admin/ai/lunwen/ref/AgentLaboratory`
- 主要定位：端到端 autonomous research workflow
- README 关键信息：
  - 三阶段：`Literature Review -> Experimentation -> Report Writing`
  - 支持 YAML 配置和 checkpoint
  - 强调 task notes、硬件限制说明、可恢复状态
- 已看到的关键文件：
  - `ai_lab_repo.py`
  - `agents.py`
  - `tools.py`
  - `papersolver.py`
  - `experiment_configs/*.yaml`
- 对 FARS 的启发：
  - research run 必须配置驱动
  - 每个阶段都要可 checkpoint / replay
  - 用户需要显式告知算力和约束
- 不要直接照搬：
  - 它更偏“研究代理流程”，不是论文知识层底座
- 结论：`工作流层高参考，知识层中等参考`

---

## 2. `autonomous-researcher`

- 本地路径：`/Users/admin/ai/lunwen/ref/autonomous-researcher`
- 主要定位：研究目标分解 + 多 agent 并发实验 + 论文式输出
- README 关键信息：
  - 会把 objective 分成 experiments
  - 每个 agent 拥有独立 GPU sandbox
  - orchestrator 根据结果决定继续还是收敛
- 对 FARS 的启发：
  - 未来的 worktree / 并发分支层可以借鉴这种“每个实验一套隔离执行环境”的思想
- 不要直接照搬：
  - 当前还没有成熟的论文知识层，不适合作为底座
- 结论：`并发实验层参考，中期使用`

---

## 3. `Oh-my--paper`

- 本地路径：`/Users/admin/ai/lunwen/ref/Oh-my--paper`
- 主要定位：研究工作区与插件化 research pipeline
- README 关键信息：
  - 5-stage pipeline：`Survey -> Ideation -> Experiment -> Publication -> Promotion`
  - 5 个角色 + 隔离 memory
  - hooks 在 session 启动时自动注入项目上下文
  - 有 `research-catalog.json`、`research-stage-map.json`
- 已看到的关键文件：
  - `skills/research-catalog.json`
  - `skills/research-stage-map.json`
  - `sidecar/index.mjs`
  - `scripts/stage-sidecar.mjs`
  - `sections/*.tex`
- 对 FARS 的启发：
  - 项目状态不要只放在 prompt 里，要有文件化的 pipeline state
  - 研究角色与 memory scope 应隔离
  - 文献调查产物、实验账本、paper sections 要分别落盘
- 不要直接照搬：
  - 这是研究工作台，不是学术知识库后端
- 结论：`流程编排和研究工作区强参考`

---

## 4. `deep-research-agent`

- 本地路径：`/Users/admin/ai/lunwen/ref/deep-research-agent`
- 主要定位：多 agent research report generator
- README 关键信息：
  - 4 agents：planner / searcher / synthesizer / writer
  - 有 credibility scoring、cache、circuit breaker、state persistence
- 已看到的关键文件：
  - `src/graph.py`
  - `src/agents.py`
  - `src/state.py`
  - `src/config.py`
- 对 FARS 的启发：
  - 你的论文知识层 API 以后会被 research planner / writer 调用
  - source credibility scoring 可以先做简单版
  - cache 与错误恢复应当从一开始就内建
- 不要直接照搬：
  - 更偏网络研究报告，不是文献知识图谱
- 结论：`状态机与缓存策略可借鉴`

---

## 5. `paper-qa`

- 本地路径：`/Users/admin/ai/lunwen/ref/paper-qa`
- 主要定位：面向科学文献的高精度 RAG 与证据问答
- README 关键信息：
  - 支持 PDF / text / Office / code
  - 强调 metadata-aware retrieval
  - 支持 agentic adding/querying documents
  - 默认整合多个 metadata provider
- 已看到的关键文件：
  - `src/paperqa/clients/openalex.py`
  - `src/paperqa/clients/semantic_scholar.py`
  - `src/paperqa/clients/crossref.py`
  - `src/paperqa/clients/unpaywall.py`
  - `src/paperqa/clients/retractions.py`
  - `src/paperqa/readers.py`
  - `src/paperqa/agents/search.py`
  - `src/paperqa/docs.py`
  - `packages/paper-qa-docling`
  - `packages/paper-qa-pymupdf`
- 对 FARS 的启发：
  - 文献知识层必须内建 metadata provider 聚合
  - parser 必须 reader 可插拔
  - query 不只是 vector search，而要结合 metadata / citations / ranking
  - retraction / journal quality / citation counts 值得做成 enrichment
- 不要直接照搬：
  - PaperQA 是 retrieval/QA 强，不是面向图谱和全文结构治理的全栈系统
- 结论：`MVP 检索与证据层极高参考`

---

## 6. `grobid`

- 本地路径：`/Users/admin/ai/lunwen/ref/grobid`
- 主要定位：科学 PDF 结构化解析核心引擎
- README 和文档关键信息：
  - 支持 header / references / citation contexts / fulltext / coordinates
  - 输出 TEI XML
  - 有完整 service API、Docker、batch、client 体系
  - 支持 citation context resolution
  - production ready，已被多个学术平台使用
- 已看到的关键文件：
  - `Readme.md`
  - `doc/Grobid-service.md`
  - `doc/TEI-encoding-of-results.md`
  - `grobid-home/config/grobid.yaml`
- 对 FARS 的启发：
  - 论文知识层的 canonical intermediate representation 最好不要自己乱造，优先 TEI/结构化 XML
  - 要保留 citation context，不只是 reference list
  - 要保留坐标和版面信息，为后续 figure/table/interactive UI 做准备
- 不要直接照搬：
  - 不要一开始就试图复制其全部模型训练体系
- 结论：`解析层事实标准，必须优先集成`

---

## 7. `grobid-client-python`

- 本地路径：`/Users/admin/ai/lunwen/ref/grobid-client-python`
- 主要定位：并发 GROBID 客户端
- README 关键信息：
  - 支持并发处理
  - 支持 `JSON` 与 `Markdown` 派生输出
  - 支持 coordinates / sentence segmentation
- 对 FARS 的启发：
  - MVP 阶段可直接把它当成论文解析调度器
  - 你不需要自己先写一套 GROBID 调用 SDK
- 结论：`工程实用性极高`

---

## 8. `sciencebeam-parser`

- 本地路径：`/Users/admin/ai/lunwen/ref/sciencebeam-parser`
- 主要定位：科学文档解析服务，部分 GROBID 兼容
- README 关键信息：
  - 支持 `processHeaderDocument / processFulltextDocument / processReferences`
  - 支持 `TEI`、`JATS`、`zip with assets`
  - 提供单一 `/convert` 端点
- 对 FARS 的启发：
  - 解析器接口要抽象成统一 contract
  - 可以定义“标准输出”为 `TEI / JATS / JSON normalized`
  - 可把 figure assets 与全文同时回收
- 结论：`可作为 GROBID 对照实现和备选引擎`

---

## 9. `scipdf_parser`

- 本地路径：`/Users/admin/ai/lunwen/ref/scipdf_parser`
- 主要定位：GROBID 的轻量封装
- README 关键信息：
  - 直接输出 `title / abstract / sections / references / figures / doi` 字典
- 对 FARS 的启发：
  - 对外 API 层可以提供“轻量 dict 视图”，便于 agent 使用
  - 内部保留 TEI，外部派生 JSON dict
- 结论：`适合快速原型，不适合做唯一底座`

---

## 10. `papercast`

- 本地路径：`/Users/admin/ai/lunwen/ref/papercast`
- 主要定位：文档处理 pipeline 与插件生态
- README 关键信息：
  - 输入源：PDF / LaTeX / ArXiv / SemanticScholar
  - extraction 可插拔
- 对 FARS 的启发：
  - ingestion connector 应当 plugin 化
- 结论：`连接器架构参考`

---

## 11. `pyalex`

- 本地路径：`/Users/admin/ai/lunwen/ref/pyalex`
- 主要定位：OpenAlex Python 客户端
- README 关键信息：
  - 支持 Work/Author/Source/Institution/Topic 等实体
  - 支持 semantic search、abstract 重建、PDF/TEI 获取
  - 自 2026-02-13 起 API key 必需
- 对 FARS 的启发：
  - OpenAlex 是你论文知识层的主 metadata 源候选
  - 需要在系统里单独管理 OpenAlex API 配额和限速
- 结论：`MVP 接入层首选`

---

## 12. `openalex-guts`

- 本地路径：`/Users/admin/ai/lunwen/ref/openalex-guts`
- 主要定位：OpenAlex 数据计算和实体生产底座
- 已看到的关键文件：
  - `models/work.py`
  - `models/citation.py`
  - `models/work_related_work.py`
  - `models/work_embedding.py`
  - `models/topic.py`
  - `models/affiliation.py`
  - `merge/*`
  - `scripts/*`
- 对 FARS 的启发：
  - 论文知识层的数据模型不应只有 `Paper`
  - 还需要 `Citation / RelatedWork / Topic / Keyword / Affiliation / Embedding / ExtraID`
- 结论：`数据模型设计极高参考`

---

## 13. `openalex-elastic-api`

- 本地路径：`/Users/admin/ai/lunwen/ref/openalex-elastic-api`
- 主要定位：OpenAlex Elasticsearch API 层
- 已看到的关键文件：
  - `core/search.py`
  - `core/filter.py`
  - `core/semantic_search.py`
  - `core/knn.py`
  - `core/cursor.py`
  - `query_translation/*`
  - `docs/api-guide-for-llms.md`
- 对 FARS 的启发：
  - API 层要有 `filter + semantic + cursor + export + autocomplete`
  - 给 agent 写一份“API guide for LLMs”非常有用
- 结论：`统一检索 API 设计的重要参考`

---

## 14. `orkg-backend`

- 本地路径：`/Users/admin/ai/lunwen/ref/orkg-backend`
- 主要定位：研究知识图谱后端 API
- README 关键信息：
  - Kotlin + Spring
  - 依赖 Neo4j + PostgreSQL
  - OpenAPI + auto-generated clients
- 对 FARS 的启发：
  - 研究图谱系统往往不是单一数据库
  - 图关系与事务元数据层可分开
- 结论：`知识图谱后端形态参考`

---

## 15. `opencitations/index`

- 本地路径：`/Users/admin/ai/lunwen/ref/index`
- 主要定位：OpenCitations 引文索引生产
- 对 FARS 的启发：
  - citation index 需要单独生产管线，不应混在解析请求里临时构建
- 结论：`离线索引构建参考`

---

## 16. `oc_meta`

- 本地路径：`/Users/admin/ai/lunwen/ref/oc_meta`
- 主要定位：书目元数据治理
- README 关键信息：
  - 处理 CSV 元数据并产出 RDF / OCDM 兼容结构
- 对 FARS 的启发：
  - 后续如果要把知识层做成可交换图谱，需预留 RDF / graph export 能力
- 结论：`元数据治理和图谱标准参考`

---

## 17. `papergraph`

- 本地路径：`/Users/admin/ai/lunwen/ref/papergraph`
- 主要定位：citation graph with Postgres + Hasura GraphQL
- 已看到的关键文件：
  - `hasura/schema.graphql`
  - `docker-compose.yml`
  - `notebooks/*.ipynb`
- 对 FARS 的启发：
  - 图谱服务不一定要上 Neo4j，`Postgres + GraphQL` 也是可行路线
  - notebook 分析体验对研究人员很重要
- 结论：`citation graph serving 参考`

---

## 18. `citation-graph-builder`

- 本地路径：`/Users/admin/ai/lunwen/ref/citation-graph-builder`
- 主要定位：从 BibTeX/PDF/API 混合构建 citation graph
- 已看到的关键文件：
  - `src/build_citation_graph.py`
  - `src/grobid_config.json`
- 对 FARS 的启发：
  - 图谱构建不能只依赖一个来源
  - PDF 解析结果要和 bibliographic API 联合校验
- 结论：`你想做的论文关系图的直接参考`

---

## 19. `awesome-automated-research`

- 本地路径：`/Users/admin/ai/lunwen/ref/awesome-automated-research`
- 主要定位：自动科研项目目录
- 对 FARS 的启发：
  - 可持续扩充参考池
  - 可作为后续竞品追踪来源
- 结论：`生态雷达，不是底层实现`

---

## 20. 阅读后的总体判断

### 最值得直接借鉴的五个能力组合

1. `pyalex + openalex-*` 负责多源学术 metadata
2. `grobid + grobid-client-python` 负责结构化全文解析
3. `paper-qa` 负责 evidence-oriented retrieval 和 metadata enrichment
4. `citation-graph-builder + papergraph + OpenCitations` 负责 citation graph
5. `Oh-my--paper + AgentLaboratory` 负责上层研究 workflow 组织

### 不建议的做法

- 不要自己从零写 PDF 结构解析器
- 不要只做向量检索，不做 citation / metadata / graph
- 不要把论文知识层和实验 worktree 状态混在一个存储里
- 不要一开始就押注单一图库或单一 citation provider

### 当前最佳实现思路

先做一个 `组合式论文知识层`：
- 接入层：OpenAlex / Crossref / Semantic Scholar / Unpaywall
- 解析层：GROBID 为主，ScienceBeam 为备
- 统一模型层：Paper / Version / Section / Chunk / Citation / CitationContext / Method / Dataset / Metric / Result
- 图谱层：先用 Postgres edge tables，后续再考虑 Neo4j 镜像
- API 层：混合检索 + 图谱查询 + 证据追踪

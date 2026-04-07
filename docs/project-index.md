# FARS 参考项目索引

日期：2026-04-08  
工作区：`/Users/admin/ai/self-dev/FARS`  
参考仓库目录：`/Users/admin/ai/lunwen/ref`

## 1. 这份索引的目的

这份文档用于给 `FARS 论文知识层` 提供可直接复用的开源参考底座。

目标不是简单收集“AI 科研项目”，而是按你当前最优先的需求拆成四类：

1. `自动科研 / research workflow`
2. `论文获取与解析`
3. `引文关系 / 学术知识图谱`
4. `检索与 API 组织方式`

当前策略是：
- 先通过多轮 `gh search repos` 搜索和去重
- 再按“对论文知识层是否有直接价值”筛选
- 全部 clone 到本地做 README 和目录级阅读
- 最终形成可执行的系统设计文档，而不是停留在灵感层

## 2. 搜索方法与选择规则

### 搜索轮次关键词

已实际搜索过的关键词包括：
- `autonomous research`
- `scientific discovery agent`
- `research agent literature review`
- `paper parser scientific pdf`
- `grobid`
- `paper-qa`
- `openalex scholarly graph`
- `open research knowledge graph`
- `citation graph`
- `semantic citation`
- `scholarly knowledge graph`
- `opencitations`
- `orkg`

### 选择规则

优先保留这些项目：
- 能直接支持 `论文获取 / 解析 / 元数据增强 / 引文关系`
- 能体现 `面向研究任务的 agent / workflow 组织方式`
- 能提供 `学术图谱或 citation graph` 的已有数据模型
- 近一年仍有更新，且结构较清晰，便于借鉴

明确降权：
- 纯 demo 项目
- 只做“报告生成”但没有知识层能力的项目
- 与学术文献结构无直接关系的通用 agent 框架

## 3. 已 clone 的参考仓库总览

| 类别 | 仓库 | Stars | 本地目录 | 价值判断 |
|---|---|---:|---|---|
| 自动科研 | `SamuelSchmidgall/AgentLaboratory` | 5484 | `/Users/admin/ai/lunwen/ref/AgentLaboratory` | 高 |
| 自动科研 | `mshumer/autonomous-researcher` | 800 | `/Users/admin/ai/lunwen/ref/autonomous-researcher` | 中高 |
| 自动科研/工作流 | `LigphiDonk/Oh-my--paper` | 309 | `/Users/admin/ai/lunwen/ref/Oh-my--paper` | 高 |
| 自动科研/研究代理 | `tarun7r/deep-research-agent` | 151 | `/Users/admin/ai/lunwen/ref/deep-research-agent` | 中高 |
| 论文问答/RAG | `Future-House/paper-qa` | 8347 | `/Users/admin/ai/lunwen/ref/paper-qa` | 极高 |
| 论文解析 | `grobidOrg/grobid` | 4769 | `/Users/admin/ai/lunwen/ref/grobid` | 极高 |
| GROBID 客户端 | `grobidOrg/grobid-client-python` | 398 | `/Users/admin/ai/lunwen/ref/grobid-client-python` | 高 |
| 论文解析 | `eLifePathways/sciencebeam-parser` | 297 | `/Users/admin/ai/lunwen/ref/sciencebeam-parser` | 高 |
| 论文解析 | `titipata/scipdf_parser` | 452 | `/Users/admin/ai/lunwen/ref/scipdf_parser` | 中高 |
| 文档处理管线 | `papercast-dev/papercast` | 54 | `/Users/admin/ai/lunwen/ref/papercast` | 中 |
| OpenAlex 客户端 | `J535D165/pyalex` | 370 | `/Users/admin/ai/lunwen/ref/pyalex` | 高 |
| OpenAlex 数据底座 | `ourresearch/openalex-guts` | 152 | `/Users/admin/ai/lunwen/ref/openalex-guts` | 极高 |
| OpenAlex API | `ourresearch/openalex-elastic-api` | 40 | `/Users/admin/ai/lunwen/ref/openalex-elastic-api` | 极高 |
| 学术知识图谱后端 | `TIBHannover/orkg-backend` | 5 | `/Users/admin/ai/lunwen/ref/orkg-backend` | 高 |
| 引文索引构建 | `opencitations/index` | 15 | `/Users/admin/ai/lunwen/ref/index` | 高 |
| 书目元数据管线 | `opencitations/oc_meta` | 9 | `/Users/admin/ai/lunwen/ref/oc_meta` | 高 |
| citation graph | `dennybritz/papergraph` | 189 | `/Users/admin/ai/lunwen/ref/papergraph` | 高 |
| citation graph 构建 | `FZJ-IEK3-VSA/citation-graph-builder` | 24 | `/Users/admin/ai/lunwen/ref/citation-graph-builder` | 高 |
| 生态索引 | `MinhaoXiong/awesome-automated-research` | 99 | `/Users/admin/ai/lunwen/ref/awesome-automated-research` | 中 |

## 4. 按价值排序的核心参考库

### P0：必须重点参考

#### 1) `grobidOrg/grobid`
- 作用：学术 PDF 结构化解析事实标准之一
- 你最该借鉴的点：
  - `PDF -> TEI XML` 主链路
  - `header / fulltext / references / citation context` 服务拆分
  - 坐标、版面、token、citation context 的联合抽取
  - 大规模并行服务化设计
- 对 FARS 的价值：是论文知识层 `解析层` 的首选底座

#### 2) `Future-House/paper-qa`
- 作用：面向科研文献的高质量 agentic RAG
- 你最该借鉴的点：
  - 多元 metadata client：`semantic_scholar / openalex / crossref / unpaywall / retractions`
  - `reader` 可插拔设计
  - 基于论文的 citation-grounded answer 组织方式
  - 支持多 reader 包：`docling / pymupdf / pypdf / nemotron`
- 对 FARS 的价值：是知识层 `文献检索 + 元数据增强 + 证据问答` 的最佳参考

#### 3) `ourresearch/openalex-guts`
- 作用：OpenAlex 的数据计算和实体建模底座
- 你最该借鉴的点：
  - `work / citation / work_related_work / work_embedding / topic / affiliation` 等实体拆分
  - 批处理、更新、合并、去重、导出脚本体系
- 对 FARS 的价值：是你设计论文知识层核心数据模型时最值得抄结构的项目之一

#### 4) `ourresearch/openalex-elastic-api`
- 作用：OpenAlex 的 Elasticsearch API 层
- 你最该借鉴的点：
  - `query_translation`
  - `filter / cursor / search / semantic_search / knn / autocomplete`
  - 面向多实体的统一 API 分层
- 对 FARS 的价值：适合作为未来知识层 `统一检索 API` 的参考样板

#### 5) `J535D165/pyalex`
- 作用：轻量、接近 OpenAlex 原生 API 的 Python 客户端
- 你最该借鉴的点：
  - OpenAlex 访问抽象
  - abstract 重建
  - `Work/Author/Source/Institution/Topic` 调用方式
  - PDF/TEI 内容获取能力
- 对 FARS 的价值：非常适合作为 MVP 阶段的 OpenAlex 接入层

#### 6) `FZJ-IEK3-VSA/citation-graph-builder`
- 作用：基于 `BibTeX + PDF + GROBID + bibliographic APIs` 构建 citation network
- 你最该借鉴的点：
  - “PDF 抽取 + API 增广” 的混合思路
  - 从不完整 PDF 引文中，借助外部 API 补齐 citation graph
  - 输出 GraphML/SVG 便于可视化
- 对 FARS 的价值：与你要做的“论文关系图”最接近

### P1：强烈建议参考

#### 7) `opencitations/index`
- 作用：OpenCitations 索引生产管线
- 对 FARS 价值：适合参考 citation index 的离线构建逻辑

#### 8) `opencitations/oc_meta`
- 作用：OpenCitations 的 bibliographic metadata 管理软件
- 对 FARS 价值：适合参考书目元数据治理、RDF/图谱化表达

#### 9) `dennybritz/papergraph`
- 作用：Semantic Scholar 语料 + Postgres + Hasura GraphQL 的 citation graph
- 对 FARS 价值：很适合作为图谱 API 和分析 notebook 的参考

#### 10) `eLifePathways/sciencebeam-parser`
- 作用：另一条结构化解析路线，支持 TEI/JATS/asset zip，且有 GROBID 兼容 API
- 对 FARS 价值：适合作为 `GROBID 替补 / 对照 / 增强解析器`

#### 11) `grobidOrg/grobid-client-python`
- 作用：并发、批处理、可转 JSON / Markdown 的 GROBID Python 客户端
- 对 FARS 价值：适合作为 MVP 的解析调度入口，而不是你自己直接拼 REST 请求

#### 12) `TIBHannover/orkg-backend`
- 作用：Open Research Knowledge Graph 的后端
- 对 FARS 价值：适合参考“如何把研究对象组织成知识图谱后端”

### P2：结构和工作流可借鉴，但不是论文知识层核心底座

#### 13) `SamuelSchmidgall/AgentLaboratory`
- 重点参考：多阶段研究 workflow、配置驱动实验、checkpoint 思路

#### 14) `LigphiDonk/Oh-my--paper`
- 重点参考：角色隔离、pipeline memory、hook 驱动、阶段式研究工作区

#### 15) `tarun7r/deep-research-agent`
- 重点参考：LangGraph 状态机、可信度评分、搜索缓存

#### 16) `mshumer/autonomous-researcher`
- 重点参考：实验分解与 GPU sandbox 概念

#### 17) `titipata/scipdf_parser`
- 重点参考：轻量 dict 输出、figure 提取、快速原型

#### 18) `papercast-dev/papercast`
- 重点参考：文档处理 pipeline / plugin 思路

#### 19) `MinhaoXiong/awesome-automated-research`
- 重点参考：继续扩充生态池，而非直接复用代码

## 5. 面向 FARS 论文知识层的复用地图

### A. 文献源接入层
建议重点参考：
- `pyalex`
- `paper-qa`
- `openalex-elastic-api`
- `openalex-guts`

适合借鉴的能力：
- OpenAlex works / authors / sources / topics 查询
- metadata enrichment
- related works / citations / similar works
- API 查询规范化

### B. PDF / 全文解析层
建议重点参考：
- `grobid`
- `grobid-client-python`
- `sciencebeam-parser`
- `scipdf_parser`

适合借鉴的能力：
- `PDF -> TEI`
- header / references / fulltext / citation contexts
- figure/table/坐标抽取
- 批量并发处理
- JSON / Markdown 派生输出

### C. 引文关系与图谱层
建议重点参考：
- `citation-graph-builder`
- `papergraph`
- `opencitations/index`
- `oc_meta`
- `orkg-backend`

适合借鉴的能力：
- citation graph 建模
- bibliographic metadata normalization
- graph query / GraphQL / OpenAPI
- 图谱持久化与数据生产流水线

### D. 研究工作流层
建议重点参考：
- `AgentLaboratory`
- `Oh-my--paper`
- `deep-research-agent`
- `autonomous-researcher`

适合借鉴的能力：
- research pipeline 分阶段组织
- 角色隔离
- 状态持久化
- 并发实验和资源约束

## 6. 当前建议的参考优先顺序

如果只允许深读 8 个项目，建议顺序如下：

1. `grobid`
2. `paper-qa`
3. `openalex-guts`
4. `openalex-elastic-api`
5. `pyalex`
6. `citation-graph-builder`
7. `papergraph`
8. `orkg-backend`

如果只允许先实现 MVP，并严格控制工程量，则优先：

1. `pyalex`
2. `paper-qa`
3. `grobid`
4. `grobid-client-python`
5. `citation-graph-builder`

## 7. 当前结论

对你当前目标“先做好论文知识层”来说，最值得直接吸收的不是某一个单体项目，而是一组组合：

- `pyalex + openalex-*`：负责学术元数据与检索
- `grobid + grobid-client-python`：负责结构化解析
- `paper-qa`：负责基于论文的 agentic retrieval 与证据组织
- `citation-graph-builder + papergraph + OpenCitations`：负责 citation / graph / enrichment
- `orkg-backend`：负责研究对象图谱后端的思路

也就是说，FARS 论文知识层更适合做成一个 `组合式系统`，而不是试图把某一个开源仓库直接改造成你的最终系统。

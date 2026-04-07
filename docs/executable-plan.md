# FARS 论文知识层可执行开发方案

日期：2026-04-08

## 1. 目标定义

当前阶段不实现完整 FARS，而是优先实现一个可独立工作的 `论文知识层`，供未来的 `Ideation / Planning / Experiment / Writing` 统一调用。

这个系统要解决四个核心问题：

1. `找得到`：多源检索相关论文、代码、数据集、基准
2. `拿得到`：拿到 metadata、PDF、TEI、引用信息、开放全文
3. `读得懂`：解析为结构化对象，而不只是纯文本
4. `连得清`：构建 citation graph 和更高阶语义关系图

## 2. 这一阶段的明确边界

### 本阶段要做

- 多源文献获取
- 论文归一化与去重
- PDF / TEI / 引文解析
- 统一数据模型
- citation graph
- 混合检索 API
- 论文详情页和图谱查询接口

### 本阶段不做

- 自动生成完整研究 hypothesis
- 自动运行大规模实验
- 自动写完整论文
- 多 worktree 并发调度落地实现

### 但要预留的能力

- research run 可以固定引用一个 `evidence snapshot`
- 后续 worktree 实验结果可以回写到知识层

## 3. 推荐技术路线

### 总体技术栈

- 语言：`Python 3.12`
- API：`FastAPI`
- 后台任务：`Celery 或 Arq`（MVP 推荐 `Arq + Redis`，实现快）
- 主数据库：`PostgreSQL 16`
- 向量检索：`pgvector`
- 对象存储：`MinIO / S3`
- 全文检索：MVP 先用 `Postgres FTS + pgvector`，后续再接 `OpenSearch`
- 论文解析：`GROBID` 主，`ScienceBeam` 备，`scipdf_parser` 做轻量 JSON 视图
- 学术元数据源：`OpenAlex` 主，`Crossref / Semantic Scholar / Unpaywall / OpenCitations` 辅
- 前端：MVP 可先不做完整前端，只做 API + 简单 graph page

### 为什么不先上 Neo4j

MVP 阶段不建议一开始就把图谱主存储放到 Neo4j：
- 运营复杂度高
- 大量业务数据其实是关系型 + 文档型
- citation graph 可以先用 edge table 跑起来

推荐策略：
- `Postgres` 作为 source of truth
- `paper_edge` 表承载图关系
- 如果后续图查询复杂，再镜像一份到 Neo4j

## 4. 系统架构

```text
                ┌──────────────────────────┐
                │     External Sources      │
                │ OpenAlex / Crossref /     │
                │ SemanticScholar /         │
                │ Unpaywall / OpenCitations │
                └────────────┬─────────────┘
                             │
                    ┌────────▼────────┐
                    │  Acquisition     │
                    │  Connectors      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Fetch & Sync    │
                    │ metadata/pdf/tei │
                    └────────┬────────┘
                             │
                ┌────────────▼────────────┐
                │ Parsing & Normalization │
                │ GROBID / ScienceBeam    │
                │ section/chunk/citation  │
                └────────────┬────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌────────▼────────┐   ┌──────▼───────┐
│ Postgres      │   │ Object Storage   │   │ Vector Index │
│ papers/edges  │   │ pdf/tei/assets   │   │ pgvector     │
└───────┬───────┘   └────────┬────────┘   └──────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Search & Graph   │
                    │ API Layer        │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Future Research  │
                    │ Agents / Runs    │
                    └──────────────────┘
```

## 5. 核心数据模型

### 5.1 Paper 级对象

#### `paper`
- `id`
- `canonical_title`
- `doi`
- `arxiv_id`
- `openalex_id`
- `semantic_scholar_id`
- `publication_year`
- `venue`
- `abstract`
- `language`
- `is_open_access`
- `citation_count`
- `retraction_status`
- `primary_source`

#### `paper_version`
- `id`
- `paper_id`
- `version_type` (`arxiv`, `conference`, `journal`, `camera_ready`, `unknown`)
- `source_url`
- `pdf_url`
- `tei_url`
- `checksum`
- `fetched_at`

### 5.2 结构化全文对象

#### `paper_section`
- `id`
- `paper_version_id`
- `section_type` (`abstract`, `intro`, `method`, `experiment`, `conclusion`, `references`, ...)
- `heading`
- `order_index`

#### `paper_chunk`
- `id`
- `section_id`
- `text`
- `page_start`
- `page_end`
- `bbox_json`
- `embedding`

#### `citation`
- `id`
- `source_paper_version_id`
- `target_paper_id`
- `raw_reference`
- `citation_key`
- `resolution_confidence`

#### `citation_context`
- `id`
- `citation_id`
- `chunk_id`
- `context_text`
- `context_type` (`background`, `comparison`, `extension`, `critique`, `unknown`)

### 5.3 研究对象实体

#### `method`
- `id`
- `name`
- `aliases`

#### `dataset`
- `id`
- `name`
- `aliases`

#### `metric`
- `id`
- `name`
- `aliases`

#### `experiment_result`
- `id`
- `paper_id`
- `method_id`
- `dataset_id`
- `metric_id`
- `value`
- `split`
- `raw_evidence_chunk_id`

### 5.4 图关系

#### `paper_edge`
- `id`
- `src_paper_id`
- `dst_paper_id`
- `edge_type`
- `confidence`
- `evidence_chunk_id`
- `source`

`edge_type` 初始支持：
- `cites`
- `extends`
- `compares`
- `contradicts`
- `reproduces`
- `uses_dataset`
- `proposes_method`
- `reports_result_against`

## 6. 数据流设计

### 6.1 多源文献获取流

```text
用户输入 topic
 -> topic expansion
 -> OpenAlex search
 -> Crossref / Semantic Scholar / OpenCitations enrichment
 -> canonicalize identifiers
 -> upsert paper
 -> enqueue fetch jobs
```

### 6.2 全文获取流

优先级：
1. OpenAlex 可直接给的 PDF / TEI
2. DOI landing page / Unpaywall OA URL
3. 本地上传 PDF
4. 仅 metadata 入库，等待后续补抓

### 6.3 解析流

```text
PDF/TEI 入库
 -> choose parser
    - primary: GROBID
    - fallback: ScienceBeam
 -> store raw TEI/JATS/XML
 -> normalize to internal schema
 -> split sections/chunks
 -> resolve references
 -> build citation + citation_context
 -> embed chunks
```

### 6.4 图谱构建流

```text
reference list resolved
 + citation context extracted
 + metadata enrichment
 -> build cites edges
 -> infer semantic edges
 -> persist edge evidence
```

## 7. 与开源项目的映射关系

### 获取与 metadata
- `pyalex`
- `paper-qa/src/paperqa/clients/*`
- `openalex-guts`
- `openalex-elastic-api`

### 结构化解析
- `grobid`
- `grobid-client-python`
- `sciencebeam-parser`
- `scipdf_parser`

### 图谱与关系
- `citation-graph-builder`
- `papergraph`
- `opencitations/index`
- `oc_meta`
- `orkg-backend`

### 上层工作流接口
- `AgentLaboratory`
- `Oh-my--paper`
- `deep-research-agent`

## 8. MVP API 设计

### 检索接口
- `POST /topics/expand`
- `GET /papers/search`
- `GET /papers/{id}`
- `GET /papers/{id}/versions`
- `GET /papers/{id}/citations`
- `GET /papers/{id}/references`
- `GET /papers/{id}/graph`

### 获取与同步接口
- `POST /ingest/topic`
- `POST /ingest/paper`
- `POST /fetch/paper/{id}`
- `POST /parse/paper/{version_id}`
- `POST /enrich/paper/{id}`

### 图谱接口
- `GET /graph/papers/{id}/neighbors`
- `GET /graph/lineage`
- `GET /graph/conflicts`
- `GET /graph/baselines`

### Agent 使用接口
- `POST /agent/evidence-pack`
- `POST /agent/novelty-check`
- `POST /agent/topic-landscape`

## 9. MVP 页面 / 可视化

至少要有：

### 页面 1：Paper Detail
- 基础 metadata
- abstract
- parsed sections
- references / citations
- datasets / methods / metrics
- evidence snippets

### 页面 2：Citation Graph
- 中心论文
- 被引 / 引用邻居
- edge type 过滤
- 年份过滤
- 展开局部子图

### 页面 3：Topic Landscape
- topic 下核心论文
- 代表方法
- 常用数据集
- 常用 metric
- 争议点 / 冲突结果

## 10. 目录结构建议

```text
FARS/
  docs/
  services/
    api/
    worker/
  libs/
    connectors/
      openalex/
      crossref/
      semanticscholar/
      opencitations/
    parsers/
      grobid/
      sciencebeam/
      scipdf/
    normalization/
    graph/
    retrieval/
  infra/
    docker/
    migrations/
  data/
    samples/
    schemas/
```

## 11. 开发阶段划分

### Phase 0：文档与样例固化
- 完成参考项目索引
- 完成架构设计
- 准备 20~50 篇论文样本集

### Phase 1：Metadata 基础层
- 接 OpenAlex
- 做 paper canonicalization
- 建 paper / version / identifier 表
- 跑 topic ingest

### Phase 2：解析层
- 集成 GROBID
- 打通 grobid-client-python
- 存 raw PDF / TEI / normalized JSON
- 提取 sections / references / chunks

### Phase 3：检索与图谱层
- pgvector + FTS
- citation edges
- paper detail API
- citation graph API

### Phase 4：研究对象抽取
- method / dataset / metric 基础抽取
- result 结构化抽取
- graph edge enrichment

### Phase 5：面向 agent 的能力封装
- evidence pack
- topic landscape
- baseline discovery
- novelty check v1

## 12. 未来与 worktree 并发层的接口预留

未来 worktree 并发层接入时，知识层应这样衔接：

### run 输入
每个 research run 在开始时固定：
- `topic_id`
- `paper snapshot ids`
- `evidence pack version`

### run 输出
每个 run 完成后回写：
- 新实验结果
- 新 claim
- 对已有 paper edge 的支持 / 反驳证据

### 为什么不能把知识层放进 worktree
- worktree 适合隔离代码和实验产物
- 不适合承载共享文献库、向量索引和图谱状态
- 否则并发下会产生重复下载、重复 embedding、重复解析

所以建议：
- `知识层共享`
- `实验 worktree 隔离`
- `结果通过 API 回写`

## 13. 当前的开发决策

### 决策 1：MVP 以 OpenAlex 为主元数据源
原因：
- 覆盖广
- 实体类型丰富
- 有 works/authors/sources/topics/related works
- 有 Python 客户端 `pyalex`

### 决策 2：MVP 以 GROBID 为主解析器
原因：
- 论文结构解析最成熟
- citation context 非常关键
- 有生产级服务模式和 Python client

### 决策 3：MVP 图谱主存储先用 Postgres edge table
原因：
- 开发速度快
- 运维简单
- 后续可镜像到 Neo4j

### 决策 4：MVP 先不做复杂语义边自动抽取
原因：
- `extends / contradicts / compares` 质量要求高
- 应在 citation/context 基础稳定后再上

## 14. 开始编码前的门槛

只有当以下条件都满足，再开始实际编码：

- [x] 参考项目已搜集并 clone
- [x] 已形成项目索引
- [x] 已形成阅读笔记
- [x] 已形成可执行方案
- [ ] 样本论文集准备完成
- [ ] 选定 MVP 第一个 topic domain（建议先 AI/ML）
- [ ] 确认存储方案（Postgres + pgvector + MinIO）
- [ ] 确认 GROBID 运行方式（docker service）

## 15. 一句话结论

当前最稳的执行路径不是“先写一个 agent”，而是先做一个：

`OpenAlex + GROBID + Postgres/pgvector + citation edge model` 的论文知识层 MVP。

这会为未来真正的 FARS 自动科研流水线提供可靠底座。

# FARS 统一总览：需求、设计、实现、架构、用法、参考项目

日期：2026-04-09  
项目路径：`/Users/admin/ai/self-dev/FARS`

---

## 1. 这份文档是干什么的

这是一份**单文档总览**，把下面几类信息放到一起：

1. 你的需求
2. 当前产品定位
3. 我的设计思路
4. 当前已经实现的功能
5. 当前系统架构
6. 当前怎么用
7. 参考过的开源项目
8. 当前边界与下一步

如果你现在要继续开发、切换会话、交接给别的 agent，优先先看这一份。

---

## 2. 你的核心需求

你的目标不是做一个普通的论文搜索工具，而是做一个未来自动科研系统的底座。

你的需求可以归纳成 7 点：

### 2.1 先做论文知识层

- 先不要一上来做完整 autonomous scientist
- 先把 `paper knowledge layer` 做稳
- 让后面的 ideation / planning / experiment / writing 都建立在这个底座上

### 2.2 重点优化论文获取

你特别强调要把论文获取做好，包括：

- 多源元数据获取
- 全文获取
- 版本归一化
- 开放获取能力

### 2.3 重点优化论文解析

你特别强调要把解析做好，包括：

- section
- chunk
- citation
- citation context
- 方法 / 数据集 / 指标
- 结果抽取

### 2.4 把论文和论文的关系讲清楚

你要的不只是“有引用数”，而是：

- 哪篇论文引用哪篇论文
- 为什么引用
- 引用上下文是什么
- 是否是 compare / extend / contradict 之类关系
- 最终能以图结构表达出来

### 2.5 单条流水线先跑通，再做并发

你明确说过：

- 先把完整流程跑通
- worktree / 多分支并发是下一层
- 共享知识层不能和隔离执行层混在一起

### 2.6 不是纯后端，要有可展示页面

你后面明确补充过：

- 不能只是 backend
- 要有页面
- 最好和线上公开版 FARS 的感觉接近

### 2.7 参考 FARS，但不能空想

你要求必须：

- 多轮搜索类似开源项目
- clone 到本地阅读
- 总结成开发文档
- 让后续 agent 都必须参考这些结论

一句话总结你的需求：

> 先做一个强论文知识层 + 可展示前端 + 可衔接自动科研流水线的研究操作系统底座。

---

## 3. 当前产品定位

当前这个仓库不是“完整 FARS 复制品”，而是：

> 一个以 `paper knowledge layer` 为核心、已经接上 run / artifact / graph / public UI / operator UI 的本地优先研究系统底座。

当前定位是：

### 3.1 对外

- `/fars` = public/live view
- 像公开展示页
- 更强调运行状态、部署展示、public progress

### 3.2 对内

- `/console` = operator console
- 更强调：
  - run
  - batch run
  - reconcile
  - graph inspect
  - paper inspect

### 3.3 对未来自动科研系统

它已经不是空壳，而是已经具备：

- 论文 ingest
- 解析
- 图谱
- snapshot
- run
- artifact
- report / paper draft
- batch orchestration
- worktree-ready execution surface

---

## 4. 我的设计思路

### 4.1 设计原则一：先知识层，后科研代理

先做：

- metadata
- paper canonicalization
- parsing
- graph
- evidence pack
- snapshot

再做：

- hypothesis
- planning
- experiment
- writing

### 4.2 设计原则二：共享知识，隔离执行

我按你强调的方向采用：

- `knowledge shared`
- `execution isolated`

也就是说：

- 论文、图谱、evidence、snapshot 放共享层
- run、artifact、未来 worktree 执行放隔离层

### 4.3 设计原则三：public view 和 operator view 分离

为了更贴近线上版本，又不丢失工程能力：

- `/fars`：public/live presentation
- `/console`：operator workflows

这避免了把内部调试入口塞进公开页里。

### 4.4 设计原则四：本地优先验证

当前实现尽量满足：

- 本地可跑
- 本地可测试
- 不依赖外部付费 API 才能过验证

### 4.5 设计原则五：参考项目驱动，而不是空想

设计不是拍脑袋，而是吸收了这些方向的项目 DNA：

- `grobid`：论文结构化解析
- `paper-qa`：证据导向 retrieval
- `pyalex / openalex-*`：学术元数据与检索
- `citation-graph-builder / papergraph / OpenCitations`：图谱与引用关系
- `AgentLaboratory / Oh-my--paper / autonomous-researcher / autoresearch`：研究流水线、执行闭环、公开展示感

---

## 5. 当前系统架构

## 5.1 包与目录

### canonical 实现

- `src/fars_kg/`

这是当前真正的主系统，包括：

- config
- db
- models
- schemas
- routes
- services
- migrations
- worktree manager

### compat / demo 层

- `src/fars/`

这是兼容层，不是未来主要扩展面。

### 规格与状态

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`

### 参考文档

- `docs/project-index.md`
- `docs/repo-reading-notes.md`
- `docs/executable-plan.md`

---

## 5.2 逻辑分层

```text
Public UI (/fars)
        │
Operator UI (/console)
        │
FastAPI API Layer
        │
Services / Repository Layer
        │
Database / Artifact / Worktree / Parser / Metadata Connectors
```

具体拆分：

### A. 获取层

- topic ingestion
- metadata adapters
- paper canonicalization
- version persistence

### B. 解析层

- parser abstraction
- sections
- chunks
- citations
- citation contexts

### C. 图谱层

- citation edges
- semantic edges
- graph explanations
- graph neighbors

### D. evidence / workflow 层

- evidence packs
- snapshots
- research runs
- experiment plans
- experiment tasks
- iterations
- artifact bundles

### E. 展示层

- `/fars`
- `/console`

---

## 5.3 端到端链路

当前系统已经能走通：

```text
Topic
  -> ingest papers
  -> parse versions
  -> enrich semantics
  -> infer graph edges
  -> build evidence snapshot
  -> create research run
  -> generate hypotheses/plans/tasks
  -> execute deterministic iterations
  -> write results
  -> generate report/paper draft
  -> export artifact bundle
```

这条链路现在已经不是设计稿，而是有本地验证的实现。

---

## 6. 当前已经实现的功能

## 6.1 论文与元数据

- topic ingestion
- canonical paper persistence
- paper version persistence
- OpenAlex 风格标识整合
- search API

## 6.2 结构化解析

- parser abstraction
- sections
- chunks
- citations
- citation contexts
- context type classification

## 6.3 图谱能力

- citation graph
- semantic edge inference
- graph neighbors
- graph explanations
- mermaid export（API 仍保留）

## 6.4 语义对象

- methods
- datasets
- metrics
- manual enrichment
- auto enrichment from parsed text
- auto result extraction

## 6.5 运行态与自动 loop

- evidence packs
- snapshots
- research runs
- hypothesis generation
- experiment plan generation
- experiment task generation
- deterministic local execution
- multi-iteration loop
- report generation
- paper draft generation
- SVG figure generation
- artifact bundle generation
- event log export

## 6.6 并发 / worktree 面

- git worktree manager
- batch orchestration
- batch artifact bundle
- batch reconcile

## 6.7 生产化能力

- request ID
- request logging
- health / readiness / system info
- Alembic bootstrap
- migration scripts
- artifact manifest + checksums

## 6.8 前端与页面

### `/fars`

public/live view：

- hero
- deployments
- research runs
- latest run events
- last-updated indicator
- visible-count pills（deployments / runs / events）
- refresh cadence + countdown indicator（15s live refresh）
- mobile menu sheet
- footer
- public copy rhythm
- self-contained hero asset

### `/console`

operator view：

- single run
- batch run
- continue run（auto experiment continuation）
- Codex LLM config controls（profile/model/reasoning）
- reconcile
- paper explorer
- graph viewer
- runs/batches inspection

## 6.9 operator boundary

现在支持：

- `FARS_OPERATOR_TOKEN`
- `/console` 登录
- operator cookie session
- `X-FARS-Operator-Token` header
- 当开启 token 时：
  - `/fars` 保持公开
  - `/fars/data` 保持公开
  - `/fars/events` 保持公开（脱敏事件流）
  - operator API 被保护

而且 `/fars/data` 已做脱敏，不再暴露：

- branch_name
- full summary
- has_artifact
- deployment exists

---

## 7. 当前怎么用

## 7.1 安装与启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

启动：

```bash
uvicorn fars_kg.api.app:app --reload
```

---

## 7.2 页面入口

### 公共页

```text
http://127.0.0.1:8000/fars
```

### operator console

```text
http://127.0.0.1:8000/console
```

---

## 7.3 如果要开启 operator 保护

在环境变量里设置：

```bash
FARS_OPERATOR_TOKEN=your-secret-token
```

此时：

- `/fars` 仍可公开访问
- `/fars/data` 仍可公开访问
- `/console` 会要求登录
- 受保护 API 需要 token

---

## 7.4 常用脚本

### 本地端到端

```bash
python scripts/run_local_e2e_flow.py
```

### 自动 research loop

```bash
python scripts/run_autonomous_research_loop.py
```

### batch loop

```bash
python scripts/run_batch_research_loop.py
```

### 导出 OpenAPI

```bash
python scripts/export_openapi.py
```

### 数据库迁移

```bash
python scripts/db_upgrade.py
python scripts/db_current.py
```

---

## 7.5 常用 Makefile

```bash
make test
make run
make loop
make batch-loop
make db-upgrade
make db-current
```

---

## 8. 当前关键 API

## 8.1 公共 / 基础

- `GET /api/health`
- `GET /api/health/readiness`
- `GET /api/system/info`
- `GET /fars/data`
- `GET /fars/events`

## 8.2 论文与图谱

- `POST /api/topics/ingest`
- `GET /api/papers/search`
- `GET /api/papers/{paper_id}`
- `GET /api/papers/{paper_id}/sections`
- `GET /api/papers/{paper_id}/citations`
- `GET /api/graph/papers/{paper_id}/neighbors`
- `GET /api/graph/papers/{paper_id}/explanations`
- `GET /api/graph/papers/{paper_id}/mermaid`

## 8.3 enrichment / evidence

- `POST /api/papers/{paper_id}/semantic-enrichment`
- `POST /api/papers/{paper_id}/semantic-enrichment/auto`
- `GET /api/papers/{paper_id}/evidence-pack`
- `GET /api/topics/landscape`

## 8.4 run / workflow

- `POST /api/papers/{paper_id}/snapshots`
- `POST /api/runs`
- `POST /api/runs/{run_id}/result`
- `POST /api/runs/{run_id}/experiment-results`
- `POST /api/runs/{run_id}/experiment-results/auto`
- `GET /api/runs/{run_id}/events`
- `POST /api/research-loops/run`（支持 `llm_profile` / `llm_model` / `llm_reasoning_effort`）
- `POST /api/research-loops/{run_id}/continue`（支持 `llm_profile` / `llm_model` / `llm_reasoning_effort`）

## 8.5 batch / reconcile

- `POST /api/research-loops/batch-run`（支持 `llm_profile` / `llm_model` / `llm_reasoning_effort`）
- `POST /api/research-loops/reconcile`
- `GET /api/research-loops/batches`
- `GET /api/research-loops/batches/{batch_id}/manifest`
- `GET /api/research-loops/batches/{batch_id}/download`
- `GET /api/research-loops/batches/{batch_id}/summary/download`
- `GET /api/research-loops/batches/{batch_id}/items/download`
- `GET /api/research-loops/batches/{batch_id}/reconciliation/download`

---

## 9. 你的需求 vs 我的设计 vs 当前实现

## 9.1 已对齐的部分

### 需求：先做论文知识层

已对齐：

- 当前系统主轴就是 `fars_kg`
- 不是先做完整 scientist UI/agent 幻觉壳

### 需求：优化论文获取与解析

已对齐：

- ingest
- canonicalization
- parsing abstraction
- citation/context persistence

### 需求：把论文关系讲清楚

已对齐：

- graph neighbors
- explanations
- citation contexts
- semantic edges

### 需求：以后支持 worktree / 并发

已对齐：

- worktree manager 已有
- batch orchestration 已有
- batch artifact / reconcile 已有

### 需求：不是纯后端，要有页面

已对齐：

- `/fars`
- `/console`

---

## 9.2 还没有完全做满的部分

这些不是没做，而是还没做到你最终想要的“生产级完整自动科研系统”：

### A. 更强的研究语义理解

- 更强 semantic relation extraction
- 更强 claim/result extraction
- 更强 research lineage tracing

### B. 更强的真实实验执行

- 当前 deterministic local execution 已有
- 真实 benchmark / training backend 还需要继续补

### C. 更强的 worktree 并发执行层

- 目前是 local orchestration + interface 完成度较高
- 真正大规模并行 executor 仍可继续深化

### D. 更像线上版本的前端细节

- 当前已明显靠近线上 public/live page
- 但还没有做到 pixel-perfect clone

---

## 10. 参考过的开源项目

下面这些项目是当前设计和实现的重要参考来源。

## 10.1 论文获取 / 元数据 / 学术检索

### `J535D165/pyalex`

- 作用：OpenAlex Python 客户端
- 参考点：
  - work / author / venue / topic 查询
  - 学术元数据接入抽象

### `ourresearch/openalex-guts`

- 作用：OpenAlex 数据建模与处理底座
- 参考点：
  - scholarly entity model
  - paper/topic/affiliation 等拆分思路

### `ourresearch/openalex-elastic-api`

- 作用：OpenAlex API 与检索层
- 参考点：
  - search / filter / semantic search / cursor 分层

---

## 10.2 论文解析 / 全文结构化

### `grobidOrg/grobid`

- 作用：学术 PDF 结构化解析事实标准之一
- 参考点：
  - TEI XML
  - citation context
  - fulltext parse

### `grobidOrg/grobid-client-python`

- 作用：GROBID 的并发 Python 客户端
- 参考点：
  - 工程调度入口

### `eLifePathways/sciencebeam-parser`

- 作用：另一条学术文档结构化路线
- 参考点：
  - parser abstraction
  - 备选解析后端

### `titipata/scipdf_parser`

- 作用：轻量学术 PDF dict 输出
- 参考点：
  - 对外轻量 JSON 视图

---

## 10.3 引文图谱 / 学术知识图谱

### `FZJ-IEK3-VSA/citation-graph-builder`

- 作用：论文引用网络构建
- 参考点：
  - paper-to-paper relation
  - graph export

### `dennybritz/papergraph`

- 作用：citation graph + graph API
- 参考点：
  - graph query 表达

### `opencitations/index`

- 作用：OpenCitations 索引生产
- 参考点：
  - citation index pipeline

### `opencitations/oc_meta`

- 作用：bibliographic metadata management
- 参考点：
  - metadata 治理与图谱化思路

### `TIBHannover/orkg-backend`

- 作用：Open Research Knowledge Graph 后端
- 参考点：
  - scholarly KG backend 组织方式

---

## 10.4 自动科研 / research workflow / public 展示

### `SamuelSchmidgall/AgentLaboratory`

- 参考点：
  - research workflow 分阶段组织
  - config-driven execution

### `LigphiDonk/Oh-my--paper`

- 参考点：
  - research workspace
  - 多阶段 research pipeline
  - session context 注入

### `mshumer/autonomous-researcher`

- 参考点：
  - 并发实验
  - 隔离执行

### `tarun7r/deep-research-agent`

- 参考点：
  - planner / searcher / writer 状态机

### `karpathy/autoresearch`
### `uditgoenka/autoresearch`

- 参考点：
  - 自动研究 loop 的 execution cadence
  - 迭代式评估与写作风格

---

## 11. 当前文档与参考入口

如果你要继续推进，建议按下面顺序阅读：

1. `docs/2026-04-09-fars-unified-overview.md`（本文件）
2. `docs/project-index.md`
3. `docs/repo-reading-notes.md`
4. `docs/executable-plan.md`
5. `.planning/PROJECT.md`
6. `.planning/STATE.md`

---

## 12. 当前一句话状态

> 当前 FARS 已经从“需求分析”进入到“可运行、可展示、可验证、可扩展”的知识层底座阶段：公共页 `/fars`、操作台 `/console`、论文知识层、run/batch/reconcile、artifact 与 operator boundary 都已经落地，并且具备本地验证能力。

# FARS：需求、设计与实现总览

日期：2026-04-08  
项目路径：`/Users/admin/ai/self-dev/FARS`

---

## 1. 你的核心需求

你当前要做的不是普通论文 RAG，而是一个未来自动科研系统的 `paper knowledge layer` 底座。

你的需求可以概括为：

1. **先做论文知识层**
   - 先不要急着做完整自动科研闭环
   - 先把论文系统做强、做稳、做可追溯

2. **重点优化论文获取与解析**
   - 多源论文获取
   - 元数据归一化
   - PDF / 全文解析
   - 结构化 section / chunk / citation / context

3. **把论文与论文之间的关系讲清楚**
   - 不只是 citation count
   - 要有 graph 结构
   - 最好能看到 raw reference、citation context、edge type

4. **后续支持并发 worktree 流水线**
   - 但前提是单条流水线和共享知识层先跑通
   - worktree 只做隔离执行，不要承载共享知识状态

一句话：

> 你要的是一个可作为未来自动科研系统底座的“论文知识操作系统”。

---

## 2. 设计原则

当前设计严格围绕你的需求收敛，采用以下原则：

### 2.1 先知识层，后科学家代理

- 先实现共享论文知识层
- 再接 ideation / planning / experiment / writing

### 2.2 共享知识，隔离实验

- `knowledge is shared`
- `experiments are isolated`

也就是：
- 知识库、图谱、snapshot、evidence pack 是共享的
- worktree、实验日志、执行产物是隔离的

### 2.3 参考项目驱动设计

不是凭空设计，而是从参考项目里吸收 DNA：

- `grobid`：结构化 PDF/TEI/citation context
- `paper-qa`：evidence-oriented retrieval
- `pyalex / openalex-*`：学术元数据与检索
- `citation-graph-builder / papergraph / OpenCitations`：citation graph 与图谱建模
- `Oh-my--paper / AgentLaboratory / autonomous-researcher`：共享事实层 + 隔离执行层

### 2.4 本地优先验证

- 所有当前实现必须在本地可验证
- 不依赖外部 API key 才能通过测试
- 先用 fake client / fake parser 跑完整链路

---

## 3. 当前架构设计

当前仓库已经明确分层：

### 3.1 canonical 包

- `src/fars_kg/`

这是当前真正的主实现，包含：
- 数据模型
- 数据库层
- API
- repository/service
- parser adapter
- metadata adapter
- worktree manager

### 3.2 compat/demo 包

- `src/fars/`

这是兼容/示例层：
- 保留旧测试/seed-data/demo 入口
- 不是未来主要扩展面

### 3.3 规格管理

通过 GSD 管理：

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`

### 3.4 agent 约束

通过仓库级 `AGENTS.md` 约束：
- agent 编码前必须先阅读参考项目结论和设计文档

---

## 4. 当前已经实现的能力

以下内容已经落地：

### 4.1 元数据与论文对象

- topic ingestion
- canonical paper persistence
- paper version persistence
- DOI / OpenAlex 等标识整合

### 4.2 结构化解析

- parser abstraction
- parsed sections
- parsed chunks
- citations
- citation contexts
- automatic citation-context classification

### 4.3 图谱能力

- citation edges
- semantic edges（当前为轻量启发式）
- graph neighbor API
- Mermaid graph export
- explainable graph API
- explainable graph API

### 4.4 语义对象

- methods
- datasets
- metrics
- manual semantic enrichment
- automatic semantic enrichment from parsed text
- automatic experiment-result extraction from parsed text

### 4.5 运行态能力

- evidence packs
- snapshots
- research runs
- automatic hypothesis generation
- automatic experiment plan generation
- automatic experiment task generation
- deterministic experiment execution iterations
- multiple task types with runner dispatch
- automatic research report generation
- dynamic SVG figure generation for reports/drafts
- configurable multi-iteration autonomous looping
- result writeback
- run artifact bundle generation
- run audit events / events.jsonl export
- request ID headers and runtime request logging controls
- Alembic migration/bootstrap support for production startup
- full paper-draft section coverage
- artifact manifest/checksum generation
- run audit event generation / export
- request-id based runtime tracing
- automatic experiment-result extraction
- paper-level result stats
- topic-level result stats
- autonomous research loop（deterministic / local-first / no-worktree default）

### 4.6 worktree 相关

- real git worktree manager 已实现
- 但当前完整流程验证默认仍以 **不跑 worktree** 为主

---

## 5. 当前暴露的关键 API

### 论文与检索

- `POST /api/topics/ingest`
- `GET /api/papers/search`
- `GET /api/papers/{paper_id}`
- `GET /api/papers/{paper_id}/sections`
- `GET /api/papers/{paper_id}/citations`
- `GET /api/papers/{paper_id}/results`

### 图谱

- `GET /api/graph/papers/{paper_id}/neighbors`
- `GET /api/graph/papers/{paper_id}/mermaid`
- `GET /api/graph/papers/{paper_id}/explanations`
- `POST /api/graph/papers/{paper_id}/infer-semantic-edges`

### enrichment / evidence

- `POST /api/papers/{paper_id}/semantic-enrichment`
- `POST /api/papers/{paper_id}/semantic-enrichment/auto`
- `GET /api/papers/{paper_id}/evidence-pack`
- `GET /api/topics/landscape`

### run / snapshot / execution

- `POST /api/papers/{paper_id}/snapshots`
- `GET /api/snapshots/{snapshot_id}`
- `POST /api/runs`
- `POST /api/runs/{run_id}/result`
- `POST /api/runs/{run_id}/experiment-results`
- `POST /api/runs/{run_id}/experiment-results/auto`
- `GET /api/runs/{run_id}/events`
- `GET /api/runs/{run_id}/execution-manifest`
- `POST /api/runs/{run_id}/worktree`
- `POST /api/research-loops/run`
- `GET /api/health`
- `GET /api/health/readiness`
- `GET /api/system/info`

---

## 6. 当前最关键的“对齐结果”

### 已经和你的需求对齐的部分

- 先做知识层，而不是完整自动科研系统
- 强化论文获取与解析
- 能把论文关系图清楚表示出来
- 支持 evidence pack / snapshot / run
- 未来能接 worktree 并发，但不让 worktree 持有知识状态

### 还没有完全做满的部分

- 更强的 semantic relation inference
- 更强的自动结果抽取
- 更复杂的研究脉络与 baseline 分析
- 完整 scientist loop

---

## 7. 当前验证状态

### 7.1 全量测试

当前仓库验证结果：

```bash
pytest -q
```

结果：

```text
34 passed, 1 warning
```

### 7.2 无 worktree 整流程

当前已经可以实际运行：

```bash
source .venv/bin/activate
python scripts/run_local_e2e_flow.py
```

输出示例：

```text
E2E flow completed without worktree
{'paper_id': 1, 'version_id': 1, 'snapshot_id': 1, 'run_id': 1, 'neighbors': 2, 'methods': ['Transformer'], 'landscape_methods': ['Transformer'], 'result_count': 1}
```

这说明当前已经跑通：

`ingest -> parse -> semantic enrichment -> semantic edge inference -> evidence pack -> landscape -> snapshot -> run -> result writeback`

当前 API 还会为每个请求返回 `X-Request-ID`，并为每个 research run 生成可追溯的 event log，artifact bundle 中包含 `events.jsonl`。

此外，当前还可以直接跑自动科研 loop：

```bash
source .venv/bin/activate
python scripts/run_autonomous_research_loop.py
```

---

## 8. 当前最推荐的使用方式

### 启动 canonical API

```bash
cd /Users/admin/ai/self-dev/FARS
source .venv/bin/activate
uvicorn fars_kg.api.app:app --reload
```

### 查看 topic landscape

```bash
curl "http://127.0.0.1:8000/api/topics/landscape?q=paper"
```

### 查看解释型图关系

```bash
curl "http://127.0.0.1:8000/api/graph/papers/1/explanations"
```

### 跑无 worktree 整流程

```bash
python scripts/run_local_e2e_flow.py
```

---

## 9. 结论

当前这个项目已经不再只是“需求分析”或“文档设计”，而是：

> 一个已经具备论文知识层核心能力、可本地运行、可测试、可继续扩展的 FARS 底座。

如果继续做，最自然的下一步方向是：

1. 增强 semantic relation inference  
2. 增强自动 result extraction  
3. 增强 topic landscape 的研究脉络分析  
4. 再把这些能力接给更上层的 researcher agents

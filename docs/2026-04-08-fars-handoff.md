# FARS Handoff

日期：2026-04-08
工作目录：`/Users/admin/ai/self-dev/FARS`

## 1. 用户目标

用户希望实现一个类似 `FARS` 的自动科研系统，并先完成需求收敛与参考项目调研。

当前已确认的核心目标：

1. 以 `Analemma FARS (Fully Automated Research System)` 为参考对象进行产品和系统设计。
2. 优先建设 `论文知识层`，而不是先做完整的自动科研流水线。
3. 重点优化以下能力：
   - 论文多源获取
   - 论文全文获取
   - 论文结构化解析
   - 论文之间的引用关系和语义关系梳理
   - 论文图谱可视化，尤其是图结构表达
4. 后续要支持 `git worktree / 多工作树` 风格的并发执行，使系统可以在单条流水线跑通后并发探索多个研究分支。
5. 需要多轮搜索相似开源项目，尤其是：
   - 自动科研 / Research Agent
   - 论文解析 / PDF 结构化
   - 引文图谱 / 学术知识图谱
6. 需要把高相关参考仓库 clone 到：
   - `/Users/admin/ai/lunwen/ref`
7. clone 完后需要继续阅读这些项目，生成两类文档并作为开发参考：
   - 项目索引文档
   - 可执行开发文档

## 2. 对需求的当前理解

这个项目本质上不是一个普通的“论文 RAG”，而是一个偏 `Research OS` 的系统。

系统应分成三层主能力：

1. `论文知识层`
   - 负责检索、获取、解析、去重、归一化、索引、图谱构建
   - 是当前最高优先级
2. `自动科研编排层`
   - 负责 hypothesis、planning、experiment、review、writing
   - 先不优先实现，但架构上要预留接口
3. `并发执行层`
   - 负责 worktree、任务隔离、资源调度、结果回收
   - 是后续阶段重点

当前对论文知识层的定义：

- 不只是“下载 PDF + RAG”
- 要把论文变成结构化对象
- 要表达论文与论文、论文与方法、论文与数据集、论文与指标之间的图关系
- 要让上层 agent 能基于证据工作，而不是仅靠模糊摘要

## 3. 已确认的产品优先级

### P0

- 论文多源检索
- 论文去重与实体归一
- 全文获取
- 基础结构化解析
- citation graph
- 面向 agent 的检索接口

### P1

- method / dataset / metric 抽取
- 论文语义关系边：
  - `extends`
  - `compares`
  - `contradicts`
  - `reproduces`
- 图谱查询与可视化

### P2

- novelty check
- research lineage tracing
- 与多 worktree 并发实验层打通

## 4. 本轮已完成的分析结论

### 4.1 FARS 目标对象已确认

已确认用户说的 `FARS` 指的是 Analemma 的：

- `Fully Automated Research System`

已确认的官方公开信息：

- `2026-02-11` 发布介绍文章
- `2026-02-13` 开始首个公开部署
- `2026-03-03` 官方更新称直播结束

从公开资料中已归纳出的 FARS 关键能力：

- `Ideation -> Planning -> Experiment -> Writing` 多智能体科研流水线
- 研究方向输入后自动展开 hypothesis
- 自动检索论文与代码
- 自动筛选候选研究假设
- 自动执行实验
- 自动产出 short paper
- 共享文件系统协作
- 并发项目支持
- 公开部署页展示 run / paper / code / review
- 对外发布前有人类研究员复核

### 4.2 对论文知识层的需求判断

已明确判断：

- 当前最优先做的是 `论文知识层`
- 不是先做完整多 agent 科研系统
- worktree 并发是第二阶段核心，但不是当前第一落点

## 5. 当前助手任务

当前需要继续执行的任务如下：

1. 多轮检索与筛选和 FARS 方向相似的开源项目
2. 检索范围必须覆盖三类：
   - 自动科研 agent / research workflow
   - 论文获取与论文解析
   - 引文图谱 / 学术知识图谱 / 学术元数据
3. 把高相关仓库 clone 到 `/Users/admin/ai/lunwen/ref`
4. 阅读这些仓库的 README、目录结构和关键模块
5. 在当前 FARS 工作区生成文档：
   - `project-index.md`
   - `executable-plan.md`
6. 后续开发优先聚焦论文知识层，并预留与 worktree 并发层的接口

## 6. 当前搜索状态

### 6.1 搜索方式

已使用：

- 网页搜索
- `gh search repos`
- `omx` / `opencode` 本地命令探测

### 6.2 已发现的高相关候选项目

#### 自动科研 / 研究代理方向

- `SamuelSchmidgall/AgentLaboratory`
- `mshumer/autonomous-researcher`
- `LigphiDonk/Oh-my--paper`
- `tarun7r/deep-research-agent`
- `MinhaoXiong/awesome-automated-research`
- `allenai/discoveryworld`

#### 论文解析 / 全文结构化方向

- `grobidOrg/grobid`
- `grobidOrg/grobid-client-python`
- `eLifePathways/sciencebeam-parser`
- `titipata/scipdf_parser`
- `ourresearch/openalex-pdf-parser`

#### 学术元数据 / 学术图谱 / OpenAlex 方向

- `J535D165/pyalex`
- `ourresearch/openalex-guts`
- `ourresearch/openalex-elastic-api`
- `ourresearch/OpenAlex`
- `ourresearch/openalex-api-tutorials`

### 6.3 当前搜索判断

当前候选池已经具备明显参考价值，但还没有完成最终筛选和 clone。

当前需要继续补的检索方向：

- paper knowledge graph
- citation context extraction
- semantic citation / scientific claim extraction
- scientific literature graph
- research object graph

## 7. 当前环境与执行状态

### 7.1 工作区状态

当前目录状态：

- `/Users/admin/ai/self-dev/FARS` 目前基本为空
- 目前仅看到：
  - `.omx`
  - `docs/`

### 7.2 GitHub 搜索状态

已确认：

- `gh search repos` 可以使用
- 之前在 sandbox 下因为代理和网络限制失败过一次
- 之后已通过高权限前缀批准恢复使用

### 7.3 OMX 状态

已确认：

- `omx` 可用
- 路径为：`/Users/admin/.petclaw/node/bin/omx`
- `omx` 是 `oh-my-codex`
- 支持：
  - `omx --xhigh`
  - `omx --madmax`
  - `omx resume`
  - `omx --worktree`

已确认的高权限运行方式：

```bash
cd /Users/admin/ai/self-dev/FARS
omx --xhigh --madmax
```

已确认的最高权限续跑方式：

```bash
omx resume --last -C /Users/admin/ai/self-dev/FARS --dangerously-bypass-approvals-and-sandbox --search -c 'model_reasoning_effort="xhigh"'
```

如果需要从选择器选会话：

```bash
omx resume --all -C /Users/admin/ai/self-dev/FARS --dangerously-bypass-approvals-and-sandbox --search -c 'model_reasoning_effort="xhigh"'
```

## 8. 下一步执行清单

### 立即继续做的事情

1. 继续拆关键词多轮搜索开源项目
2. 明确 clone 清单，保证三类项目都覆盖
3. clone 到 `/Users/admin/ai/lunwen/ref`
4. 阅读仓库并整理：
   - 项目定位
   - 关键模块
   - 可复用能力
   - 与目标系统的差异
5. 生成：
   - `docs/project-index.md`
   - `docs/executable-plan.md`

### 文档输出要求

#### `project-index.md`

必须包含：

- 项目名称
- 仓库链接
- 类别
- 核心功能
- 可复用模块
- 对 FARS 论文知识层的参考价值
- 不足与限制

#### `executable-plan.md`

必须包含：

- 论文知识层的系统边界
- 数据模型
- 模块拆分
- API 设计
- 技术选型
- MVP 范围
- 开发阶段划分
- 和未来 worktree 并发层的接口设计

## 9. 建议的 handoff 提示词

后续切到 `omx` 高权限模式时，可直接使用下面这段作为 handoff：

```text
继续之前的 FARS 调研与落地工作，直接自动执行，不要停在分析。

目标：
1. 多轮搜索与筛选和 FARS 相似的开源项目，重点覆盖三类：
   - 自动科研/研究代理流水线
   - 论文获取与论文解析
   - 引文关系/论文知识图谱/学术图数据库
2. 使用拆分关键词多搜几轮，优先用 gh search repos，必要时补网页搜索。
3. 将高相关仓库 clone 到 /Users/admin/ai/lunwen/ref
4. 阅读 clone 下来的项目，产出两份文档到 /Users/admin/ai/self-dev/FARS/docs/：
   - project-index.md：项目索引、项目定位、核心能力、可复用模块、与 FARS 的相似点/差异点
   - executable-plan.md：基于这些参考项目形成的可执行开发文档，优先聚焦论文知识层
5. 开发方向优先级：
   - P0：论文多源获取、去重、全文获取、结构化解析、citation graph
   - P1：paper-method-dataset-metric 关系图谱、语义关系（extends/compares/contradicts）
   - P2：为未来多 worktree 并发流水线预留接口

已知上下文：
- 用户当前最优先的是“论文知识层”
- 后续还要支持 worktree 并发跑多个研究流水线，但不是现在的首要实现
- 当前 FARS 工作目录：/Users/admin/ai/self-dev/FARS
- 参考仓库存放目录：/Users/admin/ai/lunwen/ref

执行要求：
- 先搜全再选，不要只 clone agent 项目，必须包含论文解析和学术图谱相关项目
- clone 后要实际阅读 README/目录结构/关键模块，再写索引文档
- 文档必须能指导后续直接开发，不要只写泛泛总结
```

## 10. 当前结论

当前项目已经完成从“泛泛想做 FARS”到“明确先做论文知识层”的收敛。

下一阶段不应直接进入大规模编码，而应先完成：

1. 参考项目池建立
2. 项目索引文档
3. 可执行开发方案

这三步完成后，再启动代码实现会更稳。

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    database_status: str
    database_bootstrap_mode: str
    request_logging_enabled: bool
    paper_count: int
    run_count: int


class SystemInfoResponse(BaseModel):
    app: str
    version: str
    environment: str
    api_prefix: str
    database_bootstrap_mode: str
    parser_provider: str
    artifacts_root: str
    repo_root: str
    worktree_root: str
    request_id_header: str
    request_logging_enabled: bool
    llm_provider: str
    llm_default_profile: str
    llm_frontier_model: str
    llm_standard_model: str
    llm_spark_model: str
    llm_default_reasoning_effort: str


class IngestTopicRequest(BaseModel):
    topic: str = Field(min_length=2)
    limit: int = Field(default=10, ge=1, le=50)


class IngestTopicResponse(BaseModel):
    topic: str
    papers_created: int
    papers_updated: int
    versions_created: int
    paper_ids: list[int]
    version_ids: list[int]


class ParseVersionResponse(BaseModel):
    version_id: int
    sections_created: int
    chunks_created: int
    citations_created: int
    contexts_created: int
    edges_created: int
    parser_provider: str


class PaperSectionRead(BaseModel):
    id: int
    section_type: str
    heading: str | None = None
    order_index: int
    text: str | None = None


class CitationContextRead(BaseModel):
    id: int
    context_text: str
    context_type: str


class CitationRead(BaseModel):
    id: int
    raw_reference: str
    citation_key: str | None = None
    target_paper_id: int | None = None
    target_paper_title: str | None = None
    resolution_confidence: float
    contexts: list[CitationContextRead]


class PaperVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_type: str
    source_url: str | None = None
    pdf_url: str | None = None
    local_pdf_path: str | None = None
    parse_status: str


class PaperRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_title: str
    doi: str | None = None
    openalex_id: str | None = None
    publication_year: int | None = None
    venue: str | None = None
    citation_count: int


class PaperResultStats(BaseModel):
    result_count: int
    method_count: int
    dataset_count: int
    metric_count: int
    metric_names: list[str]


class TopicTopResultPaper(BaseModel):
    paper_id: int
    canonical_title: str
    result_count: int


class TopicLandscapeResponse(BaseModel):
    query: str
    paper_count: int
    papers: list[PaperRead]
    methods: list[str]
    datasets: list[str]
    metrics: list[str]
    edge_type_counts: dict[str, int]
    result_count: int
    papers_with_results: int
    top_result_papers: list[TopicTopResultPaper]


class PaperDetailResponse(PaperRead):
    abstract: str | None = None
    is_open_access: bool
    primary_source: str | None = None
    versions: list[PaperVersionRead] = []
    result_stats: PaperResultStats


class GraphNeighborResponse(BaseModel):
    paper_id: int
    title: str
    edge_type: str
    confidence: float


class GraphMermaidResponse(BaseModel):
    paper_id: int
    mermaid: str


class GraphExplanationItem(BaseModel):
    target_paper_id: int | None = None
    target_paper_title: str | None = None
    edge_types: list[str]
    raw_references: list[str]
    context_texts: list[str]
    context_types: list[str]


class GraphExplanationResponse(BaseModel):
    paper_id: int
    explanations: list[GraphExplanationItem]


class SemanticEnrichmentRequest(BaseModel):
    methods: list[str] = []
    datasets: list[str] = []
    metrics: list[str] = []


class SemanticEnrichmentResponse(BaseModel):
    paper_id: int
    methods_attached: int
    datasets_attached: int
    metrics_attached: int


class AutoSemanticEnrichmentResponse(SemanticEnrichmentResponse):
    extracted_methods: list[str]
    extracted_datasets: list[str]
    extracted_metrics: list[str]


class SemanticEntityRead(BaseModel):
    id: int
    name: str


class ExperimentResultRead(BaseModel):
    id: int
    run_id: int
    paper_id: int
    method_name: str | None = None
    dataset_name: str | None = None
    metric_name: str | None = None
    value: str
    source: str
    notes: str | None = None


class ResearchHypothesisRead(BaseModel):
    id: int
    run_id: int
    paper_id: int
    statement: str
    rationale: str | None = None


class ExperimentPlanRead(BaseModel):
    id: int
    run_id: int
    paper_id: int
    title: str
    steps: list[str]


class ExperimentTaskRead(BaseModel):
    id: int
    run_id: int
    plan_id: int
    paper_id: int
    title: str
    task_type: str
    status: str
    config_json: str


class ResearchIterationRead(BaseModel):
    id: int
    run_id: int
    iteration_index: int
    plan_title: str
    metric_name: str | None = None
    metric_value: str | None = None
    decision: str
    rationale: str | None = None


class ResearchRunEventRead(BaseModel):
    id: int
    run_id: int
    event_type: str
    status: str
    source: str
    message: str
    payload_json: str | None = None
    time_created: str


class EvidencePackResponse(BaseModel):
    paper_id: int
    canonical_title: str
    methods: list[SemanticEntityRead]
    datasets: list[SemanticEntityRead]
    metrics: list[SemanticEntityRead]
    experiment_results: list[ExperimentResultRead]
    result_stats: PaperResultStats
    neighbors: list[GraphNeighborResponse]


class SemanticEdgeInferenceResponse(BaseModel):
    paper_id: int
    edges_created: int


class SnapshotCreateRequest(BaseModel):
    topic: str | None = None


class SnapshotRead(BaseModel):
    id: int
    paper_id: int
    topic: str | None = None
    payload_json: str


class ResearchRunCreateRequest(BaseModel):
    snapshot_id: int
    branch_name: str | None = None


class ResearchRunResultWriteRequest(BaseModel):
    status: str = "completed"
    result_summary: str | None = None
    result_payload_json: str | None = None


class ContinueRunRequest(BaseModel):
    iterations: int = Field(default=1, ge=1, le=50)
    llm_profile: str | None = None
    llm_model: str | None = None
    llm_reasoning_effort: str | None = None


class ResearchRunRead(BaseModel):
    id: int
    snapshot_id: int
    branch_name: str | None = None
    worktree_path: str | None = None
    status: str
    result_summary: str | None = None
    result_payload_json: str | None = None
    report_title: str | None = None
    report_figure_path: str | None = None
    paper_draft_title: str | None = None
    artifact_dir: str | None = None


class ResearchRunStatusResponse(BaseModel):
    run_id: int
    status: str
    summary: str | None = None


class ResearchReportResponse(BaseModel):
    run_id: int
    title: str
    markdown: str
    figure_path: str | None = None


class PaperDraftResponse(BaseModel):
    run_id: int
    title: str
    markdown: str
    figure_path: str | None = None


class ExperimentResultWriteRequest(BaseModel):
    paper_id: int
    method_name: str | None = None
    dataset_name: str | None = None
    metric_name: str | None = None
    value: str
    notes: str | None = None


class AutoExperimentResultWriteRequest(BaseModel):
    paper_id: int


class AutoExperimentResultWriteResponse(BaseModel):
    run_id: int
    paper_id: int
    created_count: int
    results: list[ExperimentResultRead]


class WorktreeExecutionManifestResponse(BaseModel):
    run_id: int
    snapshot_id: int
    branch_name: str
    knowledge_mode: str
    execution_mode: str
    worktree_path: str | None = None
    repo_root: str | None = None


class WorktreeCreateResponse(BaseModel):
    run_id: int
    branch_name: str
    worktree_path: str
    repo_root: str


class AutonomousResearchLoopRequest(BaseModel):
    topic: str
    limit: int = Field(default=5, ge=1, le=20)
    iterations: int = Field(default=1, ge=1, le=20)
    branch_name: str | None = None
    use_worktree: bool = False
    llm_profile: str | None = None
    llm_model: str | None = None
    llm_reasoning_effort: str | None = None


class BatchAutonomousResearchLoopRequest(BaseModel):
    topics: list[str] = Field(min_length=1, max_length=20)
    limit: int = Field(default=5, ge=1, le=20)
    iterations: int = Field(default=1, ge=1, le=20)
    use_worktree: bool = False
    max_concurrency: int = Field(default=1, ge=1, le=8)
    branch_prefix: str | None = None
    llm_profile: str | None = None
    llm_model: str | None = None
    llm_reasoning_effort: str | None = None


class RunReconciliationRequest(BaseModel):
    run_ids: list[int] = Field(min_length=1, max_length=200)


class AutonomousResearchLoopResponse(BaseModel):
    topic: str
    requested_iterations: int
    paper_ids: list[int]
    version_ids: list[int]
    parsed_versions: int
    enriched_papers: int
    inferred_edges: int
    result_count: int
    executed_result_count: int
    hypothesis_count: int
    experiment_plan_count: int
    experiment_task_count: int
    iteration_count: int
    snapshot_id: int
    run_id: int
    lead_paper_id: int
    lead_paper_title: str
    used_worktree: bool
    worktree_path: str | None = None
    artifact_dir: str | None = None
    llm_provider: str | None = None
    llm_profile: str | None = None
    llm_model: str | None = None
    llm_reasoning_effort: str | None = None
    summary: str


class BatchAutonomousResearchLoopItem(BaseModel):
    topic: str
    status: str
    run_id: int | None = None
    lead_paper_id: int | None = None
    lead_paper_title: str | None = None
    artifact_dir: str | None = None
    summary: str | None = None
    result_count: int
    error: str | None = None


class BatchMetricLeader(BaseModel):
    metric_name: str
    run_id: int
    topic: str
    value: float
    value_raw: str


class BatchLoopReconciliationResponse(BaseModel):
    successful_run_count: int
    failed_run_count: int
    total_result_count: int
    best_metrics: list[BatchMetricLeader]


class BatchArtifactBundleResponse(BaseModel):
    batch_id: str
    kind: str
    artifact_dir: str
    summary_path: str
    items_path: str
    reconciliation_path: str
    manifest_path: str
    zip_path: str


class BatchAutonomousResearchLoopResponse(BaseModel):
    requested_topics: list[str]
    requested_iterations: int
    requested_concurrency: int
    completed_count: int
    failed_count: int
    llm_provider: str | None = None
    llm_profile: str | None = None
    llm_model: str | None = None
    llm_reasoning_effort: str | None = None
    items: list[BatchAutonomousResearchLoopItem]
    reconciliation: BatchLoopReconciliationResponse
    artifact: BatchArtifactBundleResponse


class RunReconciliationResponse(BaseModel):
    requested_run_ids: list[int]
    missing_run_ids: list[int]
    found_count: int
    items: list[BatchAutonomousResearchLoopItem]
    reconciliation: BatchLoopReconciliationResponse
    artifact: BatchArtifactBundleResponse


class BatchArtifactManifestFile(BaseModel):
    path: str
    exists: bool
    size_bytes: int | None = None
    sha256: str | None = None


class BatchArtifactManifestResponse(BaseModel):
    batch_id: str
    kind: str
    artifact_dir: str
    files: dict[str, BatchArtifactManifestFile]


class BatchArtifactIndexItem(BaseModel):
    batch_id: str
    kind: str
    artifact_dir: str
    manifest_path: str
    created_at: str | None = None
    exists: bool


class RunArtifactBundleResponse(BaseModel):
    run_id: int
    artifact_dir: str
    report_path: str | None = None
    paper_draft_path: str | None = None
    figure_path: str | None = None
    summary_path: str | None = None
    iterations_path: str | None = None
    hypotheses_path: str | None = None
    experiment_plans_path: str | None = None
    experiment_tasks_path: str | None = None
    experiment_results_path: str | None = None
    events_path: str | None = None
    manifest_path: str | None = None
    zip_path: str | None = None


class RunArtifactManifestFile(BaseModel):
    path: str
    exists: bool
    size_bytes: int | None = None
    sha256: str | None = None


class RunArtifactManifestResponse(BaseModel):
    run_id: int
    artifact_dir: str
    files: dict[str, RunArtifactManifestFile]

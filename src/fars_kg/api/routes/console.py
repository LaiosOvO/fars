from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from fars_kg.api.auth import OPERATOR_SESSION_COOKIE, operator_access_granted
from fars_kg.services.repository import list_recent_run_events, list_runs
from fars_kg.services.research_loop import AutonomousResearchLoopService

router = APIRouter(tags=["console"], include_in_schema=False)


@router.get("/", include_in_schema=False)
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/fars", status_code=307)


@router.get("/fars", response_class=HTMLResponse, include_in_schema=False)
def fars_live_style_page(request: Request) -> HTMLResponse:
    api_prefix = request.app.state.settings.api_prefix
    return HTMLResponse(_fars_html(api_prefix))


@router.get("/fars/data", response_class=JSONResponse, include_in_schema=False)
def fars_live_data(request: Request, limit: int = 8) -> JSONResponse:
    db = request.app.state.db
    with db.session() as session:
        runs = list_runs(session)[: max(1, limit)]
    batches = AutonomousResearchLoopService(
        openalex_client=None,
        parser=None,
        worktree_manager=None,
    ).list_batch_artifacts(limit=limit)
    payload = {
        "deployments": [
            {
                "batch_id": item["batch_id"],
                "kind": item["kind"],
                "created_at": item["created_at"],
            }
            for item in batches
        ],
        "research_runs": [
            {
                "id": run.id,
                "status": run.status,
            }
            for run in runs
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "deployments": len(batches),
            "research_runs": len(runs),
        },
    }
    return JSONResponse(payload)


@router.get("/fars/events", response_class=JSONResponse, include_in_schema=False)
def fars_live_events(request: Request, limit: int = 16) -> JSONResponse:
    db = request.app.state.db
    capped_limit = max(1, min(limit, 50))
    with db.session() as session:
        events = list_recent_run_events(session, limit=capped_limit)
    payload = {
        "events": [
            {
                "run_id": event.run_id,
                "event_type": event.event_type,
                "status": event.status,
                "source": event.source,
                "time_created": event.time_created.isoformat(),
            }
            for event in events
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(payload)


@router.get("/console", response_class=HTMLResponse, include_in_schema=False)
def research_console(request: Request) -> HTMLResponse:
    settings = request.app.state.settings
    if settings.operator_token and not operator_access_granted(request, settings.operator_token):
        return HTMLResponse(_console_login_html(error=None), status_code=401)
    api_prefix = request.app.state.settings.api_prefix
    return HTMLResponse(_console_html(api_prefix))


@router.post("/console/login", response_class=HTMLResponse, include_in_schema=False, response_model=None)
async def console_login(request: Request):
    settings = request.app.state.settings
    if not settings.operator_token:
        return RedirectResponse(url="/console", status_code=303)
    body = (await request.body()).decode("utf-8")
    token = parse_qs(body).get("token", [""])[0]
    if token != settings.operator_token:
        return HTMLResponse(_console_login_html(error="Invalid operator token"), status_code=401)
    response = RedirectResponse(url="/console", status_code=303)
    response.set_cookie(
        key=OPERATOR_SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/console/logout", include_in_schema=False)
def console_logout() -> RedirectResponse:
    response = RedirectResponse(url="/console", status_code=303)
    response.delete_cookie(OPERATOR_SESSION_COOKIE)
    return response


def _console_html(api_prefix: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FARS Research Console</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b1020;
      --panel: #121a2e;
      --muted: #97a3bf;
      --text: #f1f5ff;
      --accent: #6aa4ff;
      --ok: #34d399;
      --warn: #fbbf24;
      --err: #f87171;
      --border: #223150;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    }}
    .wrap {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
    }}
    p {{
      color: var(--muted);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
    }}
    .span-3 {{ grid-column: span 3; }}
    .span-4 {{ grid-column: span 4; }}
    .span-6 {{ grid-column: span 6; }}
    .span-8 {{ grid-column: span 8; }}
    .span-12 {{ grid-column: span 12; }}
    @media (max-width: 980px) {{
      .span-3, .span-4, .span-6, .span-8, .span-12 {{ grid-column: span 12; }}
    }}
    .kpi {{
      font-size: 28px;
      font-weight: 700;
      margin-top: 4px;
    }}
    .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .06em;
    }}
    input, select, button, textarea {{
      background: #0e1528;
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 14px;
    }}
    textarea {{ min-height: 88px; width: 100%; }}
    input, select {{ width: 100%; }}
    button {{
      cursor: pointer;
      border-color: #335190;
      background: #1b2f5f;
    }}
    button:hover {{ filter: brightness(1.1); }}
    .row {{
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 10px;
    }}
    .c3 {{ grid-column: span 3; }}
    .c4 {{ grid-column: span 4; }}
    .c6 {{ grid-column: span 6; }}
    .c12 {{ grid-column: span 12; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      border-bottom: 1px solid var(--border);
      text-align: left;
      padding: 8px 6px;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
    .tag {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      border: 1px solid var(--border);
    }}
    .ok {{ color: var(--ok); }}
    .warn {{ color: var(--warn); }}
    .err {{ color: var(--err); }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    #graph {{
      width: 100%;
      min-height: 380px;
      border: 1px dashed var(--border);
      border-radius: 10px;
      display: grid;
      place-items: center;
      color: var(--muted);
    }}
    pre {{
      white-space: pre-wrap;
      margin: 0;
      color: #d0d8ef;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel span-12" style="margin-bottom:16px">
      <h1>FARS Research Console</h1>
      <p>Not just backend: run research loops, inspect runs/batches, and visualize paper graph relationships.</p>
      <p><span class="label">API Prefix</span> <code id="api-prefix">{api_prefix}</code></p>
    </div>

    <div class="grid">
      <div class="panel span-3">
        <div class="label">Readiness</div>
        <div class="kpi" id="k-ready">-</div>
      </div>
      <div class="panel span-3">
        <div class="label">Papers</div>
        <div class="kpi" id="k-paper">-</div>
      </div>
      <div class="panel span-3">
        <div class="label">Runs</div>
        <div class="kpi" id="k-run">-</div>
      </div>
      <div class="panel span-3">
        <div class="label">Batches</div>
        <div class="kpi" id="k-batch">-</div>
      </div>
    </div>

    <div class="grid">
      <div class="panel span-6">
        <h2>Single Research Loop</h2>
        <p>Auto experiment run with Codex LLM config.</p>
        <div class="row">
          <div class="c6"><input id="run-topic" placeholder="topic (e.g. transformers)" value="transformers" /></div>
          <div class="c3"><input id="run-limit" type="number" min="1" max="20" value="2" /></div>
          <div class="c3"><input id="run-iter" type="number" min="1" max="20" value="2" /></div>
        </div>
        <div class="row">
          <div class="c4">
            <select id="run-llm-profile">
              <option value="frontier" selected>llm profile: frontier</option>
              <option value="standard">llm profile: standard</option>
              <option value="spark">llm profile: spark</option>
              <option value="custom">llm profile: custom</option>
            </select>
          </div>
          <div class="c4"><input id="run-llm-model" placeholder="model (auto from profile if empty)" /></div>
          <div class="c4">
            <select id="run-llm-reasoning">
              <option value="">reasoning: profile default</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="xhigh">xhigh</option>
            </select>
          </div>
        </div>
        <div class="row">
          <div class="c6"><input id="run-branch" placeholder="branch name (optional)" /></div>
          <div class="c3">
            <select id="run-worktree">
              <option value="false" selected>no worktree</option>
              <option value="true">use worktree</option>
            </select>
          </div>
          <div class="c3"><button id="run-submit">Run Loop</button></div>
        </div>
      </div>

      <div class="panel span-6">
        <h2>Batch Loop</h2>
        <p>Auto experiment batch with shared Codex LLM config.</p>
        <div class="row">
          <div class="c12"><textarea id="batch-topics" placeholder="one topic per line">transformers
machine translation</textarea></div>
        </div>
        <div class="row">
          <div class="c3"><input id="batch-limit" type="number" min="1" max="20" value="2" /></div>
          <div class="c3"><input id="batch-iter" type="number" min="1" max="20" value="2" /></div>
          <div class="c3"><input id="batch-concurrency" type="number" min="1" max="8" value="2" /></div>
          <div class="c3"><input id="batch-prefix" placeholder="branch prefix" value="batch-ui" /></div>
        </div>
        <div class="row">
          <div class="c6">
            <select id="batch-worktree">
              <option value="false" selected>no worktree</option>
              <option value="true">use worktree</option>
            </select>
          </div>
          <div class="c6"><button id="batch-submit">Run Batch</button></div>
        </div>
        <div class="row">
          <div class="c4">
            <select id="batch-llm-profile">
              <option value="frontier" selected>llm profile: frontier</option>
              <option value="standard">llm profile: standard</option>
              <option value="spark">llm profile: spark</option>
              <option value="custom">llm profile: custom</option>
            </select>
          </div>
          <div class="c4"><input id="batch-llm-model" placeholder="model (auto from profile if empty)" /></div>
          <div class="c4">
            <select id="batch-llm-reasoning">
              <option value="">reasoning: profile default</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="xhigh">xhigh</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="panel span-12">
        <h2>Continue Auto Experiment Run</h2>
        <div class="row">
          <div class="c4"><input id="continue-run-id" type="number" min="1" placeholder="run id" /></div>
          <div class="c4"><input id="continue-iterations" type="number" min="1" max="20" value="1" /></div>
          <div class="c4"><button id="continue-submit">Continue Run</button></div>
        </div>
        <div class="row">
          <div class="c4">
            <select id="continue-llm-profile">
              <option value="frontier" selected>llm profile: frontier</option>
              <option value="standard">llm profile: standard</option>
              <option value="spark">llm profile: spark</option>
              <option value="custom">llm profile: custom</option>
            </select>
          </div>
          <div class="c4"><input id="continue-llm-model" placeholder="model (auto from profile if empty)" /></div>
          <div class="c4">
            <select id="continue-llm-reasoning">
              <option value="">reasoning: profile default</option>
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="xhigh">xhigh</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="panel span-12">
        <h2>Run Reconciliation</h2>
        <div class="row">
          <div class="c10"><input id="reconcile-run-ids" placeholder="run ids, comma separated (e.g. 1,2,3)" /></div>
          <div class="c2"><button id="reconcile-submit">Reconcile</button></div>
        </div>
        <pre id="reconcile-output">No reconciliation executed.</pre>
      </div>
    </div>

    <div class="grid">
      <div class="panel span-12">
        <h2>Paper Explorer</h2>
        <div class="row">
          <div class="c10"><input id="paper-query" placeholder="search papers (title / abstract / venue)" value="transformer" /></div>
          <div class="c2"><button id="paper-search">Search</button></div>
        </div>
        <table>
          <thead>
            <tr><th>ID</th><th>Title</th><th>Year</th><th>Citations</th><th>Action</th></tr>
          </thead>
          <tbody id="papers-body"><tr><td colspan="5">Search to load papers.</td></tr></tbody>
        </table>
        <div class="row" style="margin-top:10px">
          <div class="c12">
            <div class="label">Selected Paper Detail</div>
            <pre id="paper-detail">No paper selected.</pre>
          </div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="panel span-8">
        <h2>Runs</h2>
        <table>
          <thead>
            <tr><th>ID</th><th>Status</th><th>LLM</th><th>Branch</th><th>Summary</th><th>Artifacts</th></tr>
          </thead>
          <tbody id="runs-body"><tr><td colspan="6">Loading...</td></tr></tbody>
        </table>
      </div>
      <div class="panel span-4">
        <h2>Graph Viewer</h2>
        <div class="row">
          <div class="c8"><input id="graph-paper-id" type="number" min="1" value="1" /></div>
          <div class="c4"><button id="graph-load">Load</button></div>
        </div>
        <div id="graph">No graph loaded</div>
      </div>
    </div>

    <div class="grid">
      <div class="panel span-12">
        <h2>Batches</h2>
        <table>
          <thead>
            <tr><th>Batch ID</th><th>Kind</th><th>Created</th><th>Manifest</th><th>Downloads</th></tr>
          </thead>
          <tbody id="batches-body"><tr><td colspan="5">Loading...</td></tr></tbody>
        </table>
      </div>
    </div>

    <div class="grid">
      <div class="panel span-12">
        <h2>Logs</h2>
        <pre id="log">ready.</pre>
      </div>
    </div>
  </div>

  <script>
    const API = "{api_prefix}";
    const logEl = document.getElementById("log");
    const llmDefaults = {{
      llm_provider: "codex",
      llm_default_profile: "frontier",
      llm_frontier_model: "gpt-5.4",
      llm_standard_model: "gpt-5.4-mini",
      llm_spark_model: "gpt-5.3-codex-spark",
      llm_default_reasoning_effort: "high",
    }};

    function log(msg, payload) {{
      const line = `[${{new Date().toLocaleTimeString()}}] ${{msg}}`;
      if (payload !== undefined) {{
        logEl.textContent = line + "\\n" + JSON.stringify(payload, null, 2) + "\\n\\n" + logEl.textContent;
      }} else {{
        logEl.textContent = line + "\\n" + logEl.textContent;
      }}
    }}

    async function fetchJson(path, options={{}}) {{
      const res = await fetch(path, {{
        headers: {{ "Content-Type": "application/json" }},
        ...options,
      }});
      if (!res.ok) {{
        let detail = `${{res.status}} ${{res.statusText}}`;
        try {{
          const body = await res.json();
          if (body.detail) detail = body.detail;
        }} catch (_err) {{}}
        throw new Error(detail);
      }}
      return res.json();
    }}

    function modelForProfile(profile) {{
      if (profile === "spark") return llmDefaults.llm_spark_model;
      if (profile === "standard") return llmDefaults.llm_standard_model;
      return llmDefaults.llm_frontier_model;
    }}

    function reasoningForProfile(profile) {{
      if (profile === "spark") return "low";
      if (profile === "standard") return llmDefaults.llm_default_reasoning_effort || "high";
      return llmDefaults.llm_default_reasoning_effort || "high";
    }}

    function buildLlmPayload(prefix) {{
      const profile = (document.getElementById(`${{prefix}}-llm-profile`)?.value || llmDefaults.llm_default_profile || "frontier").trim();
      const modelInput = document.getElementById(`${{prefix}}-llm-model`)?.value || "";
      const reasoningInput = document.getElementById(`${{prefix}}-llm-reasoning`)?.value || "";
      const model = modelInput.trim() || modelForProfile(profile);
      const reasoning = reasoningInput.trim() || reasoningForProfile(profile);
      return {{
        llm_profile: profile,
        llm_model: model,
        llm_reasoning_effort: reasoning,
      }};
    }}

    function setDefaultLlmUI(prefix) {{
      const profileNode = document.getElementById(`${{prefix}}-llm-profile`);
      const modelNode = document.getElementById(`${{prefix}}-llm-model`);
      const reasoningNode = document.getElementById(`${{prefix}}-llm-reasoning`);
      if (!profileNode || !modelNode || !reasoningNode) return;
      profileNode.value = llmDefaults.llm_default_profile || "frontier";
      modelNode.value = modelForProfile(profileNode.value);
      reasoningNode.value = "";
      profileNode.addEventListener("change", () => {{
        if (profileNode.value !== "custom") {{
          modelNode.value = modelForProfile(profileNode.value);
        }}
      }});
    }}

    async function loadLlmDefaults() {{
      try {{
        const info = await fetchJson(`${{API}}/system/info`);
        llmDefaults.llm_provider = info.llm_provider || llmDefaults.llm_provider;
        llmDefaults.llm_default_profile = info.llm_default_profile || llmDefaults.llm_default_profile;
        llmDefaults.llm_frontier_model = info.llm_frontier_model || llmDefaults.llm_frontier_model;
        llmDefaults.llm_standard_model = info.llm_standard_model || llmDefaults.llm_standard_model;
        llmDefaults.llm_spark_model = info.llm_spark_model || llmDefaults.llm_spark_model;
        llmDefaults.llm_default_reasoning_effort = info.llm_default_reasoning_effort || llmDefaults.llm_default_reasoning_effort;
      }} catch (_err) {{
        // keep defaults
      }}
      setDefaultLlmUI("run");
      setDefaultLlmUI("batch");
      setDefaultLlmUI("continue");
    }}

    function badge(status) {{
      const cls = status === "completed" || status === "ready" ? "ok" : (status.includes("fail") ? "err" : "warn");
      return `<span class="tag ${{cls}}">${{status}}</span>`;
    }}

    function parseRunLlm(run) {{
      try {{
        const payload = run.result_payload_json ? JSON.parse(run.result_payload_json) : null;
        const llm = payload && payload.llm ? payload.llm : null;
        if (!llm) return "-";
        return `${{llm.profile || "profile?"}} / ${{llm.model || "model?"}} / ${{llm.reasoning_effort || "reasoning?"}}`;
      }} catch (_err) {{
        return "-";
      }}
    }}

    async function refreshKpis() {{
      const readiness = await fetchJson(`${{API}}/health/readiness`);
      const runs = await fetchJson(`${{API}}/runs`);
      const batches = await fetchJson(`${{API}}/research-loops/batches?limit=50`);
      document.getElementById("k-ready").innerHTML = badge(readiness.status);
      document.getElementById("k-paper").textContent = readiness.paper_count;
      document.getElementById("k-run").textContent = runs.length;
      document.getElementById("k-batch").textContent = batches.length;
    }}

    async function refreshRuns() {{
      const runs = await fetchJson(`${{API}}/runs`);
      const body = document.getElementById("runs-body");
      if (!runs.length) {{
        body.innerHTML = '<tr><td colspan="6">No runs yet.</td></tr>';
        return;
      }}
      body.innerHTML = runs.map(run => {{
        const summary = run.result_summary ? run.result_summary.slice(0, 110) : "-";
        const llm = parseRunLlm(run);
        return `
          <tr>
            <td>${{run.id}}</td>
            <td>${{badge(run.status)}}</td>
            <td><code>${{llm}}</code></td>
            <td><code>${{run.branch_name || "-"}}</code></td>
            <td>${{summary}}</td>
            <td>
              <a href="${{API}}/runs/${{run.id}}/report/download">report</a> ·
              <a href="${{API}}/runs/${{run.id}}/paper-draft/download">draft</a> ·
              <a href="${{API}}/runs/${{run.id}}/bundle/download">bundle</a>
            </td>
          </tr>
        `;
      }}).join("");
    }}

    async function searchPapers() {{
      const q = document.getElementById("paper-query").value.trim();
      if (!q) {{
        document.getElementById("papers-body").innerHTML = '<tr><td colspan="5">Enter query.</td></tr>';
        return;
      }}
      const papers = await fetchJson(`${{API}}/papers/search?q=${{encodeURIComponent(q)}}`);
      const body = document.getElementById("papers-body");
      if (!papers.length) {{
        body.innerHTML = '<tr><td colspan="5">No papers found.</td></tr>';
        return;
      }}
      body.innerHTML = papers.map(item => `
        <tr>
          <td>${{item.id}}</td>
          <td>${{item.canonical_title}}</td>
          <td>${{item.publication_year || "-"}}</td>
          <td>${{item.citation_count}}</td>
          <td><button onclick="inspectPaper(${{item.id}})">Inspect</button></td>
        </tr>
      `).join("");
    }}

    async function inspectPaper(paperId) {{
      try {{
        const detail = await fetchJson(`${{API}}/papers/${{paperId}}`);
        const citations = await fetchJson(`${{API}}/papers/${{paperId}}/citations`);
        const explanations = await fetchJson(`${{API}}/graph/papers/${{paperId}}/explanations`);
        document.getElementById("paper-detail").textContent = JSON.stringify({{
          detail,
          citations,
          explanations,
        }}, null, 2);
        document.getElementById("graph-paper-id").value = paperId;
        await loadGraph();
        log(`paper ${{paperId}} inspected`, {{
          title: detail.canonical_title,
          citations: citations.length,
        }});
      }} catch (err) {{
        document.getElementById("paper-detail").textContent = "Inspect failed: " + err.message;
        log("paper inspect failed: " + err.message);
      }}
    }}

    async function refreshBatches() {{
      const batches = await fetchJson(`${{API}}/research-loops/batches?limit=50`);
      const body = document.getElementById("batches-body");
      if (!batches.length) {{
        body.innerHTML = '<tr><td colspan="5">No batches yet.</td></tr>';
        return;
      }}
      body.innerHTML = batches.map(item => `
        <tr>
          <td><code>${{item.batch_id}}</code></td>
          <td>${{item.kind}}</td>
          <td>${{item.created_at || "-"}}</td>
          <td><a href="${{API}}/research-loops/batches/${{item.batch_id}}/manifest">manifest</a></td>
          <td>
            <a href="${{API}}/research-loops/batches/${{item.batch_id}}/download">zip</a> ·
            <a href="${{API}}/research-loops/batches/${{item.batch_id}}/summary/download">summary</a> ·
            <a href="${{API}}/research-loops/batches/${{item.batch_id}}/items/download">items</a> ·
            <a href="${{API}}/research-loops/batches/${{item.batch_id}}/reconciliation/download">recon</a>
          </td>
        </tr>
      `).join("");
    }}

    async function refreshAll() {{
      await Promise.all([refreshKpis(), refreshRuns(), refreshBatches()]);
    }}

    function parseTopics(value) {{
      return value.split("\\n").map(v => v.trim()).filter(Boolean);
    }}

    async function submitRun() {{
      try {{
        const payload = {{
          topic: document.getElementById("run-topic").value.trim(),
          limit: Number(document.getElementById("run-limit").value),
          iterations: Number(document.getElementById("run-iter").value),
          branch_name: document.getElementById("run-branch").value.trim() || null,
          use_worktree: document.getElementById("run-worktree").value === "true",
          ...buildLlmPayload("run"),
        }};
        log("run loop started", payload);
        const result = await fetchJson(`${{API}}/research-loops/run`, {{
          method: "POST",
          body: JSON.stringify(payload),
        }});
        log("run loop completed", result);
        await refreshAll();
      }} catch (err) {{
        log("run loop failed: " + err.message);
      }}
    }}

    async function submitBatch() {{
      try {{
        const payload = {{
          topics: parseTopics(document.getElementById("batch-topics").value),
          limit: Number(document.getElementById("batch-limit").value),
          iterations: Number(document.getElementById("batch-iter").value),
          max_concurrency: Number(document.getElementById("batch-concurrency").value),
          branch_prefix: document.getElementById("batch-prefix").value.trim() || null,
          use_worktree: document.getElementById("batch-worktree").value === "true",
          ...buildLlmPayload("batch"),
        }};
        log("batch loop started", payload);
        const result = await fetchJson(`${{API}}/research-loops/batch-run`, {{
          method: "POST",
          body: JSON.stringify(payload),
        }});
        log("batch loop completed", result);
        await refreshAll();
      }} catch (err) {{
        log("batch loop failed: " + err.message);
      }}
    }}

    async function submitContinue() {{
      try {{
        const runId = Number(document.getElementById("continue-run-id").value);
        if (!Number.isInteger(runId) || runId <= 0) {{
          throw new Error("Provide a valid run id");
        }}
        const payload = {{
          iterations: Number(document.getElementById("continue-iterations").value),
          ...buildLlmPayload("continue"),
        }};
        log(`continue run started #${{runId}}`, payload);
        const result = await fetchJson(`${{API}}/research-loops/${{runId}}/continue`, {{
          method: "POST",
          body: JSON.stringify(payload),
        }});
        log(`continue run completed #${{runId}}`, result);
        await refreshAll();
      }} catch (err) {{
        log("continue run failed: " + err.message);
      }}
    }}

    async function submitReconcile() {{
      try {{
        const raw = document.getElementById("reconcile-run-ids").value.trim();
        const runIds = raw
          .split(",")
          .map(item => Number(item.trim()))
          .filter(item => Number.isInteger(item) && item > 0);
        if (!runIds.length) {{
          throw new Error("Provide at least one valid run id");
        }}
        const payload = {{ run_ids: runIds }};
        log("reconcile started", payload);
        const result = await fetchJson(`${{API}}/research-loops/reconcile`, {{
          method: "POST",
          body: JSON.stringify(payload),
        }});
        document.getElementById("reconcile-output").textContent = JSON.stringify(result, null, 2);
        log("reconcile completed", result);
        await refreshAll();
      }} catch (err) {{
        document.getElementById("reconcile-output").textContent = "Reconcile failed: " + err.message;
        log("reconcile failed: " + err.message);
      }}
    }}

    function renderGraph(paperId, neighbors) {{
      const host = document.getElementById("graph");
      const width = 680;
      const height = 360;
      const cx = width / 2;
      const cy = height / 2;
      const radius = 130;
      const centerLabel = `Paper ${{paperId}}`;
      let svg = `<svg viewBox="0 0 ${{width}} ${{height}}" width="100%" height="${{height}}">`;
      svg += `<circle cx="${{cx}}" cy="${{cy}}" r="28" fill="#21418a" stroke="#6aa4ff" />`;
      svg += `<text x="${{cx}}" y="${{cy + 5}}" text-anchor="middle" fill="#fff" font-size="10">${{centerLabel}}</text>`;
      neighbors.forEach((n, i) => {{
        const angle = (Math.PI * 2 * i) / Math.max(neighbors.length, 1);
        const nx = cx + Math.cos(angle) * radius;
        const ny = cy + Math.sin(angle) * radius;
        svg += `<line x1="${{cx}}" y1="${{cy}}" x2="${{nx}}" y2="${{ny}}" stroke="#4563a6" />`;
        svg += `<circle cx="${{nx}}" cy="${{ny}}" r="22" fill="#1d2a45" stroke="#5b7ec7" />`;
        const label = (n.title || `P${{n.paper_id}}`).slice(0, 14);
        svg += `<text x="${{nx}}" y="${{ny + 4}}" text-anchor="middle" fill="#dce7ff" font-size="9">${{label}}</text>`;
      }});
      svg += "</svg>";
      host.innerHTML = svg;
    }}

    async function loadGraph() {{
      const paperId = Number(document.getElementById("graph-paper-id").value);
      try {{
        const neighbors = await fetchJson(`${{API}}/graph/papers/${{paperId}}/neighbors`);
        renderGraph(paperId, neighbors);
        log(`graph loaded for paper ${{paperId}}`, neighbors);
      }} catch (err) {{
        document.getElementById("graph").textContent = "Graph unavailable: " + err.message;
        log("graph load failed: " + err.message);
      }}
    }}

    document.getElementById("run-submit").addEventListener("click", submitRun);
    document.getElementById("batch-submit").addEventListener("click", submitBatch);
    document.getElementById("continue-submit").addEventListener("click", submitContinue);
    document.getElementById("reconcile-submit").addEventListener("click", submitReconcile);
    document.getElementById("graph-load").addEventListener("click", loadGraph);
    document.getElementById("paper-search").addEventListener("click", () => searchPapers().catch(err => log("paper search failed: " + err.message)));
    document.getElementById("paper-query").addEventListener("keydown", (event) => {{
      if (event.key === "Enter") {{
        searchPapers().catch(err => log("paper search failed: " + err.message));
      }}
    }});
    Promise.all([refreshAll(), loadLlmDefaults()])
      .then(() => searchPapers())
      .catch(err => log("initial load failed: " + err.message));
  </script>
</body>
</html>
"""


def _fars_html(api_prefix: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FARS - Analemma | Analemma</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #090b11;
      --panel: #11141f;
      --text: #f5f7ff;
      --muted: #9aa3bb;
      --line: #23283a;
      --accent: #ffffff;
      --brand: #ffffff;
      --ok: #32d296;
      --warn: #f6c453;
      --err: #f46b6b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: radial-gradient(1200px 600px at 50% -200px, #1c2235 0%, #090b11 62%);
      color: var(--text);
      font-family: "IBM Plex Mono", "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
      min-height: 100vh;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 20;
      backdrop-filter: blur(10px);
      background: rgba(9, 11, 17, 0.75);
      border-bottom: 1px solid var(--line);
    }}
    .nav {{
      max-width: 1560px;
      margin: 0 auto;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .logo {{
      letter-spacing: 0.12em;
      font-size: 14px;
      color: white;
      text-decoration: none;
      font-weight: 700;
    }}
    .nav-links {{
      display: flex;
      gap: 8px;
      align-items: center;
    }}
    .menu-toggle {{
      display: none;
      color: #f0f4ff;
      background: transparent;
      border: 1px solid transparent;
      width: auto;
      padding: 8px 10px;
      font-size: 12px;
    }}
    .sr-only {{
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }}
    .mobile-sheet {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(7, 9, 15, 0.78);
      backdrop-filter: blur(10px);
      z-index: 30;
      padding: 18px;
    }}
    .mobile-sheet.open {{
      display: block;
    }}
    .mobile-sheet-panel {{
      margin-left: auto;
      width: min(320px, 100%);
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #11141f;
      padding: 16px;
      box-shadow: 0 24px 60px rgba(0,0,0,.4);
    }}
    .mobile-sheet-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }}
    .mobile-sheet-title {{
      font-size: 13px;
      letter-spacing: .08em;
      color: var(--muted);
    }}
    .mobile-sheet-nav {{
      display: grid;
      gap: 8px;
    }}
    .mobile-sheet-nav a {{
      text-decoration: none;
      color: #f2f5ff;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      background: #0d111d;
      font-size: 12px;
      transition: border-color .18s ease, background .18s ease;
    }}
    .mobile-sheet-nav a.external::after {{
      content: " ↗";
      opacity: .8;
    }}
    .mobile-sheet-nav a:hover {{
      border-color: #3d4866;
      background: #12182a;
    }}
    .nav-links a {{
      text-decoration: none;
      color: #f0f4ff;
      font-size: 12px;
      border: 1px solid transparent;
      border-radius: 4px;
      padding: 8px 12px;
    }}
    .nav-links a.active {{
      border-color: #fff;
      background: #fff;
      color: #090b11;
      font-weight: 700;
    }}
    .nav-links a.secondary {{
      color: #f0f4ff;
      opacity: .92;
      transition: border-color .18s ease, background .18s ease, color .18s ease;
    }}
    .nav-links a.secondary::after {{
      content: " ↗";
      opacity: .8;
    }}
    .nav-links a.secondary:hover {{
      border-color: #2b3144;
      background: rgba(255,255,255,.04);
    }}
    .page {{
      max-width: 1240px;
      margin: 0 auto;
      padding: 28px 20px 44px;
    }}
    .hero {{
      text-align: center;
      margin-bottom: 34px;
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: clamp(24px, 4vw, 44px);
      line-height: 1.1;
      font-weight: 700;
      letter-spacing: -0.01em;
    }}
    .hero-sub {{
      margin: 0 0 18px;
      color: var(--muted);
      font-size: 13px;
    }}
    .social {{
      display: flex;
      justify-content: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .social a {{
      text-decoration: none;
      color: #d7ddf5;
      border: 1px solid #2f3547;
      border-radius: 999px;
      padding: 6px 12px;
      font-size: 12px;
      transition: border-color .18s ease, color .18s ease, background .18s ease;
    }}
    .social a:hover {{
      border-color: #4a5572;
      color: #ffffff;
      background: rgba(255,255,255,.04);
    }}
    .social a:focus-visible,
    .nav-links a:focus-visible,
    .mobile-sheet-nav a:focus-visible,
    .menu-toggle:focus-visible,
    .footer a:focus-visible {{
      outline: 2px solid #8aa6ff;
      outline-offset: 2px;
    }}
    .social a svg {{
      width: 14px;
      height: 14px;
      flex: none;
    }}
    .hero-image {{
      margin: 24px auto 34px;
      width: 100%;
      max-width: 1000px;
      border: 2px solid #2f364a;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 20px 45px rgba(0,0,0,.45);
      aspect-ratio: 1000 / 625;
      background: #0f1220;
      transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease;
    }}
    .hero-image:hover {{
      border-color: #48567a;
      box-shadow: 0 24px 54px rgba(0,0,0,.5);
      transform: translateY(-1px);
    }}
    .hero-image img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .section {{
      margin-bottom: 26px;
      background: rgba(17, 20, 31, 0.72);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
    }}
    .section-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }}
    .section h2 {{
      margin: 0 0 10px;
      font-size: 22px;
      letter-spacing: 0.06em;
    }}
    .loading {{
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      padding: 22px 0;
      gap: 8px;
      font-size: 13px;
    }}
    .spinner {{
      width: 20px;
      height: 20px;
      animation: spin 1s linear infinite;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 8px 6px;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
    .badge {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 10px;
      text-transform: uppercase;
    }}
    .ok {{ color: var(--ok); }}
    .warn {{ color: var(--warn); }}
    .err {{ color: var(--err); }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 12px;
    }}
    #graph {{
      min-height: 330px;
      border: 1px dashed var(--line);
      border-radius: 10px;
      display: grid;
      place-items: center;
      color: var(--muted);
      background: #0d111d;
    }}
    input, button {{
      width: 100%;
      background: #0f1524;
      color: #f4f7ff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 12px;
      font-family: inherit;
    }}
    button {{
      cursor: pointer;
      background: #192038;
      border-color: #36405e;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      color: #d4dbf3;
      font-size: 11px;
      line-height: 1.4;
      max-height: 260px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #0d111d;
    }}
    .links a {{
      color: #cdd6f3;
      text-decoration: none;
    }}
    .links a:hover {{ text-decoration: underline; }}
    .mini-pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 10px;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.04em;
      background: #0b101c;
    }}
    .meta-strip {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }}
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .card {{
      border: 1px solid var(--line);
      background: #0d111d;
      border-radius: 12px;
      padding: 14px;
      min-height: 140px;
      transition: border-color .18s ease, transform .18s ease, background .18s ease;
    }}
    .card:hover {{
      border-color: #47557b;
      transform: translateY(-1px);
      background: #10172a;
    }}
    .card-title {{
      font-size: 13px;
      font-weight: 700;
      margin: 0 0 8px;
      line-height: 1.45;
    }}
    .meta {{
      color: var(--muted);
      font-size: 11px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }}
    .summary {{
      color: #d7ddf4;
      font-size: 12px;
      line-height: 1.5;
      margin-bottom: 10px;
    }}
    .footer {{
      border-top: 1px solid var(--line);
      color: var(--muted);
      margin-top: 30px;
      padding: 18px 0 8px;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .footer-brand {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .footer-note {{
      color: #808aa6;
      font-size: 11px;
    }}
    .footer a {{
      color: #d6def8;
      text-decoration: none;
      margin-left: 12px;
      transition: color .18s ease, opacity .18s ease;
    }}
    .footer a::after {{
      content: " ↗";
      opacity: .8;
    }}
    .footer a:hover {{
      color: #ffffff;
    }}
    @media (max-width: 980px) {{
      .grid-2 {{ grid-template-columns: 1fr; }}
      .card-grid {{ grid-template-columns: 1fr; }}
      .nav {{ padding: 14px 16px; }}
      .page {{ padding: 18px 12px 30px; }}
      .nav-links {{ display: none; }}
      .menu-toggle {{ display: inline-flex; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="nav">
      <a class="logo" href="/fars">ANALEMMA</a>
      <nav class="nav-links">
        <a class="active" href="/fars">FARS</a>
        <a class="secondary" href="https://analemma.ai/#blog" target="_blank" rel="noopener noreferrer">BLOG</a>
        <a class="secondary" href="https://analemma.ai/about/" target="_blank" rel="noopener noreferrer">ABOUT</a>
      </nav>
      <button id="menu-toggle" class="menu-toggle" type="button" aria-label="Toggle menu" aria-expanded="false" aria-controls="mobile-sheet">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <line x1="4" x2="20" y1="6" y2="6"></line>
          <line x1="4" x2="20" y1="12" y2="12"></line>
          <line x1="4" x2="20" y1="18" y2="18"></line>
        </svg>
        <span class="sr-only">Toggle menu</span>
      </button>
    </div>
    <div id="mobile-sheet" class="mobile-sheet" hidden>
      <div class="mobile-sheet-panel" role="dialog" aria-modal="true" aria-labelledby="mobile-sheet-title" tabindex="-1">
        <div class="mobile-sheet-head">
          <div id="mobile-sheet-title" class="mobile-sheet-title">MENU</div>
          <button id="menu-close" class="menu-toggle" type="button" aria-label="Close menu" style="display:inline-flex">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="6" x2="18" y1="6" y2="18"></line>
              <line x1="6" x2="18" y1="18" y2="6"></line>
            </svg>
            <span class="sr-only">Close menu</span>
          </button>
        </div>
        <nav class="mobile-sheet-nav">
          <a href="/fars">FARS</a>
          <a class="external" href="https://analemma.ai/#blog" target="_blank" rel="noopener noreferrer">BLOG</a>
          <a class="external" href="https://analemma.ai/about/" target="_blank" rel="noopener noreferrer">ABOUT</a>
        </nav>
      </div>
    </div>
  </header>
  <main class="page">
    <section class="hero">
      <h1>FARS: Fully Automated Research System</h1>
      <p class="hero-sub">Analemma Live Streaming Platform - Real-time AI research demonstration</p>
      <div class="social">
        <a href="https://x.com/AnalemmaAI" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path></svg>
          <span>X / Follow</span>
        </a>
        <a href="https://www.youtube.com/@AnalemmaAI" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"></path></svg>
          <span>YouTube Channel</span>
        </a>
      </div>
      <div class="hero-image">
        {_hero_card_svg()}
      </div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>FARS DEPLOYMENTS</h2>
        <div class="links">
          <span id="deployments-count" class="mini-pill">Visible deployments: --</span>
        </div>
      </div>
      <div id="deployments-wrap" class="loading">{_loading_indicator_html("Loading deployments...")}</div>
    </section>

    <section class="section">
      <div class="section-head">
        <h2>RESEARCH RUNS</h2>
        <div class="links">
          <span id="runs-count" class="mini-pill">Visible runs: --</span>
          <span id="refresh-cadence" class="mini-pill">Refresh: 15s</span>
          <span id="refresh-countdown" class="mini-pill">Next refresh: --</span>
          <span id="last-updated" class="mini-pill">Last updated: --</span>
          <a href="/console">Advanced operations in console →</a>
        </div>
      </div>
      <div class="grid-2">
        <div style="grid-column:1 / -1">
          <div id="runs-body" class="loading">{_loading_indicator_html("Loading research runs...")}</div>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="section-head">
        <h2>LATEST RUN EVENTS</h2>
        <div class="links">
          <span id="events-count" class="mini-pill">Visible events: --</span>
        </div>
      </div>
      <div id="events-body" class="loading">{_loading_indicator_html("Loading latest run events...")}</div>
    </section>
    <footer class="footer">
      <div class="footer-brand">
        <div>© 2026 Analemma Intelligence. All rights reserved.</div>
        <div class="footer-note">Public live view for autonomous research progress.</div>
      </div>
      <div>
        <a href="https://analemma.ai/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a>
        <a href="https://analemma.ai/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
        <a href="https://analemma.ai/cookies" target="_blank" rel="noopener noreferrer">Cookie Policy</a>
        <a href="https://analemma.ai/about/" target="_blank" rel="noopener noreferrer">Join Us</a>
      </div>
    </footer>
  </main>

  <script>
    const API = "{api_prefix}";
    const REFRESH_INTERVAL_MS = 15000;
    const fmtStatus = (value) => {{
      const status = (value || "unknown").toLowerCase();
      const cls = status.includes("complete") || status.includes("ready") ? "ok" : (status.includes("fail") ? "err" : "warn");
      return `<span class="badge ${{cls}}">${{status}}</span>`;
    }};

    async function fetchJson(url, options={{}}) {{
      const res = await fetch(url, {{
        headers: {{ "Content-Type": "application/json" }},
        ...options,
      }});
      if (!res.ok) {{
        let detail = `${{res.status}} ${{res.statusText}}`;
        try {{
          const body = await res.json();
          if (body && body.detail) detail = body.detail;
        }} catch (_e) {{}}
        throw new Error(detail);
      }}
      return res.json();
    }}

    let lastFocusedElement = null;
    let refreshCountdownTimer = null;
    let nextRefreshAt = Date.now() + REFRESH_INTERVAL_MS;

    function formatIso(value) {{
      if (!value) return "-";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString();
    }}

    function updateRefreshCountdown() {{
      const node = document.getElementById("refresh-countdown");
      const seconds = Math.max(0, Math.ceil((nextRefreshAt - Date.now()) / 1000));
      node.textContent = `Next refresh: ${{seconds}}s`;
    }}

    function resetRefreshCountdown() {{
      nextRefreshAt = Date.now() + REFRESH_INTERVAL_MS;
      updateRefreshCountdown();
    }}

    function ensureRefreshTicker() {{
      if (refreshCountdownTimer) return;
      refreshCountdownTimer = window.setInterval(updateRefreshCountdown, 1000);
    }}

    function updateLastUpdated(value) {{
      const node = document.getElementById("last-updated");
      node.textContent = `Last updated: ${{formatIso(value)}}`;
    }}

    function updateVisibleCounts({{ deployments = 0, runs = 0, events = 0 }}) {{
      document.getElementById("deployments-count").textContent = `Visible deployments: ${{deployments}}`;
      document.getElementById("runs-count").textContent = `Visible runs: ${{runs}}`;
      document.getElementById("events-count").textContent = `Visible events: ${{events}}`;
    }}

    function renderDeployments(batches) {{
      const wrap = document.getElementById("deployments-wrap");
      if (!batches.length) {{
        wrap.innerHTML = '<div class="loading"><span>No deployments yet.</span></div>';
        return 0;
      }}
      wrap.innerHTML = `<div class="card-grid">
        ${{batches.map(item => `
          <article class="card">
            <div class="card-title">${{item.kind.toUpperCase()}} · <code>${{item.batch_id}}</code></div>
            <div class="meta-strip">
              <span class="mini-pill">created: ${{item.created_at || "-"}}</span>
            </div>
            <div class="summary">${{
              item.kind === "reconcile"
                ? "Reconciliation bundle available for public progress tracking."
                : "Deployment record available for public progress tracking."
            }}</div>
          </article>`).join("")}}
      </div>`;
      return batches.length;
    }}

    function renderRuns(runs) {{
      const body = document.getElementById("runs-body");
      if (!runs.length) {{
        body.innerHTML = '<div class="loading"><span>No research runs yet.</span></div>';
        return 0;
      }}
      body.innerHTML = `<div class="card-grid">
        ${{runs.map(run => `
          <article class="card">
            <div class="card-title">Run #${{run.id}} ${{fmtStatus(run.status)}}</div>
            <div class="meta-strip">
              <span class="mini-pill">status: ${{run.status}}</span>
            </div>
            <div class="summary">Research run status is visible here. Full details remain in the operator console.</div>
          </article>`).join("")}}
      </div>`;
      return runs.length;
    }}

    function renderEvents(events) {{
      const body = document.getElementById("events-body");
      if (!events.length) {{
        body.innerHTML = '<div class="loading"><span>No run events yet.</span></div>';
        return 0;
      }}
      body.innerHTML = `<div class="card-grid">
        ${{events.map(event => `
          <article class="card">
            <div class="card-title">Run #${{event.run_id}} ${{fmtStatus(event.status)}}</div>
            <div class="meta-strip">
              <span class="mini-pill">${{event.event_type}}</span>
              <span class="mini-pill">${{event.source}}</span>
            </div>
            <div class="summary">${{formatIso(event.time_created)}}</div>
          </article>`).join("")}}
      </div>`;
      return events.length;
    }}

    async function refreshLive() {{
      const [_readiness, publicData, eventsData] = await Promise.all([
        fetchJson(`${{API}}/health/readiness`),
        fetchJson(`/fars/data?limit=12`),
        fetchJson(`/fars/events?limit=16`),
      ]);
      const deploymentCount = renderDeployments(publicData.deployments || []);
      const runCount = renderRuns(publicData.research_runs || []);
      const eventCount = renderEvents(eventsData.events || []);
      updateLastUpdated(eventsData.generated_at || publicData.generated_at);
      updateVisibleCounts({{
        deployments: deploymentCount,
        runs: runCount,
        events: eventCount,
      }});
      resetRefreshCountdown();
    }}

    function setMenuOpen(open) {{
      const sheet = document.getElementById("mobile-sheet");
      const toggle = document.getElementById("menu-toggle");
      const panel = document.querySelector(".mobile-sheet-panel");
      const close = document.getElementById("menu-close");
      const main = document.querySelector("main");
      const nav = document.querySelector(".nav");
      if (open) {{
        lastFocusedElement = document.activeElement;
      }}
      sheet.hidden = !open;
      sheet.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
      if (main) {{
        main.inert = open;
        main.setAttribute("aria-hidden", open ? "true" : "false");
      }}
      if (nav) {{
        nav.inert = open;
        nav.setAttribute("aria-hidden", open ? "true" : "false");
      }}
      if (open) {{
        window.requestAnimationFrame(() => {{
          close.focus();
        }});
      }} else {{
        if (lastFocusedElement && typeof lastFocusedElement.focus === "function" && document.contains(lastFocusedElement)) {{
          lastFocusedElement.focus();
        }} else {{
          toggle.focus();
        }}
      }}
    }}

    function toggleMenu() {{
      const sheet = document.getElementById("mobile-sheet");
      setMenuOpen(sheet.hidden);
    }}

    function trapMenuFocus(event) {{
      if (event.key !== "Tab") return;
      const panel = document.querySelector(".mobile-sheet-panel");
      if (!panel) return;
      const focusables = Array.from(
        panel.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')
      );
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (event.shiftKey && document.activeElement === first) {{
        event.preventDefault();
        last.focus();
      }} else if (!event.shiftKey && document.activeElement === last) {{
        event.preventDefault();
        first.focus();
      }}
    }}

    document.getElementById("menu-toggle").addEventListener("click", toggleMenu);
    document.getElementById("menu-close").addEventListener("click", () => setMenuOpen(false));
    document.getElementById("mobile-sheet").addEventListener("click", (event) => {{
      if (event.target.id === "mobile-sheet") {{
        setMenuOpen(false);
      }}
    }});
    document.querySelector(".mobile-sheet-panel").addEventListener("keydown", trapMenuFocus);
    document.querySelectorAll(".mobile-sheet-nav a").forEach((node) => {{
      node.addEventListener("click", () => setMenuOpen(false));
    }});
    document.addEventListener("keydown", (event) => {{
      if (event.key === "Escape" && !document.getElementById("mobile-sheet").hidden) {{
        setMenuOpen(false);
      }}
    }});

    Promise.all([refreshLive()]).catch((err) => {{
      console.error(err);
    }});
    ensureRefreshTicker();
    updateRefreshCountdown();
    setInterval(() => {{
      refreshLive().catch(() => {{}});
    }}, REFRESH_INTERVAL_MS);
  </script>
</body>
</html>
"""


def _console_login_html(error: str | None) -> str:
    error_block = f'<p style="color:#f46b6b;margin:0 0 12px">{error}</p>' if error else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>FARS Console Login</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #090b11;
      color: #f4f7ff;
      font-family: "IBM Plex Mono", ui-monospace, monospace;
    }}
    .card {{
      width: min(420px, calc(100vw - 32px));
      border: 1px solid #23283a;
      border-radius: 12px;
      background: #11141f;
      padding: 20px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 22px; }}
    p {{ color: #9aa3bb; font-size: 13px; }}
    input, button {{
      width: 100%;
      box-sizing: border-box;
      border-radius: 8px;
      padding: 10px 12px;
      font-family: inherit;
      font-size: 13px;
    }}
    input {{ border: 1px solid #2c3550; background: #0d1322; color: #fff; margin: 10px 0 12px; }}
    button {{ border: 1px solid #3b4a72; background: #18223d; color: #fff; cursor: pointer; }}
    a {{ color: #d8def4; text-decoration: none; }}
  </style>
</head>
<body>
  <form class="card" method="post" action="/console/login">
    <h1>Operator Login</h1>
    <p>Enter the configured operator token to access the advanced console.</p>
    {error_block}
    <input type="password" name="token" placeholder="Operator token" autofocus />
    <button type="submit">Enter Console</button>
    <p style="margin-top:12px"><a href="/fars">Back to FARS</a></p>
  </form>
</body>
</html>"""


def _hero_card_svg() -> str:
    return """<svg viewBox="0 0 1000 625" width="100%" height="100%" role="img" aria-label="FARS live deployment completed card" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#11192c"/>
      <stop offset="100%" stop-color="#06080f"/>
    </linearGradient>
    <linearGradient id="glow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#7aa2ff" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#b4c8ff" stop-opacity="0.35"/>
    </linearGradient>
  </defs>
  <rect width="1000" height="625" fill="url(#bg)"/>
  <circle cx="220" cy="180" r="180" fill="#1d2b51" opacity="0.38"/>
  <circle cx="770" cy="140" r="150" fill="#18274c" opacity="0.28"/>
  <circle cx="820" cy="480" r="190" fill="#13203f" opacity="0.25"/>
  <rect x="62" y="62" width="876" height="501" rx="22" fill="none" stroke="#27355c"/>
  <text x="86" y="110" fill="#d9e4ff" font-size="16" font-family="IBM Plex Mono, monospace" letter-spacing="3">ANALEMMA</text>
  <text x="86" y="220" fill="#ffffff" font-size="54" font-family="Arial, Helvetica, sans-serif" font-weight="700">FARS: Fully Automated</text>
  <text x="86" y="280" fill="#ffffff" font-size="54" font-family="Arial, Helvetica, sans-serif" font-weight="700">Research System</text>
  <text x="88" y="330" fill="#9fb0d8" font-size="22" font-family="IBM Plex Mono, monospace">Real-time AI research demonstration</text>
  <rect x="86" y="384" width="300" height="2" fill="url(#glow)"/>
  <text x="86" y="430" fill="#dfe8ff" font-size="20" font-family="IBM Plex Mono, monospace">FARS DEPLOYMENTS</text>
  <text x="86" y="468" fill="#9aa7ca" font-size="18" font-family="IBM Plex Mono, monospace">Loading deployments...</text>
  <text x="86" y="528" fill="#dfe8ff" font-size="20" font-family="IBM Plex Mono, monospace">RESEARCH RUNS</text>
  <text x="86" y="566" fill="#9aa7ca" font-size="18" font-family="IBM Plex Mono, monospace">Loading research runs...</text>
</svg>"""


def _loading_indicator_html(text: str) -> str:
    return f"""<svg class="spinner" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
</svg><span>{text}</span>"""

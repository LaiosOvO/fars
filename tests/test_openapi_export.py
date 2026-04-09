from pathlib import Path
import json
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_openapi_can_be_exported() -> None:
    subprocess.run(
        ["python", "scripts/export_openapi.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output_path = ROOT / ".artifacts" / "openapi" / "openapi.json"
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["info"]["title"] == "FARS Paper Knowledge Layer"
    assert "/api/research-loops/run" in payload["paths"]
    assert "/api/research-loops/batch-run" in payload["paths"]
    assert "/api/research-loops/reconcile" in payload["paths"]
    assert "/api/research-loops/batches" in payload["paths"]
    assert "/api/research-loops/batches/{batch_id}/manifest" in payload["paths"]
    assert "/api/research-loops/batches/{batch_id}/download" in payload["paths"]
    assert "/api/research-loops/batches/{batch_id}/summary/download" in payload["paths"]
    assert "/api/research-loops/batches/{batch_id}/items/download" in payload["paths"]
    assert "/api/research-loops/batches/{batch_id}/reconciliation/download" in payload["paths"]

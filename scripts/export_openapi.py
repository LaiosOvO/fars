from __future__ import annotations

import json
from pathlib import Path

from fars_kg.api.app import create_app


def main() -> None:
    app = create_app()
    output_dir = Path(".artifacts") / "openapi"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "openapi.json"
    output_path.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()

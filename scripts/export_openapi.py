"""Dump the full FastAPI OpenAPI spec to a local file.

Imports the app factory directly so no running server is required. The
output is consumed by `openapi-typescript` to generate the frontend's
`src/lib/api-types.ts`, eliminating the hand-synced drift between
`schemas.py` and `frontend/src/lib/types.ts`.

Usage:
    python scripts/export_openapi.py [output_path]

Default output path is `openapi.json` at the repo root.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql://openapi-export/noop")
os.environ.setdefault("DISABLE_AUTH", "1")

from world_of_taxonomy.api.app import create_app  # noqa: E402


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
    app = create_app()
    spec = app.openapi()
    output.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"Wrote {output} ({len(spec.get('paths', {}))} paths)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

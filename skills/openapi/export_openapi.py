"""Fetch the WorldOfTaxonomy OpenAPI spec and trim it to the endpoints a
ChatGPT Custom GPT Action should expose.

Usage:
    python skills/openapi/export_openapi.py > worldoftaxonomy_gpt_actions.json

Custom GPT Actions have a 30-operation soft limit and prefer compact schemas,
so we keep only the endpoints most useful to a conversational agent.
"""

import json
import sys
from urllib.request import urlopen

SPEC_URL = "https://worldoftaxonomy.com/api/v1/openapi.json"

KEEP_PATHS = {
    "/systems",
    "/systems/{system_id}",
    "/systems/{system_id}/nodes/{code}",
    "/systems/{system_id}/nodes/{code}/children",
    "/systems/{system_id}/nodes/{code}/ancestors",
    "/systems/{system_id}/nodes/{code}/siblings",
    "/systems/{system_id}/nodes/{code}/equivalences",
    "/search",
    "/classify",
    "/equivalences/stats",
}


def main() -> int:
    with urlopen(SPEC_URL) as resp:
        spec = json.load(resp)

    spec["servers"] = [{"url": "https://worldoftaxonomy.com/api/v1"}]
    spec["paths"] = {p: v for p, v in spec.get("paths", {}).items() if p in KEEP_PATHS}

    json.dump(spec, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

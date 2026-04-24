"""WHO ICD-11 API client + entity renderer.

Used by ``scripts/backfill_icd11_api_descriptions.py`` to replace the
thin CodingNote-only descriptions (see ``icd11_descriptions.py``) with
the full Definition / Long definition / Inclusions / Exclusions /
Coding note blocks that live only behind the authenticated ICD-11 API.

Auth: OAuth2 client credentials against
``https://icdaccessmanagement.who.int/connect/token`` with scope
``icdapi_access``. Tokens expire after 1 hour -- callers must refresh.

Entity fetches use ``https://id.who.int/icd/release/11/{release}/mms/{id}``
(the Simple Tabulation file provides the linearization URIs directly,
so the ``/codeinfo/`` lookup is not needed).
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable

_EM_DASH = "\u2014"
_BOM = "\ufeff"

ICD11_TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"
ICD11_API_HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "en",
    "API-Version": "v2",
}


_RELEASE_SEGMENT = re.compile(r"/release/11/(\d{4}-\d{2}/)?mms/")


def rewrite_release(uri: str, release: str) -> str:
    """Return a URI pointing at the requested ICD-11 release.

    The Simple Tabulation URIs omit the release date
    (``/release/11/mms/123``). The API's linearization endpoints need
    it (``/release/11/2026-01/mms/123``), so we rewrite on the fly.
    Also upgrades ``http://`` to ``https://`` so we avoid a 301 round
    trip per request.
    """
    out = _RELEASE_SEGMENT.sub(f"/release/11/{release}/mms/", uri, count=1)
    if out.startswith("http://"):
        out = "https://" + out[len("http://"):]
    return out


def parse_code_to_uri_map(path: Path) -> Dict[str, str]:
    """Return ``{code: LinearizationURI}`` from the Simple Tabulation TSV.

    Accepts the raw ``.txt`` or the WHO-style ZIP. Used by the API
    backfill to avoid an extra ``/codeinfo/`` round-trip per code.
    """
    out: Dict[str, str] = {}
    for header, row in _iter_rows(path):
        code = _col(row, header, "Code").strip()
        uri = _col(row, header, "Linearization URI").strip()
        if code and uri:
            out[code] = uri
    return out


def _col(row: list[str], header: list[str], name: str) -> str:
    try:
        idx = header.index(name)
    except ValueError:
        return ""
    if idx >= len(row):
        return ""
    return row[idx]


def _iter_rows(path: Path):
    for raw in _iter_text(path):
        lines = raw.splitlines()
        if not lines:
            continue
        header = lines[0].lstrip(_BOM).split("\t")
        for line in lines[1:]:
            if not line.strip():
                continue
            yield header, line.split("\t")


def _iter_text(path: Path):
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            members = [
                n for n in z.namelist()
                if n.lower().endswith(".txt") and "icd-11" in n.lower()
            ]
            for name in members:
                with z.open(name) as fh:
                    yield fh.read().decode("utf-8", errors="replace")
        return
    yield p.read_text(encoding="utf-8", errors="replace")


def render_entity(entity: Dict[str, Any]) -> str:
    """Return a markdown description for an ICD-11 MMS entity.

    Returns an empty string when the entity has no clinical content
    worth storing (definition, long definition, inclusion, exclusion,
    or coding note). The caller should skip rows with an empty render
    so we never overwrite ``classification_node.description`` with ''.
    """
    blocks: list[str] = []

    definition = _value(entity.get("definition"))
    if definition:
        blocks.append(f"**Definition:** {definition}")

    long_def = _value(entity.get("longDefinition"))
    if long_def:
        blocks.append(f"**Long definition:** {long_def}")

    inclusions = list(_labels(entity.get("inclusion") or []))
    if inclusions:
        blocks.append("**Inclusions:**\n" + "\n".join(f"- {x}" for x in inclusions))

    exclusions = list(_labels(entity.get("exclusion") or []))
    if exclusions:
        blocks.append("**Exclusions:**\n" + "\n".join(f"- {x}" for x in exclusions))

    coding = entity.get("codingNote")
    if isinstance(coding, dict):
        notes = [
            _value(n)
            for n in coding.get("note") or []
        ]
        notes = [n for n in notes if n]
        if notes:
            blocks.append("**Coding note:**\n" + "\n".join(f"- {n}" for n in notes))

    rendered = "\n\n".join(blocks)
    return rendered.replace(_EM_DASH, "-")


def _value(field: Any) -> str:
    if not isinstance(field, dict):
        return ""
    return (field.get("@value") or "").strip()


def _labels(items: Iterable[Any]) -> Iterable[str]:
    for item in items:
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        text = _value(label)
        if text:
            yield text

"""Parser for ESCO occupation + skill descriptions from the JSON-LD dump.

ESCO publishes the whole taxonomy as one large JSON-LD file inside a
ZIP archive (``esco-v1.2.1.json-ld``, roughly 650 MB uncompressed).
Every record in the top-level ``@graph`` array carries a
``description`` list of language-tagged ``NodeLiteral`` entries. We
pick the English ``nodeLiteral`` and key it by the UUID portion of the
record's URI, which matches how the ESCO ingester stores codes in
``classification_node``.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

import ijson

_EM_DASH = "\u2014"
_UUID_PATTERN = re.compile(
    r"/esco/(?:occupation|skill)/"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
)


def extract_uuid(uri: Optional[str]) -> Optional[str]:
    """Return the UUID portion of an ESCO occupation/skill URI."""
    if not uri:
        return None
    m = _UUID_PATTERN.search(uri)
    return m.group(1) if m else None


def extract_english_description(record: Dict[str, Any]) -> str:
    """Return the English ``nodeLiteral`` from an ESCO JSON-LD record.

    Returns an empty string when no English literal is available. The
    caller should skip rows with an empty description rather than write
    an empty string back to the DB.
    """
    desc = record.get("description") or []
    if not isinstance(desc, list):
        return ""
    for entry in desc:
        if not isinstance(entry, dict):
            continue
        if entry.get("language") != "en":
            continue
        text = (entry.get("nodeLiteral") or "").strip()
        if text:
            return text.replace(_EM_DASH, "-")
    return ""


def parse_esco_descriptions(
    path: Path,
    *,
    concept_type: str,
) -> Dict[str, str]:
    """Stream the ESCO JSON-LD ZIP and return ``{uuid: description}``.

    ``concept_type`` must be one of ``"occupation"`` or ``"skill"``.
    The parser reads the archive without extracting it to disk and
    matches records whose ``type`` array contains ``esco:Occupation``
    or ``esco:Skill`` accordingly.
    """
    if concept_type not in ("occupation", "skill"):
        raise ValueError(f"concept_type must be 'occupation' or 'skill', got {concept_type!r}")

    wanted = "esco:Occupation" if concept_type == "occupation" else "esco:Skill"
    out: Dict[str, str] = {}
    with zipfile.ZipFile(path) as z:
        member = _find_jsonld_member(z)
        with z.open(member) as fh:
            for record in ijson.items(fh, "@graph.item"):
                types = record.get("type") or record.get("@type") or []
                if isinstance(types, str):
                    types = [types]
                if wanted not in types:
                    continue
                uri = record.get("uri") or record.get("@id")
                uuid = extract_uuid(uri)
                if not uuid:
                    continue
                description = extract_english_description(record)
                if description:
                    out[uuid] = description
    return out


def _find_jsonld_member(z: zipfile.ZipFile) -> str:
    for name in z.namelist():
        if name.endswith(".json-ld"):
            return name
    raise FileNotFoundError("No .json-ld member found in ESCO archive")

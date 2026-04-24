"""Parser for the NLM MeSH descriptor XML.

NLM publishes MeSH as ``descYYYY.xml`` (and an equivalent ``.xml.gz``).
The structural ingester at :mod:`world_of_taxonomy.ingest.mesh` keeps
the descriptor UI and its preferred name. This module surfaces the
``<ScopeNote>`` (definition), ``<TreeNumberList>`` (hierarchy
placement), and entry terms from the preferred concept into
``classification_node.description`` as structured markdown.

The file is ~300 MB uncompressed, so ``iterparse`` is used to stream
one descriptor record at a time and clear the element to keep memory
bounded.
"""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional
from xml.etree import ElementTree as ET

_EM_DASH = "\u2014"


def parse_mesh_descriptor_xml(path: Path) -> Dict[str, str]:
    """Return ``{descriptor_ui: markdown_description}`` for every record.

    Accepts ``.xml`` or ``.xml.gz``. Records without a definition,
    tree numbers, or synonyms are skipped (title alone carries no
    additional information).
    """
    out: Dict[str, str] = {}
    with _open_stream(path) as fh:
        for _, record in _iterparse_descriptors(fh):
            ui = _findtext(record, "DescriptorUI")
            if not ui:
                _clear(record)
                continue
            rendered = _render(record)
            if rendered:
                out[ui] = rendered
            _clear(record)
    return out


def _render(record: ET.Element) -> Optional[str]:
    blocks: list[str] = []

    preferred = _preferred_concept(record)

    scope_note = _findtext(preferred, "ScopeNote") if preferred is not None else ""
    if scope_note:
        blocks.append(f"**Definition:**\n{scope_note}")

    tree_numbers = [
        tn.text.strip()
        for tn in record.findall("TreeNumberList/TreeNumber")
        if tn is not None and tn.text
    ]
    if tree_numbers:
        blocks.append(
            "**Tree numbers:**\n"
            + "\n".join(f"- {tn}" for tn in tree_numbers)
        )

    synonyms = _collect_synonyms(preferred) if preferred is not None else []
    if synonyms:
        blocks.append(
            "**Synonyms:**\n"
            + "\n".join(f"- {s}" for s in synonyms)
        )

    if not blocks:
        return None
    return "\n\n".join(blocks).replace(_EM_DASH, "-")


def _preferred_concept(record: ET.Element) -> Optional[ET.Element]:
    for concept in record.findall("ConceptList/Concept"):
        if concept.get("PreferredConceptYN") == "Y":
            return concept
    return None


def _collect_synonyms(concept: ET.Element) -> list[str]:
    preferred_name = _findtext(concept, "ConceptName/String").strip()
    seen: set[str] = set()
    out: list[str] = []
    for term in concept.findall("TermList/Term"):
        if term.get("IsPermutedTermYN") == "Y":
            continue
        if term.get("ConceptPreferredTermYN") == "Y":
            continue
        value = _findtext(term, "String").strip()
        if not value or value == preferred_name or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _findtext(elem: Optional[ET.Element], path: str) -> str:
    if elem is None:
        return ""
    node = elem.find(path)
    if node is None or node.text is None:
        return ""
    return " ".join(node.text.split())


def _clear(elem: ET.Element) -> None:
    elem.clear()


def _iterparse_descriptors(fh) -> Iterator[tuple[str, ET.Element]]:
    """Yield (event, element) only for end-of-DescriptorRecord events."""
    for event, elem in ET.iterparse(fh, events=("end",)):
        if elem.tag == "DescriptorRecord":
            yield event, elem


def _open_stream(path: Path) -> Iterable:
    p = Path(path)
    if p.suffix.lower() == ".gz":
        return gzip.open(p, "rb")
    return open(p, "rb")

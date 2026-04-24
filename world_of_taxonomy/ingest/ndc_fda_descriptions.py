"""Parser for the FDA National Drug Code (NDC) product file.

The FDA publishes the NDC Directory as a tab-delimited archive with
``product.txt`` and ``package.txt``. The structural ingester at
:mod:`world_of_taxonomy.ingest.ndc_fda` already consumes ``product.txt``
for hierarchy and titles. This module surfaces the richer per-product
metadata -- active ingredient, strength, dosage form, route, labeler,
marketing category, pharmacologic class, DEA schedule -- into
``classification_node.description`` as structured markdown.

Codes are kept in the labeler-product form (``0002-0152``) matching
the ``PRODUCTNDC`` column and the DB layout.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, Iterable, Optional

_EM_DASH = "\u2014"


def parse_ndc_product_descriptions(path: Path) -> Dict[str, str]:
    """Return ``{productndc: markdown_description}`` for every non-excluded row.

    Accepts either a plain ``product.txt`` file or a ZIP archive
    containing it (any member whose name contains ``product``).
    """
    out: Dict[str, str] = {}
    for header, row in _iter_rows(path):
        code = _col(row, header, "PRODUCTNDC")
        if not code:
            continue
        excluded = _col(row, header, "NDC_EXCLUDE_FLAG").strip().upper()
        if excluded in ("Y", "YES"):
            continue
        desc = _render(row, header)
        if desc:
            out[code] = desc
    return out


def _render(row: list[str], header: list[str]) -> Optional[str]:
    blocks: list[str] = []

    type_name = _col(row, header, "PRODUCTTYPENAME")
    if type_name:
        blocks.append(f"**Product type:** {_titlecase(type_name)}")

    substance = _col(row, header, "SUBSTANCENAME")
    if substance:
        blocks.append(f"**Active ingredient:** {substance}")

    strength = _col(row, header, "ACTIVE_NUMERATOR_STRENGTH")
    unit = _col(row, header, "ACTIVE_INGRED_UNIT")
    if strength or unit:
        combined = f"{strength} {unit}".strip()
        if combined:
            blocks.append(f"**Strength:** {combined}")

    form = _col(row, header, "DOSAGEFORMNAME")
    if form:
        blocks.append(f"**Dosage form:** {_titlecase(form)}")

    route = _col(row, header, "ROUTENAME")
    if route:
        blocks.append(f"**Route:** {_titlecase(route)}")

    labeler = _col(row, header, "LABELERNAME")
    if labeler:
        blocks.append(f"**Labeler:** {labeler}")

    category = _col(row, header, "MARKETINGCATEGORYNAME")
    application = _col(row, header, "APPLICATIONNUMBER")
    if category:
        if application:
            blocks.append(f"**Marketing category:** {category} ({application})")
        else:
            blocks.append(f"**Marketing category:** {category}")

    pharm = _col(row, header, "PHARM_CLASSES")
    if pharm:
        blocks.append(f"**Pharmacologic class:** {pharm}")

    dea = _col(row, header, "DEASCHEDULE")
    if dea:
        blocks.append(f"**DEA schedule:** {dea}")

    if not blocks:
        return None
    rendered = "\n\n".join(blocks)
    return rendered.replace(_EM_DASH, "-")


def _col(row: list[str], header: list[str], name: str) -> str:
    try:
        idx = header.index(name)
    except ValueError:
        return ""
    if idx >= len(row):
        return ""
    return row[idx].strip()


def _titlecase(value: str) -> str:
    """Title-case a shouting-caps field without mangling punctuation."""
    if not value:
        return value
    if value != value.upper():
        return value
    return value.title()


def _iter_rows(path: Path) -> Iterable[tuple[list[str], list[str]]]:
    for raw in _iter_text(path):
        lines = raw.splitlines()
        if not lines:
            continue
        header = lines[0].split("\t")
        for line in lines[1:]:
            if not line.strip():
                continue
            yield header, line.split("\t")


def _iter_text(path: Path) -> Iterable[str]:
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            members = [
                n for n in z.namelist()
                if "product" in n.lower() and n.lower().endswith(".txt")
            ]
            for name in members:
                with z.open(name) as fh:
                    yield fh.read().decode("utf-8", errors="replace")
        return
    yield p.read_text(encoding="utf-8", errors="replace")

"""Backfill NIC 2008 4-digit class descriptions from the MOSPI PDF.

Source: ``data/nic/nic_2008_publication.pdf`` (Central Statistical
Organisation publication, ~1.4 MB, 193 pages). Downloaded once from
``https://www.mospi.gov.in/.../nic_2008_17apr09.pdf`` and cached
locally; gitignored under ``data/*``.

Extracts the 4-digit class explanatory notes from the "Detailed
Structure" section and applies them to ``nic_2008``. Other code
levels (sections, divisions, groups, 5-digit subclasses) are not
covered because the PDF only carries titles for those (which we
already have in the DB).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import urllib.request
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from pypdf import PdfReader

from world_of_taxonomy.ingest.descriptions import apply_descriptions
from world_of_taxonomy.ingest.nic2008_pdf import extract_class_notes


_SOURCE_URL = (
    "https://www.mospi.gov.in/sites/default/files/main_menu/"
    "national_industrial_classification/nic_2008_17apr09.pdf"
)
_PDF_PATH = Path("data/nic/nic_2008_publication.pdf")
_STRUCTURED_FROM_PAGE = 35
_SYSTEM_ID = "nic_2008"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_downloaded(root: Path) -> Path:
    pdf = root / _PDF_PATH
    if pdf.exists() and pdf.stat().st_size > 1_000_000:
        return pdf
    pdf.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {_SOURCE_URL}...")
    req = urllib.request.Request(
        _SOURCE_URL,
        headers={"User-Agent": "Mozilla/5.0 WorldOfTaxonomy-backfill"},
    )
    with urllib.request.urlopen(req) as resp, pdf.open("wb") as dst:
        while chunk := resp.read(1 << 20):
            dst.write(chunk)
    print(f"  Saved to {pdf} ({pdf.stat().st_size:,} bytes)")
    return pdf


def _structured_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(
        (p.extract_text() or "")
        for p in reader.pages[_STRUCTURED_FROM_PAGE:]
    )


async def _run(dry_run: bool) -> int:
    root = _project_root()
    load_dotenv(root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        return 1

    pdf = _ensure_downloaded(root)
    print(f"  Reading {pdf.name}...")
    text = _structured_text(pdf)
    print(f"  Structured-section text: {len(text):,} chars")

    mapping = extract_class_notes(text)
    print(f"  Extracted notes for {len(mapping):,} 4-digit classes")

    conn = await asyncpg.connect(database_url, statement_cache_size=0)
    try:
        before = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND LENGTH(code) = 4 "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Empty 4-digit rows before: {before:,}")

        if dry_run:
            empty_codes = await conn.fetch(
                "SELECT code FROM classification_node "
                f"WHERE system_id = '{_SYSTEM_ID}' AND LENGTH(code) = 4 "
                "AND (description IS NULL OR description = '')"
            )
            would = sum(1 for r in empty_codes if r["code"] in mapping)
            print(f"  Dry run: would update {would:,} rows")
            return 0

        updated = await apply_descriptions(conn, _SYSTEM_ID, mapping)
        after = await conn.fetchval(
            "SELECT COUNT(*) FROM classification_node "
            f"WHERE system_id = '{_SYSTEM_ID}' AND LENGTH(code) = 4 "
            "AND (description IS NULL OR description = '')"
        )
        print(f"  Updated {updated:,} rows; 4-digit still-empty {after:,}")
    finally:
        await conn.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return asyncio.run(_run(dry_run=args.dry_run))


if __name__ == "__main__":
    sys.exit(main())

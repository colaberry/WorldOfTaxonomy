"""NDC full ingester (112K products from FDA National Drug Code Directory).

The National Drug Code (NDC) Directory contains product listing data for
all finished drugs: prescription, OTC, biologics, vaccines, etc.

Source: US Food and Drug Administration (public domain, US government)
URL: https://www.accessdata.fda.gov/cder/ndctext.zip
Data file: data/ndc_product.zip containing product.txt

Format: tab-delimited with header row. Key columns:
  PRODUCTNDC: NDC code (labeler-product format, e.g. 0002-0152)
  PRODUCTTYPENAME: e.g. HUMAN PRESCRIPTION DRUG
  PROPRIETARYNAME: brand name (e.g. Zepbound)
  NONPROPRIETARYNAME: generic name (e.g. tirzepatide)
  DOSAGEFORMNAME: e.g. INJECTION, SOLUTION
  NDC_EXCLUDE_FLAG: Y if excluded from NDC directory

Hierarchy:
  Product Type (level 1)  -> 7 categories, parent = None
  Dosage Form (level 2)   -> ~136 forms, parent = product type
  Individual NDC (level 3) -> ~112K products, parent = dosage form

Overlap check: NDC identifies specific drug products by manufacturer.
Different from RxNorm (drug concepts), ATC (pharmacological classification),
and NCI Thesaurus (biomedical vocabulary). No duplication.

Verified 2025-04-15: 112,940 products, 7 types, 136 dosage forms.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional

from world_of_taxonomy.ingest.hash_util import sha256_of_file

CHUNK = 500

_SYSTEM_ROW = (
    "ndc_fda",
    "NDC",
    "National Drug Code Directory (FDA)",
    "2025",
    "United States",
    "US Food and Drug Administration (FDA)",
)

_SOURCE_URL = "https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory"
_DATA_PROVENANCE = "official_download"
_LICENSE = "Public Domain (US Government)"

_DEFAULT_ZIP = "data/ndc_product.zip"
_EXPECTED_MIN = 90_000

# Product type codes for level 1 hierarchy
NDC_PRODUCT_TYPES: list[tuple[str, str]] = [
    ("NDC-RX", "Human Prescription Drug"),
    ("NDC-OTC", "Human OTC Drug"),
    ("NDC-ALG", "Non-Standardized Allergenic"),
    ("NDC-PLS", "Plasma Derivative"),
    ("NDC-VAC", "Vaccine"),
    ("NDC-SAL", "Standardized Allergenic"),
    ("NDC-CEL", "Cellular Therapy"),
]

# Map raw FDA type names to our codes
_TYPE_CODE_MAP = {
    "HUMAN PRESCRIPTION DRUG": "NDC-RX",
    "HUMAN OTC DRUG": "NDC-OTC",
    "NON-STANDARDIZED ALLERGENIC": "NDC-ALG",
    "PLASMA DERIVATIVE": "NDC-PLS",
    "VACCINE": "NDC-VAC",
    "STANDARDIZED ALLERGENIC": "NDC-SAL",
    "CELLULAR THERAPY": "NDC-CEL",
}


def _find_data_file() -> Optional[str]:
    """Auto-detect the NDC data file."""
    p = Path(_DEFAULT_ZIP)
    if p.exists():
        return str(p)
    zips = sorted(Path("data").glob("ndc*.zip"))
    if zips:
        return str(zips[-1])
    return None


def _make_form_code(type_code: str, form_name: str) -> str:
    """Create a deterministic code for a dosage form under a product type."""
    # Normalize form name to a short slug
    slug = form_name.upper().replace(" ", "_").replace(",", "").replace("/", "_")
    slug = slug.replace("__", "_").strip("_")[:30]
    return f"{type_code}.{slug}"


def parse_ndc_products(path: str) -> list[tuple[str, str, int, Optional[str]]]:
    """Parse FDA NDC product file into (code, title, level, parent_code) tuples.

    Returns product type nodes (level 1), dosage form nodes (level 2),
    and individual NDC product nodes (level 3).
    """
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            prod_files = [f for f in z.namelist() if "product" in f.lower()]
            if not prod_files:
                raise FileNotFoundError(f"No product file found in {path}")
            raw = z.read(prod_files[0]).decode("utf-8", errors="replace")
    else:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")

    lines = raw.splitlines()
    if not lines:
        return []

    header = lines[0].split("\t")
    col = {name: i for i, name in enumerate(header)}

    ndc_idx = col.get("PRODUCTNDC", 0)
    type_idx = col.get("PRODUCTTYPENAME", 2)
    prop_idx = col.get("PROPRIETARYNAME", 3)
    nonprop_idx = col.get("NONPROPRIETARYNAME", 5)
    form_idx = col.get("DOSAGEFORMNAME", 6)
    excl_idx = col.get("NDC_EXCLUDE_FLAG", 18)

    # Phase 1: collect products and discover dosage forms
    type_code_map = dict(_TYPE_CODE_MAP)
    form_codes: dict[str, str] = {}  # (type_code, form_name) key -> form_code
    products: list[tuple[str, str, str, str]] = []  # (ndc, title, type_code, form_code)

    for line in lines[1:]:
        cols = line.split("\t")
        if len(cols) <= max(ndc_idx, type_idx, form_idx):
            continue

        # Skip excluded products
        if len(cols) > excl_idx and cols[excl_idx].strip().upper() in ("Y", "YES"):
            continue

        ndc = cols[ndc_idx].strip()
        if not ndc:
            continue

        type_name = cols[type_idx].strip()
        prop_name = cols[prop_idx].strip() if len(cols) > prop_idx else ""
        nonprop_name = cols[nonprop_idx].strip() if len(cols) > nonprop_idx else ""
        form_name = cols[form_idx].strip() if len(cols) > form_idx else ""

        # Build display title: "Brand Name (generic)" or just generic
        if prop_name and nonprop_name:
            title = f"{prop_name} ({nonprop_name})"
        elif prop_name:
            title = prop_name
        elif nonprop_name:
            title = nonprop_name
        else:
            title = ndc

        # Replace em-dashes
        title = title.replace("\u2014", "-")

        type_code = type_code_map.get(type_name)
        if type_code is None:
            # Unknown product type - create a new code
            slug = type_name.upper().replace(" ", "_")[:10]
            type_code = f"NDC-{slug}"
            type_code_map[type_name] = type_code

        # Build form code
        form_key = (type_code, form_name)
        if form_key not in form_codes and form_name:
            form_codes[form_key] = _make_form_code(type_code, form_name)

        fc = form_codes.get(form_key, type_code)
        products.append((ndc, title, type_code, fc))

    # Phase 2: build node list
    nodes: list[tuple[str, str, int, Optional[str]]] = []
    seen: set[str] = set()

    # Level 1: product types (only those that appear in data)
    seen_types = {tc for _, _, tc, _ in products}
    for type_code, type_title in NDC_PRODUCT_TYPES:
        if type_code in seen_types:
            nodes.append((type_code, type_title, 1, None))
            seen.add(type_code)

    # Level 2: dosage forms
    for (type_code, form_name), form_code in sorted(form_codes.items()):
        if form_code not in seen:
            display = form_name.title() if form_name else "Other"
            display = display.replace("\u2014", "-")
            nodes.append((form_code, display, 2, type_code))
            seen.add(form_code)

    # Level 3: individual products
    for ndc, title, type_code, form_code in products:
        if ndc not in seen:
            parent = form_code if form_code in seen else type_code
            nodes.append((ndc, title, 3, parent))
            seen.add(ndc)

    return nodes


async def ingest_ndc_fda(conn, path: Optional[str] = None) -> int:
    """Ingest full NDC from FDA product directory.

    Parses the tab-delimited file, builds hierarchy by product type
    and dosage form, and batch-inserts ~113K nodes.

    Returns total node count.
    """
    local = path or _find_data_file()
    if local is None:
        raise FileNotFoundError(
            "NDC data not found. Download from "
            "https://www.accessdata.fda.gov/cder/ndctext.zip "
            "and place the ZIP at data/ndc_product.zip"
        )

    nodes = parse_ndc_products(local)
    if len(nodes) < _EXPECTED_MIN:
        raise ValueError(
            f"Parsed only {len(nodes)} NDC nodes, expected >= {_EXPECTED_MIN}. "
            "Data file may be corrupted or truncated."
        )

    file_hash = sha256_of_file(local)

    sid, short, full, ver, region, authority = _SYSTEM_ROW
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority,
                source_url, source_date, data_provenance, license,
                source_file_hash, node_count)
           VALUES ($1,$2,$3,$4,$5,$6,$7,CURRENT_DATE,$8,$9,$10,0)
           ON CONFLICT (id) DO UPDATE SET
                name=$2, full_name=$3, version=$4, region=$5, authority=$6,
                source_url=$7, source_date=CURRENT_DATE, data_provenance=$8,
                license=$9, source_file_hash=$10, node_count=0""",
        sid, short, full, ver, region, authority,
        _SOURCE_URL, _DATA_PROVENANCE, _LICENSE, file_hash,
    )

    await conn.execute(
        "DELETE FROM classification_node WHERE system_id = $1", sid
    )

    records = [
        (sid, code, title, level, parent)
        for code, title, level, parent in nodes
    ]

    count = 0
    for i in range(0, len(records), CHUNK):
        chunk = records[i: i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, level, parent_code)
               VALUES ($1, $2, $3, $4, $5)""",
            chunk,
        )
        count += len(chunk)
        if count % 20_000 == 0:
            print(f"  ndc_fda: {count:,} nodes inserted...")

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )
    return count

"""Builder for UN M.49 (country + region) descriptions.

The UN Statistics Division's M.49 coding system assigns 3-digit
numeric codes to a four-level hierarchy:

- ``001`` World (level 0)
- 5 continent regions (level 1): Africa, Oceania, Americas, Asia, Europe
- ~24 sub-regions (level 2)
- 249 countries / territories (level 3)

Country-level descriptions reuse the same render produced by the
ISO 3166-2 backfill (same CSV, same fields). Region-level descriptions
are synthesized as a brief "X is a geographic region grouping N
countries" line that lists example members.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping, Optional

_EM_DASH = "\u2014"


def render_country(meta: Mapping[str, str]) -> str:
    """Return a short description for a country given its iso3166 row.

    Inlined from ``iso3166_2_descriptions.render_country`` so this
    module can ship independently of that branch. Keeps the same
    output format: ``"X is a country in <sub_region>, <region>.
    ISO alpha-3 code: XYZ."``.
    """
    name = (meta.get("name") or "").strip()
    alpha3 = (meta.get("alpha3") or "").strip()
    region = (meta.get("region") or "").strip()
    sub = (meta.get("sub_region") or "").strip()

    parts: list[str] = []
    if sub:
        parts.append(sub)
    if region and region != sub:
        parts.append(region)
    location = ", ".join(parts)

    if location:
        lead = f"{name} is a country in {location}."
    else:
        lead = f"{name}."
    if alpha3:
        lead = f"{lead} ISO alpha-3 code: {alpha3}."
    return lead.replace(_EM_DASH, "-")


def render_region(
    *,
    code: str,
    title: str,
    member_countries: List[str],
    parent_title: Optional[str] = None,
) -> str:
    """Return a short markdown description for an M.49 region or the World."""
    n = len(member_countries)
    if code == "001":
        lead = f"{title} is the UN M.49 aggregate covering all {n} recognized countries and territories."
    elif parent_title:
        lead = f"{title} is a UN M.49 sub-region of {parent_title}, grouping {n} countries."
    else:
        lead = f"{title} is a UN M.49 geographic region grouping {n} countries."

    if member_countries:
        preview = ", ".join(sorted(member_countries)[:5])
        if n > 5:
            preview += ", ..."
        lead += f" Members include: {preview}."

    return lead.replace(_EM_DASH, "-")


def build_m49_mapping(csv_path: Path) -> Dict[str, str]:
    """Return ``{m49_code: markdown_description}`` for every country in the
    CSV plus every region / sub-region that appears in its columns, plus
    ``001`` World.
    """
    out: Dict[str, str] = {}

    with Path(csv_path).open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    # Countries keyed by M.49 code
    for r in rows:
        m49 = (r.get("country-code") or "").strip()
        if not m49:
            continue
        meta = {
            "name": (r.get("name") or "").strip(),
            "alpha3": (r.get("alpha-3") or "").strip(),
            "region": (r.get("region") or "").strip(),
            "sub_region": (r.get("sub-region") or "").strip(),
        }
        out[m49] = render_country(meta)

    # Build region hierarchy: region-code -> title, sub-region-code -> title,
    # intermediate-region-code -> title, plus membership lists.
    region_title: Dict[str, str] = {}
    region_members: Dict[str, List[str]] = defaultdict(list)
    subregion_parent: Dict[str, str] = {}

    for r in rows:
        name = (r.get("name") or "").strip()
        rc = (r.get("region-code") or "").strip()
        sc = (r.get("sub-region-code") or "").strip()
        ic = (r.get("intermediate-region-code") or "").strip()
        r_title = (r.get("region") or "").strip()
        s_title = (r.get("sub-region") or "").strip()
        i_title = (r.get("intermediate-region") or "").strip()

        if rc and r_title:
            region_title[rc] = r_title
            region_members[rc].append(name)
        if sc and s_title:
            region_title[sc] = s_title
            region_members[sc].append(name)
            if rc:
                subregion_parent[sc] = region_title.get(rc, "")
        if ic and i_title:
            region_title[ic] = i_title
            region_members[ic].append(name)
            if sc:
                subregion_parent[ic] = region_title.get(sc, "")
            elif rc:
                subregion_parent[ic] = region_title.get(rc, "")

    for code, title in region_title.items():
        out[code] = render_region(
            code=code,
            title=title,
            member_countries=region_members.get(code, []),
            parent_title=subregion_parent.get(code),
        )

    # World
    all_country_names = [r.get("name", "").strip() for r in rows if r.get("name")]
    out["001"] = render_region(
        code="001",
        title="World",
        member_countries=all_country_names,
    )

    return out

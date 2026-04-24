"""Parser for ISO 3166-2 country + subdivision descriptions.

The structural ingester only stores code and title. For descriptions we
surface:

- Countries (level 0): UN M.49 region and sub-region from the on-disk
  ``data/iso3166_all.csv`` plus the alpha-3 ISO code.
- Subdivisions (level 1+): the subdivision type (Parish, State,
  Governorate, ...) and parent-country name, sourced from ``pycountry``.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Mapping

_EM_DASH = "\u2014"


def render_country(meta: Mapping[str, str]) -> str:
    """Return a markdown description for an ISO 3166-1 country.

    ``meta`` carries ``name``, ``alpha3``, ``region``, ``sub_region``.
    """
    name = meta.get("name", "").strip()
    alpha3 = meta.get("alpha3", "").strip()
    region = meta.get("region", "").strip()
    sub = meta.get("sub_region", "").strip()

    location_parts: list[str] = []
    if sub:
        location_parts.append(sub)
    if region and region != sub:
        location_parts.append(region)
    location = ", ".join(location_parts)

    if location:
        lead = f"{name} is a country in {location}."
    else:
        lead = f"{name}."

    if alpha3:
        lead = f"{lead} ISO alpha-3 code: {alpha3}."

    return lead.replace(_EM_DASH, "-")


def render_subdivision(
    *,
    code: str,
    sub_type: str,
    name: str,
    country_name: str,
) -> str:
    """Return a markdown description for one ISO 3166-2 subdivision."""
    sub_type = (sub_type or "").strip() or "Subdivision"
    country_name = (country_name or "").strip()
    name = (name or "").strip()

    article = "an" if sub_type[:1].lower() in "aeiou" else "a"
    if country_name:
        body = f"{name} is {article} {sub_type} of {country_name} (ISO 3166-2 code {code})."
    else:
        body = f"{name} is {article} {sub_type} (ISO 3166-2 code {code})."
    return body.replace(_EM_DASH, "-")


def _load_countries(path: Path) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            alpha2 = (row.get("alpha-2") or "").strip()
            if not alpha2:
                continue
            out[alpha2] = {
                "name": (row.get("name") or "").strip(),
                "alpha3": (row.get("alpha-3") or "").strip(),
                "region": (row.get("region") or "").strip(),
                "sub_region": (row.get("sub-region") or "").strip(),
            }
    return out


def parse_iso3166_2_descriptions(path: Path) -> Dict[str, str]:
    """Return ``{code: markdown_description}`` for every country + subdivision.

    Countries come from the on-disk CSV; subdivisions are enumerated via
    the ``pycountry`` library (already a project dependency). A missing
    pycountry match is skipped.
    """
    import pycountry

    countries = _load_countries(path)

    out: Dict[str, str] = {}
    for alpha2, meta in countries.items():
        out[alpha2] = render_country(meta)

    for sub in pycountry.subdivisions:
        country_alpha2 = sub.country_code
        country_meta = countries.get(country_alpha2) or {}
        country_name = country_meta.get("name", "")
        out[sub.code] = render_subdivision(
            code=sub.code,
            sub_type=sub.type,
            name=sub.name,
            country_name=country_name,
        )

    return out

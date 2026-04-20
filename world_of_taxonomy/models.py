"""Data models for WorldOfTaxonomy.

Plain dataclasses that map to database rows. No ORM dependency.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClassificationSystem:
    """A classification system (e.g., NAICS 2022, ISIC Rev 4)."""

    id: str
    name: str
    full_name: Optional[str] = None
    region: Optional[str] = None
    version: Optional[str] = None
    authority: Optional[str] = None
    url: Optional[str] = None
    tint_color: Optional[str] = None
    node_count: int = 0
    source_url: Optional[str] = None
    source_date: Optional[str] = None
    data_provenance: Optional[str] = None
    license: Optional[str] = None
    source_file_hash: Optional[str] = None
    # Derived from id: "domain" if id starts with "domain_", else "standard".
    # Drives the two-section UI pattern across web, API, MCP, and skills.
    category: str = "standard"


@dataclass
class ClassificationNode:
    """A single node in a classification hierarchy."""

    system_id: str
    code: str
    title: str
    description: Optional[str] = None
    level: int = 0
    parent_code: Optional[str] = None
    sector_code: Optional[str] = None
    is_leaf: bool = False
    seq_order: int = 0
    id: Optional[int] = None

    # Transient fields populated by queries (not stored in DB)
    children: list["ClassificationNode"] = field(default_factory=list)
    equivalences: list["Equivalence"] = field(default_factory=list)


@dataclass
class Equivalence:
    """A cross-system equivalence edge."""

    source_system: str
    source_code: str
    target_system: str
    target_code: str
    match_type: str = "partial"  # exact, partial, broad, narrow
    notes: Optional[str] = None

    # Transient fields populated by joins
    source_title: Optional[str] = None
    target_title: Optional[str] = None


@dataclass
class DomainTaxonomy:
    """A domain-specific taxonomy (e.g., ICD-10, ATC, HS codes).

    Placeholder for future implementation.
    """

    id: str
    name: str
    full_name: Optional[str] = None
    authority: Optional[str] = None
    url: Optional[str] = None
    code_count: int = 0


# Sector color mapping from DESIGN.md
SECTOR_COLORS = {
    "11": "#4ADE80",      # Agriculture
    "21": "#F59E0B",      # Mining
    "22": "#06B6D4",      # Utilities
    "23": "#EF4444",      # Construction
    "31-33": "#8B5CF6",   # Manufacturing
    "42": "#EC4899",      # Wholesale
    "44-45": "#F97316",   # Retail
    "48-49": "#14B8A6",   # Transportation
    "51": "#3B82F6",      # Information
    "52": "#6366F1",      # Finance
    "53": "#A78BFA",      # Real Estate
    "54": "#10B981",      # Professional
    "55": "#64748B",      # Management
    "56": "#78716C",      # Admin & Support
    "61": "#2563EB",      # Education
    "62": "#0D9488",      # Healthcare
    "71": "#E11D48",      # Arts
    "72": "#D97706",      # Accommodation
    "81": "#9CA3AF",      # Other Services
    "92": "#1E40AF",      # Public Admin
}

# NAICS range codes: maps 2-digit prefixes to their actual sector code
NAICS_SECTOR_MAP = {
    "31": "31-33", "32": "31-33", "33": "31-33",
    "44": "44-45", "45": "44-45",
    "48": "48-49", "49": "48-49",
}

# Classification system tints from DESIGN.md
SYSTEM_TINTS = {
    "isic_rev4": None,          # Neutral - universal baseline
    "naics_2022": "#F59E0B",    # Warm amber
    "nace_rev2": "#3B82F6",     # Cool blue
    "anzsic": "#14B8A6",        # Teal
    "jsic": "#E11D48",          # Rose
    "sic": "#9CA3AF",           # Muted gray
    "nic": "#F97316",           # Warm orange
    "gbt": "#EF4444",           # Subtle red
}

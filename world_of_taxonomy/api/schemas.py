"""Pydantic response models for the REST API."""

from typing import Any, List, Optional
from pydantic import BaseModel, EmailStr, Field, model_validator

from world_of_taxonomy.category import compute_edge_kind, get_category


class SystemResponse(BaseModel):
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
    category: str = Field(
        "standard",
        description="'domain' for curated WoT Domain taxonomies (id starts 'domain_'), 'standard' otherwise.",
    )

    @model_validator(mode="before")
    @classmethod
    def _derive_category(cls, values: Any) -> Any:
        if isinstance(values, dict) and values.get("id"):
            values = {**values, "category": get_category(values["id"])}
        return values


class NodeResponse(BaseModel):
    id: int
    system_id: str
    code: str
    title: str
    description: Optional[str] = None
    level: int = 0
    parent_code: Optional[str] = None
    sector_code: Optional[str] = None
    is_leaf: bool = False
    seq_order: int = 0
    # Derived from system_id: drives two-section rendering on mixed lists.
    category: str = Field(
        "standard",
        description="'domain' if system_id starts 'domain_', else 'standard'.",
    )
    # Provenance fields (from parent classification_system)
    data_provenance: Optional[str] = None
    license: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[str] = None
    source_file_hash: Optional[str] = None
    # Per-code authority deep link, interpolated from the system's
    # node_url_template. None when the system has no per-code page.
    source_url_for_code: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _derive_category(cls, values: Any) -> Any:
        if isinstance(values, dict) and values.get("system_id"):
            values = {**values, "category": get_category(values["system_id"])}
        return values


class SystemDetailResponse(SystemResponse):
    roots: List[NodeResponse] = []


class EquivalenceResponse(BaseModel):
    source_system: str
    source_code: str
    target_system: str
    target_code: str
    match_type: str
    notes: Optional[str] = None
    source_title: Optional[str] = None
    target_title: Optional[str] = None
    source_category: str = Field(
        "standard",
        description="Category of source_system: 'domain' or 'standard'.",
    )
    target_category: str = Field(
        "standard",
        description="Category of target_system: 'domain' or 'standard'.",
    )
    edge_kind: str = Field(
        "standard_standard",
        description="One of: standard_standard, standard_domain, domain_standard, domain_domain.",
    )

    @model_validator(mode="before")
    @classmethod
    def _derive_edge_kind(cls, values: Any) -> Any:
        if isinstance(values, dict):
            src = values.get("source_system")
            tgt = values.get("target_system")
            if src and tgt:
                values = {
                    **values,
                    "source_category": get_category(src),
                    "target_category": get_category(tgt),
                    "edge_kind": compute_edge_kind(src, tgt),
                }
        return values


class CrosswalkStatResponse(BaseModel):
    source_system: str
    target_system: str
    edge_count: int
    exact_count: int
    partial_count: int


class EdgeKindStatResponse(BaseModel):
    edge_kind: str
    edge_count: int
    exact_count: int = 0
    partial_count: int = 0
    broad_count: int = 0


class CrosswalkGraphNode(BaseModel):
    id: str
    system: str
    code: str
    title: str


class CrosswalkGraphEdge(BaseModel):
    source: str
    target: str
    match_type: str


class CrosswalkGraphResponse(BaseModel):
    source_system: str
    target_system: str
    nodes: List[CrosswalkGraphNode]
    edges: List[CrosswalkGraphEdge]
    total_edges: int
    truncated: bool


class CrosswalkSection(BaseModel):
    source_section: str
    source_title: str
    target_section: str
    target_title: str
    edge_count: int
    exact_count: int


class CrosswalkSectionsResponse(BaseModel):
    source_system: str
    target_system: str
    sections: List[CrosswalkSection]
    total_edges: int


# Auth schemas (RegisterRequest, LoginRequest, UserResponse,
# TokenResponse, CreateApiKeyRequest, ApiKeyResponse,
# ApiKeyCreatedResponse, UsageStatsResponse) were removed in 2026-04-30
# along with the /api/v1/auth/* router and oauth.py. Sign-in is now
# exclusively the magic-link flow in developers.py, which uses its own
# inline Pydantic models (SignupRequest, CreateKeyRequest,
# KeyMetadata, KeyCreatedResponse).


class SubtreeSummaryResponse(BaseModel):
    system_id: str
    code: str
    title: str
    total_nodes: int
    leaf_count: int
    max_depth: int


class CompareSectorsResponse(BaseModel):
    system_a: List[NodeResponse]
    system_b: List[NodeResponse]


class SystemGranularityResponse(BaseModel):
    system_id: str
    total_nodes: int
    leaf_nodes: int


class NodeWithContextResponse(NodeResponse):
    ancestors: List[NodeResponse] = []
    children: List[NodeResponse] = []


# -- AI Taxonomy Generation schemas ------------------------------------------


class GenerateTaxonomyRequest(BaseModel):
    count: int = 5  # how many sub-categories to generate (1-10)


class GeneratedNode(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None


class GenerateTaxonomyResponse(BaseModel):
    parent_system_id: str
    parent_code: str
    nodes: List[GeneratedNode]


class AcceptTaxonomyRequest(BaseModel):
    nodes: List[GeneratedNode]  # the subset the user chose to keep


# -- Audit schemas -----------------------------------------------------------


class ProvenanceTierSummary(BaseModel):
    data_provenance: Optional[str]
    system_count: int
    node_count: int


class AuditProvenanceResponse(BaseModel):
    total_systems: int
    total_nodes: int
    provenance_tiers: List[ProvenanceTierSummary]
    official_missing_hash: List[SystemResponse]
    structural_derivation_count: int
    structural_derivation_nodes: int
    skeleton_systems: List[SystemResponse]


# -- Wiki schemas ------------------------------------------------------------


class WikiPageSummary(BaseModel):
    slug: str
    title: str
    description: str


class WikiPageDetail(BaseModel):
    slug: str
    title: str
    description: str
    content_markdown: str

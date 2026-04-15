"""Pydantic response models for the REST API."""

from typing import List, Optional
from pydantic import BaseModel


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


class CrosswalkStatResponse(BaseModel):
    source_system: str
    target_system: str
    edge_count: int
    exact_count: int
    partial_count: int


# ── Auth schemas ─────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    tier: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreateApiKeyRequest(BaseModel):
    name: str = "Default"


class ApiKeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    is_active: bool
    last_used_at: Optional[str]
    created_at: str
    expires_at: Optional[str]


class ApiKeyCreatedResponse(BaseModel):
    key: str  # Full key, shown once
    api_key: ApiKeyResponse


class UsageStatsResponse(BaseModel):
    total_requests: int
    requests_today: int
    requests_this_hour: int


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


class GenerateTaxonomyResponse(BaseModel):
    parent_system_id: str
    parent_code: str
    nodes: List[GeneratedNode]


class AcceptTaxonomyRequest(BaseModel):
    nodes: List[GeneratedNode]  # the subset the user chose to keep

export type TaxonomyCategory = 'domain' | 'standard'

export interface ClassificationSystem {
  id: string
  name: string
  full_name: string | null
  region: string | null
  version: string | null
  authority: string | null
  url: string | null
  tint_color: string | null
  node_count: number
  source_url: string | null
  source_date: string | null
  data_provenance: 'official_download' | 'structural_derivation' | 'manual_transcription' | 'expert_curated' | null
  license: string | null
  source_file_hash: string | null
  category: TaxonomyCategory
}

export interface SystemDetail extends ClassificationSystem {
  roots: ClassificationNode[]
}

export interface ClassificationNode {
  id: number
  system_id: string
  code: string
  title: string
  description: string | null
  level: number
  parent_code: string | null
  sector_code: string | null
  is_leaf: boolean
  seq_order: number
  category: TaxonomyCategory
  // Provenance fields (from parent classification_system)
  data_provenance: 'official_download' | 'structural_derivation' | 'manual_transcription' | 'expert_curated' | null
  license: string | null
  source_url: string | null
  source_date: string | null
  source_file_hash: string | null
}

export interface ClassificationNodeWithContext extends ClassificationNode {
  ancestors?: ClassificationNode[]
}

export type EdgeKind =
  | 'standard_standard'
  | 'standard_domain'
  | 'domain_standard'
  | 'domain_domain'

export interface Equivalence {
  source_system: string
  source_code: string
  target_system: string
  target_code: string
  match_type: string
  notes: string | null
  source_title: string | null
  target_title: string | null
  source_category: TaxonomyCategory
  target_category: TaxonomyCategory
  edge_kind: EdgeKind
}

export interface CrosswalkStat {
  source_system: string
  target_system: string
  edge_count: number
  exact_count: number
  partial_count: number
}

export interface CrosswalkGraphNode {
  id: string
  system: string
  code: string
  title: string
}

export interface CrosswalkGraphEdge {
  source: string
  target: string
  match_type: string
}

export interface CrosswalkGraphResponse {
  source_system: string
  target_system: string
  nodes: CrosswalkGraphNode[]
  edges: CrosswalkGraphEdge[]
  total_edges: number
  truncated: boolean
}

export interface CrosswalkSection {
  source_section: string
  source_title: string
  target_section: string
  target_title: string
  edge_count: number
  exact_count: number
}

export interface CrosswalkSectionsResponse {
  source_system: string
  target_system: string
  sections: CrosswalkSection[]
  total_edges: number
}

export interface User {
  id: string
  email: string
  display_name: string | null
  tier: 'free' | 'pro' | 'enterprise'
  created_at: string
}

export interface ApiKey {
  id: string
  key_prefix: string
  name: string
  is_active: boolean
  last_used_at: string | null
  created_at: string
  expires_at: string | null
}

export interface AuthTokens {
  access_token: string
  token_type: string
}

export interface GeneratedNode {
  code: string
  title: string
  description: string | null
  reason?: string | null
}

export interface GenerateTaxonomyResponse {
  parent_system_id: string
  parent_code: string
  nodes: GeneratedNode[]
}

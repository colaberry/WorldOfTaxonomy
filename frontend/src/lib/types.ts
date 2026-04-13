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
}

export interface Equivalence {
  source_system: string
  source_code: string
  target_system: string
  target_code: string
  match_type: string
  notes: string | null
  source_title: string | null
  target_title: string | null
}

export interface CrosswalkStat {
  source_system: string
  target_system: string
  edge_count: number
  exact_count: number
  partial_count: number
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

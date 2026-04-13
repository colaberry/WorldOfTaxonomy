import type {
  ClassificationSystem,
  SystemDetail,
  ClassificationNode,
  Equivalence,
  CrosswalkStat,
  User,
  ApiKey,
  AuthTokens,
} from './types'

const API_BASE = ''

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) {
    throw new ApiError(res.status, `API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

// ── Systems ──

export async function getSystems(): Promise<ClassificationSystem[]> {
  return fetchJson('/api/v1/systems')
}

export async function getSystem(systemId: string): Promise<SystemDetail> {
  return fetchJson(`/api/v1/systems/${systemId}`)
}

// ── Nodes ──

export async function getNode(
  systemId: string,
  code: string
): Promise<ClassificationNode> {
  return fetchJson(`/api/v1/systems/${systemId}/nodes/${code}`)
}

export async function getChildren(
  systemId: string,
  code: string
): Promise<ClassificationNode[]> {
  return fetchJson(`/api/v1/systems/${systemId}/nodes/${code}/children`)
}

export async function getAncestors(
  systemId: string,
  code: string
): Promise<ClassificationNode[]> {
  return fetchJson(`/api/v1/systems/${systemId}/nodes/${code}/ancestors`)
}

export async function getEquivalences(
  systemId: string,
  code: string
): Promise<Equivalence[]> {
  return fetchJson(`/api/v1/systems/${systemId}/nodes/${code}/equivalences`)
}

// ── Search ──

export async function search(
  query: string,
  systemId?: string,
  limit?: number
): Promise<ClassificationNode[]> {
  const params = new URLSearchParams({ q: query })
  if (systemId) params.set('system', systemId)
  if (limit) params.set('limit', String(limit))
  return fetchJson(`/api/v1/search?${params}`)
}

// ── Crosswalk stats ──

export async function getStats(): Promise<CrosswalkStat[]> {
  return fetchJson('/api/v1/equivalences/stats')
}

// ── Countries ──

export interface CountryStat {
  country_code: string
  system_count: number
  has_official: boolean
  sector_strength_count: number
}

export async function getCountriesStats(): Promise<CountryStat[]> {
  return fetchJson('/api/v1/countries/stats')
}

export interface CountrySystem {
  id: string
  name: string
  full_name: string | null
  region: string | null
  version: string | null
  authority: string | null
  url: string | null
  tint_color: string | null
  node_count: number
  relevance: 'official' | 'regional' | 'recommended' | 'historical'
  csl_notes: string | null
}

export interface SectorStrength {
  naics_sector: string
  sector_name: string
  match_type: string
  notes: string | null
}

export interface CountryProfile {
  country: {
    code: string
    title: string | null
    parent_region: string | null
  }
  classification_systems: CountrySystem[]
  sector_strengths: SectorStrength[]
}

export async function getCountryProfile(code: string): Promise<CountryProfile> {
  return fetchJson(`/api/v1/countries/${code.toUpperCase()}`)
}

// ── Auth ──

export async function register(
  email: string,
  password: string,
  displayName?: string
): Promise<User> {
  return fetchJson('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  })
}

export async function login(
  email: string,
  password: string
): Promise<AuthTokens> {
  return fetchJson('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function getMe(token: string): Promise<User> {
  return fetchJson('/api/v1/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  })
}

export async function createApiKey(
  token: string,
  name?: string
): Promise<{ key: string; api_key: ApiKey }> {
  return fetchJson('/api/v1/auth/keys', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name: name || 'Default' }),
  })
}

export async function listApiKeys(token: string): Promise<ApiKey[]> {
  return fetchJson('/api/v1/auth/keys', {
    headers: { Authorization: `Bearer ${token}` },
  })
}

export async function revokeApiKey(
  token: string,
  keyId: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/auth/keys/${keyId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    throw new ApiError(res.status, `Failed to revoke key: ${res.statusText}`)
  }
}

export { ApiError }

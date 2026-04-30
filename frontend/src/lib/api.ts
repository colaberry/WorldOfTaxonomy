import type {
  ClassificationSystem,
  SystemDetail,
  ClassificationNode,
  ClassificationNodeWithContext,
  Equivalence,
  CrosswalkStat,
  CrosswalkGraphResponse,
  CrosswalkSectionsResponse,
  GeneratedNode,
  GenerateTaxonomyResponse,
} from './types'
import { getCsrfToken } from './auth'

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

// ── AI Taxonomy Generation ──

// Note: /nodes/.../generate is JWT-gated server-side via get_current_user.
// With OAuth + the legacy /auth router removed in 2026-04-30, no JWT can
// be minted any more, so these routes 401 in practice. The client-side
// helpers stay so the AI-taxonomy panel in NodeTree compiles, but they
// will need to be re-pointed at a require_scope-gated endpoint when the
// AI-extension flow is wired into the magic-link cookie session.
export async function generateTaxonomy(
  systemId: string,
  code: string,
  count = 5
): Promise<GenerateTaxonomyResponse> {
  const res = await fetch(
    `/api/v1/systems/${systemId}/nodes/${encodeURIComponent(code)}/generate`,
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken(),
      },
      body: JSON.stringify({ count }),
    }
  )
  if (!res.ok) {
    throw new ApiError(res.status, `Generate failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function acceptGeneratedTaxonomy(
  systemId: string,
  code: string,
  nodes: GeneratedNode[]
): Promise<ClassificationNode[]> {
  const res = await fetch(
    `/api/v1/systems/${systemId}/nodes/${encodeURIComponent(code)}/generate/accept`,
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': getCsrfToken(),
      },
      body: JSON.stringify({ nodes }),
    }
  )
  if (!res.ok) {
    throw new ApiError(res.status, `Accept failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

// ── Search ──

export async function search(
  query: string,
  systemId?: string | string[],
  limit?: number,
  context = false
): Promise<ClassificationNodeWithContext[]> {
  const params = new URLSearchParams({ q: query })
  if (Array.isArray(systemId)) {
    for (const id of systemId) params.append('system_id', id)
  } else if (systemId) {
    params.set('system', systemId)
  }
  if (limit) params.set('limit', String(limit))
  if (context) params.set('context', 'true')
  return fetchJson(`/api/v1/search?${params}`)
}

// ── Crosswalk stats ──

export async function getStats(): Promise<CrosswalkStat[]> {
  return fetchJson('/api/v1/equivalences/stats')
}

// ── Crosswalk graph ──

export async function getCrosswalkGraph(
  source: string,
  target: string,
  limit = 500,
  section?: string,
): Promise<CrosswalkGraphResponse> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (section) params.set('section', section)
  return fetchJson(
    `/api/v1/systems/${source}/crosswalk/${target}/graph?${params}`
  )
}

export async function getCrosswalkSections(
  source: string,
  target: string,
): Promise<CrosswalkSectionsResponse> {
  return fetchJson(
    `/api/v1/systems/${source}/crosswalk/${target}/sections`
  )
}

// ── Countries ──

export interface CountryStat {
  country_code: string
  system_count: number
  country_specific_count: number
  has_official: boolean
  sector_strength_count: number
  primary_system_id: string | null
}

export async function getCountriesStats(): Promise<CountryStat[]> {
  return fetchJson('/api/v1/countries/stats')
}

export interface CountryListEntry {
  code: string
  title: string
  system_count: number
  has_official: boolean
}

export async function getCountriesList(): Promise<CountryListEntry[]> {
  return fetchJson('/api/v1/countries')
}

export async function getSystemsForCountry(
  code: string
): Promise<CountrySystem[]> {
  return fetchJson(`/api/v1/systems?country=${encodeURIComponent(code.toUpperCase())}`)
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

// Auth helpers were removed in 2026-04-30. The /api/v1/auth/register,
// /login, /me, and /keys CRUD endpoints they called no longer exist.
// Sign-in lives on /login (magic-link form), key management lives in
// the developer dashboard at /developers/keys (cookie-gated; uses the
// fetch calls in app/developers/keys/page.tsx directly).

// ── Classify (demo, email-gated) ──

export interface ClassifyDemoMatch {
  code: string
  title: string
  score: number
  level: number
  crosswalk_count?: number
}

export interface ClassifyDemoSystemMatch {
  system_id: string
  system_name: string
  category: 'domain' | 'standard'
  results: ClassifyDemoMatch[]
}

export interface ClassifyDemoAtom {
  phrase: string
  domain_matches: ClassifyDemoSystemMatch[]
  standard_matches: ClassifyDemoSystemMatch[]
}

export interface ClassifyDemoCta {
  title: string
  message: string
  url: string
  cta_label: string
}

export interface ClassifyScopeInfo {
  countries: string[]
  country_specific_systems: string[]
  global_standard_systems: string[]
  candidate_systems: string[]
}

export interface ClassifyDemoResponse {
  query: string
  domain_matches: ClassifyDemoSystemMatch[]
  standard_matches: ClassifyDemoSystemMatch[]
  disclaimer: string
  report_issue_url: string
  demo: boolean
  upgrade_cta: string
  compound?: boolean
  atoms?: ClassifyDemoAtom[] | null
  hero?: ClassifyDemoAtom | null
  cta?: ClassifyDemoCta | null
  llm_used?: boolean
  llm_keywords?: string[]
  scope?: ClassifyScopeInfo | null
}

export async function classifyDemo(
  email: string,
  text: string,
  countries?: string[]
): Promise<ClassifyDemoResponse> {
  const body: Record<string, unknown> = { email, text }
  if (countries && countries.length > 0) body.countries = countries
  return fetchJson('/api/v1/classify/demo', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

// ── GitHub public repo stats ──

export async function getGithubStars(): Promise<number> {
  const res = await fetch('https://api.github.com/repos/colaberry/WorldOfTaxonomy', {
    headers: { Accept: 'application/vnd.github.v3+json' },
    next: { revalidate: 3600 }, // Next.js cache hint - 1 hour
  })
  if (!res.ok) return 0
  const data = await res.json()
  return data.stargazers_count ?? 0
}

export { ApiError }

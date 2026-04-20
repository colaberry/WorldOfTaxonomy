/**
 * Server-side API client for Next.js Server Components.
 *
 * Fetches data from the backend during server-side rendering so that
 * crawlers see fully-rendered HTML. Uses time-based revalidation
 * (ISR) since tag-based caching requires CacheLife profiles in
 * Next.js 15. On-demand invalidation uses revalidatePath via the
 * /api/revalidate webhook endpoint.
 */

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000'

// Default revalidate: 1 hour. Human users always get fresh data
// via client-side React Query refetch with staleTime: 0.
const DEFAULT_REVALIDATE = 3600

export async function serverFetch<T>(
  path: string,
  options?: { revalidate?: number | false },
): Promise<T> {
  const { revalidate = DEFAULT_REVALIDATE } = options ?? {}

  const fetchOptions: RequestInit & { next?: Record<string, unknown> } = {
    headers: { 'Content-Type': 'application/json' },
    next: {},
  }

  if (revalidate !== undefined && revalidate !== false) {
    fetchOptions.next!.revalidate = revalidate
  }

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 5000)
  try {
    const res = await fetch(`${BACKEND_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
    })
    if (!res.ok) {
      throw new Error(`Server API error ${res.status}: ${path}`)
    }
    return res.json()
  } finally {
    clearTimeout(timeout)
  }
}

// ---- Typed helpers ----

import type {
  ClassificationSystem,
  SystemDetail,
  ClassificationNode,
  Equivalence,
  CrosswalkStat,
} from './types'
import type { CountryProfile } from './api'

export async function serverGetSystems(): Promise<ClassificationSystem[]> {
  return serverFetch('/api/v1/systems')
}

export async function serverGetSystem(id: string): Promise<SystemDetail> {
  return serverFetch(`/api/v1/systems/${id}`)
}

export async function serverGetNode(
  systemId: string,
  code: string,
): Promise<ClassificationNode> {
  return serverFetch(`/api/v1/systems/${systemId}/nodes/${code}`)
}

export async function serverGetChildren(
  systemId: string,
  code: string,
): Promise<ClassificationNode[]> {
  return serverFetch(`/api/v1/systems/${systemId}/nodes/${code}/children`)
}

// BFS walk of the classification tree, returning all nodes at level <=
// maxLevel. Uses the /children endpoint per node. The underlying fetches
// respect the ISR revalidate window, so repeat calls within the cache
// window are cheap. Used at build time for sitemap generation and for
// expanding generateStaticParams beyond the sector (level 1) tier.
export async function serverListNodesUpToLevel(
  systemId: string,
  maxLevel: number,
): Promise<ClassificationNode[]> {
  if (maxLevel < 1) return []
  const detail = await serverGetSystem(systemId).catch(() => null)
  if (!detail) return []
  const result: ClassificationNode[] = [...detail.roots]
  let frontier: ClassificationNode[] = detail.roots
  for (let level = 1; level < maxLevel; level++) {
    const allChildren = await Promise.all(
      frontier.map((n) =>
        serverGetChildren(systemId, n.code).catch(
          () => [] as ClassificationNode[],
        ),
      ),
    )
    const next: ClassificationNode[] = []
    for (const children of allChildren) {
      for (const c of children) {
        result.push(c)
        next.push(c)
      }
    }
    if (next.length === 0) break
    frontier = next
  }
  return result
}

export async function serverGetAncestors(
  systemId: string,
  code: string,
): Promise<ClassificationNode[]> {
  return serverFetch(`/api/v1/systems/${systemId}/nodes/${code}/ancestors`)
}

export async function serverGetSiblings(
  systemId: string,
  code: string,
): Promise<ClassificationNode[]> {
  return serverFetch(`/api/v1/systems/${systemId}/nodes/${code}/siblings`)
}

export async function serverGetEquivalences(
  systemId: string,
  code: string,
): Promise<Equivalence[]> {
  return serverFetch(`/api/v1/systems/${systemId}/nodes/${code}/equivalences`)
}

export async function serverGetStats(): Promise<CrosswalkStat[]> {
  return serverFetch('/api/v1/equivalences/stats')
}

export async function serverGetCountryProfile(
  code: string,
): Promise<CountryProfile> {
  return serverFetch(`/api/v1/countries/${code.toUpperCase()}`)
}

export interface CountryListEntry {
  code: string
  title: string
  system_count: number
  has_official: boolean
}

export async function serverListCountries(): Promise<CountryListEntry[]> {
  return serverFetch('/api/v1/countries')
}

export async function serverSearch(
  query: string,
  systemId?: string,
  limit = 5,
): Promise<ClassificationNode[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) })
  if (systemId) params.set('system', systemId)
  return serverFetch(`/api/v1/search?${params}`)
}

// Natural-language queries ("telemedicine platform", "bakery that also sells
// coffee") often miss the tsvector AND-join used by the search endpoint. Fall
// back to searching the longest non-stopword tokens individually and merging
// by code, so curated business-type pages still resolve sensible matches even
// when no code title contains the full phrase verbatim.
const STOPWORDS = new Set<string>([
  'the', 'and', 'for', 'with', 'that', 'also', 'sells', 'company', 'service',
  'services', 'online', 'based', 'independent', 'private', 'retail', 'small',
  'commercial', 'residential', 'from', 'into', 'over', 'under', 'using',
  'provider', 'platform', 'startup', 'shop', 'store', 'agency', 'firm',
  'business', 'general', 'custom', 'local', 'mobile', 'full', 'this', 'that',
])

function extractSignificantTerms(query: string): string[] {
  return query
    .toLowerCase()
    .split(/\s+/)
    .map((w) => w.replace(/[^a-z0-9-]/g, ''))
    .filter((w) => w.length >= 4 && !STOPWORDS.has(w))
    .sort((a, b) => b.length - a.length)
}

export async function serverSearchFallback(
  query: string,
  systemId: string,
  editorialKeywords?: string[],
  limit = 3,
): Promise<ClassificationNode[]> {
  const primary = await serverSearch(query, systemId, limit).catch(
    () => [] as ClassificationNode[],
  )
  if (primary.length > 0) return primary

  const seen = new Map<string, ClassificationNode>()
  const tryTerm = async (term: string) => {
    if (seen.size >= limit) return
    const extra = await serverSearch(term, systemId, limit).catch(
      () => [] as ClassificationNode[],
    )
    for (const node of extra) {
      if (!seen.has(node.code)) seen.set(node.code, node)
      if (seen.size >= limit) break
    }
  }

  // Editorial keywords (curator-specified) first - they encode the intended
  // mapping for modern business types whose names don't appear in official
  // classification titles (e.g. "telemedicine" -> "physicians").
  if (editorialKeywords && editorialKeywords.length > 0) {
    for (const term of editorialKeywords) {
      if (seen.size >= limit) break
      await tryTerm(term)
    }
    if (seen.size > 0) return Array.from(seen.values()).slice(0, limit)
  }

  // Fall back to automatic extraction of significant terms from the query.
  const terms = extractSignificantTerms(query)
  for (const term of terms.slice(0, 3)) {
    if (seen.size >= limit) break
    await tryTerm(term)
  }
  return Array.from(seen.values()).slice(0, limit)
}

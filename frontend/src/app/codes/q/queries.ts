import queriesJson from './queries.json'

export interface CuratedQuery {
  slug: string
  query: string
  hint: string
  /**
   * Optional editorial fallback search terms. Used when the natural-language
   * query itself misses the tsvector search (typical for modern business
   * types like "telemedicine" or "cybersecurity" whose words don't appear
   * verbatim in NAICS/ISIC titles). Each term is tried in order; results
   * are merged by code.
   */
  keywords?: string[]
}

export const QUERIES: CuratedQuery[] = queriesJson as CuratedQuery[]

const SLUG_MAP = new Map<string, CuratedQuery>(
  QUERIES.map((q) => [q.slug, q]),
)

export function getQuery(slug: string): CuratedQuery | undefined {
  return SLUG_MAP.get(slug)
}

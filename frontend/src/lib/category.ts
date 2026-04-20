import type { TaxonomyCategory } from './types'

/**
 * Client-side mirror of world_of_taxonomy/category.py.
 * Keep in sync: system IDs starting with "domain_" are domain taxonomies;
 * everything else is an official standard.
 */
export function getSystemCategory(systemId: string): TaxonomyCategory {
  return systemId.startsWith('domain_') ? 'domain' : 'standard'
}

export function isDomainSystem(systemId: string): boolean {
  return systemId.startsWith('domain_')
}

export function categoryLabel(category: TaxonomyCategory): string {
  return category === 'domain' ? 'Domain taxonomy' : 'Official standard'
}

export type EdgeKind =
  | 'standard_standard'
  | 'standard_domain'
  | 'domain_standard'
  | 'domain_domain'

export function computeEdgeKind(sourceSystem: string, targetSystem: string): EdgeKind {
  const src = getSystemCategory(sourceSystem)
  const tgt = getSystemCategory(targetSystem)
  return `${src}_${tgt}` as EdgeKind
}

import type { MetadataRoute } from 'next'
import { getWikiSlugs } from '@/lib/wiki'
import { getBlogSlugs } from '@/lib/blog'
import {
  serverGetStats,
  serverListCountries,
  serverListNodesUpToLevel,
} from '@/lib/server-api'
import { MAJOR_SYSTEMS, MAJOR_SYSTEM_SET } from './codes/constants'
import { QUERIES } from './codes/q/queries'

const SITE_URL = 'https://worldoftaxonomy.com'
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000'

// Depth cap for /codes/[system]/[code] pages emitted into the sitemap.
// Level 1 = sector (e.g. NAICS 2-digit), 2 = subsector (3-digit),
// 3 = industry group (4-digit). Anything deeper is still reachable via
// SSR + ISR and via internal links on the industry group pages, but is
// not listed in the sitemap to keep it under Google's per-file limits.
const CODES_SITEMAP_MAX_LEVEL = 3

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const guidePages: MetadataRoute.Sitemap = getWikiSlugs().map((slug) => ({
    url: `${SITE_URL}/guide/${slug}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.8,
  }))

  const blogPages: MetadataRoute.Sitemap = getBlogSlugs().map((slug) => ({
    url: `${SITE_URL}/blog/${slug}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }))

  const staticPages: MetadataRoute.Sitemap = [
    { url: SITE_URL, lastModified: new Date(), changeFrequency: 'weekly', priority: 1.0 },
    { url: `${SITE_URL}/classify`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.95 },
    { url: `${SITE_URL}/codes`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.95 },
    { url: `${SITE_URL}/crosswalks`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.95 },
    { url: `${SITE_URL}/explore`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    { url: `${SITE_URL}/guide`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    { url: `${SITE_URL}/pricing`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.9 },
    { url: `${SITE_URL}/blog`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.8 },
    { url: `${SITE_URL}/developers`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },
    { url: `${SITE_URL}/api`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },
    { url: `${SITE_URL}/mcp`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },
    { url: `${SITE_URL}/about`, lastModified: new Date(), changeFrequency: 'monthly', priority: 0.6 },
    ...guidePages,
    ...blogPages,
  ]

  const codesSystemHubs: MetadataRoute.Sitemap = MAJOR_SYSTEMS.map((id) => ({
    url: `${SITE_URL}/codes/${id}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.85,
  }))

  const queryPages: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/codes/q`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.9 },
    ...QUERIES.map((q) => ({
      url: `${SITE_URL}/codes/q/${q.slug}`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.8,
    })),
  ]

  try {
    const [systemsRes, deepNodesPerSystem, stats, countries] = await Promise.all([
      fetch(`${BACKEND_URL}/api/v1/systems`, { next: { revalidate: 3600 } }),
      Promise.all(
        MAJOR_SYSTEMS.map(async (id) => {
          const nodes = await serverListNodesUpToLevel(
            id,
            CODES_SITEMAP_MAX_LEVEL,
          ).catch(() => [])
          return { id, nodes }
        }),
      ),
      serverGetStats().catch(() => []),
      serverListCountries().catch(() => []),
    ])
    if (!systemsRes.ok) return [...staticPages, ...codesSystemHubs, ...queryPages]

    const systems: Array<{ id: string }> = await systemsRes.json()
    const systemUrls: MetadataRoute.Sitemap = systems.map((s) => ({
      url: `${SITE_URL}/system/${s.id}`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.8,
    }))

    // Priority tiers by depth: sectors (level 1) = 0.85, subsectors
    // (level 2) = 0.75, industry groups (level 3) = 0.65. Shallow pages
    // aggregate more cross-system content so they are more important for
    // SEO; deeper pages are long-tail.
    const codeNodeUrls: MetadataRoute.Sitemap = deepNodesPerSystem.flatMap(
      ({ id, nodes }) =>
        nodes.map((node) => ({
          url: `${SITE_URL}/codes/${id}/${encodeURIComponent(node.code)}`,
          lastModified: new Date(),
          changeFrequency: 'monthly' as const,
          priority: node.level === 1 ? 0.85 : node.level === 2 ? 0.75 : 0.65,
        })),
    )

    // Crosswalk pair hubs: one page per major-to-major pair that has
    // edges. Detail pages (level-1 source code x target system) are
    // generated below from the already-walked deepNodesPerSystem, so we
    // do not re-query.
    const majorPairs = stats.filter(
      (s) =>
        MAJOR_SYSTEM_SET.has(s.source_system) &&
        MAJOR_SYSTEM_SET.has(s.target_system) &&
        s.edge_count > 0,
    )
    const crosswalkPairUrls: MetadataRoute.Sitemap = majorPairs.map((p) => ({
      url: `${SITE_URL}/crosswalks/${p.source_system}/to/${p.target_system}`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.85,
    }))

    const sectorNodesBySystem = new Map(
      deepNodesPerSystem.map(({ id, nodes }) => [
        id,
        nodes.filter((n) => n.level === 1),
      ]),
    )
    const crosswalkDetailUrls: MetadataRoute.Sitemap = majorPairs.flatMap(
      (p) => {
        const sectors = sectorNodesBySystem.get(p.source_system) ?? []
        return sectors.map((node) => ({
          url: `${SITE_URL}/crosswalks/${p.source_system}/${encodeURIComponent(node.code)}/${p.target_system}`,
          lastModified: new Date(),
          changeFrequency: 'monthly' as const,
          priority: 0.7,
        }))
      },
    )

    const countryUrls: MetadataRoute.Sitemap = countries.map((c) => ({
      url: `${SITE_URL}/country/${c.code.toUpperCase()}`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: c.has_official ? 0.75 : 0.6,
    }))

    return [
      ...staticPages,
      ...codesSystemHubs,
      ...codeNodeUrls,
      ...queryPages,
      ...crosswalkPairUrls,
      ...crosswalkDetailUrls,
      ...systemUrls,
      ...countryUrls,
    ]
  } catch {
    return [...staticPages, ...codesSystemHubs, ...queryPages]
  }
}

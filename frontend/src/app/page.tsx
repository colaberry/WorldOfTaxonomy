import type { Metadata } from 'next'
import { HomeContent } from './HomeContent'
import { serverGetSystems, serverGetStats } from '@/lib/server-api'

export const metadata: Metadata = {
  title: 'World Of Taxonomy - Global Classification Knowledge Graph',
  description:
    'Explore 1,000+ global classification systems with 1.2M+ codes. ' +
    'Search NAICS, ISIC, HS, ICD, SOC codes and discover cross-system mappings.',
  openGraph: {
    title: 'World Of Taxonomy - Global Classification Knowledge Graph',
    description: '1,000+ systems, 1.2M+ codes, 321K+ crosswalk edges. Open source.',
    url: 'https://worldoftaxonomy.com',
    type: 'website',
  },
}

export default async function HomePage() {
  let systems = null
  let stats = null

  try {
    ;[systems, stats] = await Promise.all([
      serverGetSystems(),
      serverGetStats(),
    ])
  } catch {
    // Backend unavailable - client component will fetch on its own
  }

  return <HomeContent initialSystems={systems} initialStats={stats} />
}

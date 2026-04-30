import type { Metadata } from 'next'
import { ExploreWrapper } from './ExploreContent'
import { serverGetSystems, serverGetStats } from '@/lib/server-api'

export const metadata: Metadata = {
  title: 'Explore - WorldOfTaxonomy',
  description:
    'Search 1.2M+ classification codes across 1,000+ systems, or browse by category. ' +
    'Industry, health, trade, occupations, regulatory, and more.',
  openGraph: {
    title: 'Explore - WorldOfTaxonomy',
    description: 'Search 1.2M+ codes across 1,000+ classification systems.',
    url: 'https://worldoftaxonomy.com/explore',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/explore' },
}

export default async function ExplorePage() {
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

  return <ExploreWrapper initialSystems={systems} initialStats={stats} />
}

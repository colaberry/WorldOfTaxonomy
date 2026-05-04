import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Explore Classifications - World Of Taxonomy',
  description:
    'Search across 1,000+ classification systems and 1.2M+ codes. ' +
    'Find NAICS, ISIC, HS, ICD, SOC, ISCO codes instantly.',
  openGraph: {
    title: 'Explore Classifications - World Of Taxonomy',
    description: 'Search 1.2M+ classification codes across 1,000+ global systems.',
    url: 'https://worldoftaxonomy.com/explore',
    type: 'website',
  },
}

export default function ExploreLayout({ children }: { children: React.ReactNode }) {
  return children
}

import type { Metadata } from 'next'
import Link from 'next/link'
import { getWikiMeta } from '@/lib/wiki'
import { BookOpen } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Classification Guides - World Of Taxonomy',
  description:
    'Curated guides for navigating 1,000+ classification systems. Industry classification, medical coding, trade codes, occupation systems, crosswalk maps, and more.',
  openGraph: {
    title: 'Classification Guides - World Of Taxonomy',
    description: 'Curated guides for 1,000+ classification systems',
    url: 'https://worldoftaxonomy.com/guide',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/guide' },
}

export default function GuidePage() {
  const pages = getWikiMeta()

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <div className="flex items-center gap-3 mb-8">
        <BookOpen className="h-7 w-7 text-primary" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Classification Guides</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Curated knowledge for navigating 1,000+ classification systems, 1.2M+ nodes, and 321K+
            crosswalk edges.
          </p>
        </div>
      </div>

      <div className="grid gap-4">
        {pages.map((page) => (
          <Link
            key={page.slug}
            href={`/guide/${page.slug}`}
            className="block p-5 rounded-lg border border-border/50 bg-card hover:bg-secondary/30 transition-colors group"
          >
            <h2 className="text-lg font-semibold group-hover:text-primary transition-colors">
              {page.title}
            </h2>
            <p className="text-sm text-muted-foreground mt-1.5">{page.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}

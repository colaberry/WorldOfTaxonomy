import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { QUERIES } from './queries'

export const metadata: Metadata = {
  title: 'Find Codes by Business Type - NAICS, ISIC, SIC, NACE | WorldOfTaxonomy',
  description:
    'Pre-matched classification codes for common business types: telemedicine platforms, bakeries, SaaS startups, trucking companies, and more. Every answer across every major system.',
  openGraph: {
    title: 'Classification Codes by Business Type',
    description:
      'Curated answers for common business classifications across NAICS, ISIC, SIC, NACE, SOC, and HS.',
    url: 'https://worldoftaxonomy.com/codes/q',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/codes/q' },
}

export default function QueryIndexPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      {/* Breadcrumb */}
      <nav className="text-xs text-muted-foreground" aria-label="Breadcrumb">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li><Link href="/" className="hover:text-foreground">Home</Link></li>
          <li aria-hidden="true">/</li>
          <li><Link href="/codes" className="hover:text-foreground">Codes</Link></li>
          <li aria-hidden="true">/</li>
          <li className="text-foreground font-medium">By business type</li>
        </ol>
      </nav>

      <header className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Classification Codes by Business Type
        </h1>
        <p className="text-lg text-muted-foreground max-w-3xl">
          Pick your business type to see the NAICS, ISIC, SIC, NACE, SOC, and HS
          codes that apply. Each answer links to the full code definition with
          cross-system crosswalks.
        </p>
        <p className="text-sm text-muted-foreground">
          {QUERIES.length} curated business types.{' '}
          <Link href="/classify" className="text-primary underline">
            Don&apos;t see yours? Try the free classifier.
          </Link>
        </p>
      </header>

      <section>
        <ul className="grid sm:grid-cols-2 gap-2">
          {QUERIES.map((q) => (
            <li key={q.slug}>
              <Link
                href={`/codes/q/${q.slug}`}
                className="block rounded-lg border border-border bg-card px-4 py-3 hover:border-primary/50 hover:bg-muted/30 transition-colors group"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium capitalize">{q.query}</div>
                    <div className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                      {q.hint}
                    </div>
                  </div>
                  <ArrowRight className="size-4 text-muted-foreground group-hover:text-primary mt-0.5 shrink-0" />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

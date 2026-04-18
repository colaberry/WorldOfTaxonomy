import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { serverGetSystems } from '@/lib/server-api'
import type { ClassificationSystem } from '@/lib/types'
import { getSystemColor } from '@/lib/colors'
import { MAJOR_SYSTEMS } from './constants'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Classification Codes - NAICS, ISIC, SIC, NACE, SOC, HS | WorldOfTaxonomy',
  description:
    'Browse classification codes across the major industry, occupational, and product systems. Every sector defined, every code mapped across systems.',
  openGraph: {
    title: 'Classification Codes Directory',
    description:
      'NAICS, ISIC, SIC, NACE, ANZSIC, NIC, SOC, ISCO, HS, CPC - every sector, every code, every crosswalk.',
    url: 'https://worldoftaxonomy.com/codes',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/codes' },
}

export default async function CodesHubPage() {
  let systems: ClassificationSystem[]
  try {
    systems = await serverGetSystems()
  } catch {
    systems = []
  }
  const covered = systems.filter((s) => MAJOR_SYSTEMS.includes(s.id))

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      <header className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Classification Codes Directory
        </h1>
        <p className="text-lg text-muted-foreground max-w-3xl">
          Every major industry, occupational, and product classification system,
          with full definitions and cross-system crosswalks. Pick a system below
          to browse its sectors.
        </p>
      </header>

      <section className="grid sm:grid-cols-2 gap-4">
        {covered.map((system) => {
          const color = getSystemColor(system.id)
          return (
            <Link
              key={system.id}
              href={`/codes/${system.id}`}
              className="rounded-xl border border-border bg-card p-5 hover:border-primary/50 transition-colors group space-y-2"
            >
              <div className="flex items-center gap-2">
                <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-xs uppercase tracking-wide text-muted-foreground">
                  {system.region ?? 'Global'}
                </span>
              </div>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h2 className="text-base font-semibold">{system.full_name ?? system.name}</h2>
                  <p className="text-xs text-muted-foreground mt-1">
                    {system.node_count.toLocaleString()} codes
                    {system.authority ? ` · ${system.authority}` : ''}
                  </p>
                </div>
                <ArrowRight className="size-4 text-muted-foreground group-hover:text-primary mt-1 shrink-0" />
              </div>
            </Link>
          )
        })}
      </section>

      <section className="grid sm:grid-cols-2 gap-4">
        <Link
          href="/codes/q"
          className="rounded-xl border border-border bg-card p-5 hover:border-primary/50 transition-colors group space-y-1"
        >
          <h2 className="text-sm font-semibold flex items-center gap-2">
            Browse by business type
            <ArrowRight className="size-3.5 group-hover:translate-x-0.5 transition-transform" />
          </h2>
          <p className="text-xs text-muted-foreground">
            Pre-matched codes for common business types - bakeries, SaaS startups, trucking companies, and more.
          </p>
        </Link>
        <Link
          href="/classify"
          className="rounded-xl border border-border bg-card p-5 hover:border-primary/50 transition-colors group space-y-1"
        >
          <h2 className="text-sm font-semibold flex items-center gap-2">
            Classify a specific business
            <ArrowRight className="size-3.5 group-hover:translate-x-0.5 transition-transform" />
          </h2>
          <p className="text-xs text-muted-foreground">
            Describe your business in plain English and we&apos;ll find matching codes across every system.
          </p>
        </Link>
      </section>
    </div>
  )
}

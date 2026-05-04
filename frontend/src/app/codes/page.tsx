import type { Metadata } from 'next'
import Link from 'next/link'
import { Suspense } from 'react'
import { ArrowRight, ChevronDown } from 'lucide-react'
import { serverGetSystems, serverGetStats } from '@/lib/server-api'
import type { ClassificationSystem, CrosswalkStat } from '@/lib/types'
import { getSystemColor } from '@/lib/colors'
import { SystemCard, type CrosswalkBadge } from './SystemCard'
import { classifyRegion, REGION_ORDER, type RegionBucket } from './regions'
import { CountryFilterShell } from './CountryFilterShell'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Classification Codes - NAICS, ISIC, SIC, NACE, SOC, HS | World Of Taxonomy',
  description:
    'Global directory of 1,000+ classification systems. Browse every sector of NAICS, ISIC, NACE, HS, SOC, and national derivatives with inline crosswalks.',
  openGraph: {
    title: 'Classification Codes Directory',
    description:
      'Global directory of 1,000+ classification systems with inline sectors and crosswalks.',
    url: 'https://worldoftaxonomy.com/codes',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/codes' },
}

function systemLabel(systems: ClassificationSystem[], id: string): string {
  return systems.find((s) => s.id === id)?.name ?? id
}

export default async function CodesHubPage() {
  let systems: ClassificationSystem[] = []
  let stats: CrosswalkStat[] = []
  try {
    ;[systems, stats] = await Promise.all([
      serverGetSystems(),
      serverGetStats().catch(() => [] as CrosswalkStat[]),
    ])
  } catch {
    systems = []
  }

  const crosswalksBySource = new Map<string, CrosswalkBadge[]>()
  for (const s of stats) {
    if (s.edge_count <= 0) continue
    const list = crosswalksBySource.get(s.source_system) ?? []
    list.push({
      target_system: s.target_system,
      target_name: systemLabel(systems, s.target_system),
      edge_count: s.edge_count,
      color: getSystemColor(s.target_system),
    })
    crosswalksBySource.set(s.source_system, list)
  }
  for (const list of crosswalksBySource.values()) {
    list.sort((a, b) => b.edge_count - a.edge_count)
  }

  const grouped = new Map<RegionBucket, ClassificationSystem[]>()
  for (const bucket of REGION_ORDER) grouped.set(bucket, [])
  for (const sys of systems) {
    const bucket = classifyRegion(sys.region)
    grouped.get(bucket)!.push(sys)
  }
  for (const list of grouped.values()) {
    list.sort((a, b) => b.node_count - a.node_count)
  }

  const totalSystems = systems.length
  const totalCodes = systems.reduce((acc, s) => acc + s.node_count, 0)
  const totalEdges = stats.reduce((acc, s) => acc + s.edge_count, 0)

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      <header className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Classification Codes Directory
        </h1>
        <p className="text-lg text-muted-foreground max-w-3xl">
          {totalSystems.toLocaleString()} classification systems, {totalCodes.toLocaleString()}+ codes, and {totalEdges.toLocaleString()}+ crosswalk edges, organized by region. Click any system to expand its sectors and crosswalks inline.
        </p>
      </header>

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

      <Suspense fallback={<div className="text-sm text-muted-foreground">Loading country filter...</div>}>
        <CountryFilterShell>
          {REGION_ORDER.map((bucket) => {
            const list = grouped.get(bucket) ?? []
            if (list.length === 0) return null
            const isNorthAmerica = bucket === 'North America'
            const summaryCodes = list.reduce((acc, s) => acc + s.node_count, 0)

            return (
              <details
                key={bucket}
                open={isNorthAmerica}
                className="group border-b border-border/60 pb-4"
              >
                <summary className="flex items-baseline justify-between gap-3 cursor-pointer list-none py-3">
                  <div className="flex items-baseline gap-3">
                    <ChevronDown className="size-4 text-muted-foreground transition-transform group-open:rotate-0 -rotate-90" />
                    <h2 className="text-xl sm:text-2xl font-semibold tracking-tight">
                      {bucket}
                    </h2>
                    <span className="text-xs text-muted-foreground">
                      {list.length} {list.length === 1 ? 'system' : 'systems'} · {summaryCodes.toLocaleString()} codes
                    </span>
                  </div>
                </summary>
                <div className="grid sm:grid-cols-2 gap-3 mt-3">
                  {list.map((sys) => (
                    <SystemCard
                      key={sys.id}
                      system={sys}
                      systemColor={getSystemColor(sys.id)}
                      crosswalks={crosswalksBySource.get(sys.id) ?? []}
                    />
                  ))}
                </div>
              </details>
            )
          })}
        </CountryFilterShell>
      </Suspense>
    </div>
  )
}

import type { Metadata } from 'next'
import Link from 'next/link'
import { ArrowRight, Network } from 'lucide-react'
import { serverGetStats, serverGetSystems } from '@/lib/server-api'
import {
  getStaticSystems,
  getStaticStats,
  getStaticAllSections,
} from '@/lib/crosswalk-data'
import CrosswalkExplorerClient from './CrosswalkExplorerClient'
import type { ClassificationSystem, CrosswalkStat } from '@/lib/types'
import { MAJOR_SYSTEMS } from '../codes/constants'
import { getSystemColor } from '@/lib/colors'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Classification Crosswalks - Every Mapping Between Systems',
  description:
    'Browse 321,000+ classification crosswalk edges between NAICS, ISIC, NACE, HS, CPC, SOC, ISCO, and more. Sector-by-sector mappings with match types and official source notes.',
  alternates: { canonical: 'https://worldoftaxonomy.com/crosswalks' },
  openGraph: {
    title: 'Classification Crosswalks',
    description:
      "Sector-level mappings between the world's major classification systems.",
    url: 'https://worldoftaxonomy.com/crosswalks',
    type: 'website',
  },
  keywords: [
    'classification crosswalk',
    'NAICS ISIC mapping',
    'NACE ISIC crosswalk',
    'HS CPC mapping',
    'SOC ISCO crosswalk',
    'industry classification mapping',
  ],
}

function systemLabel(systems: ClassificationSystem[], id: string): string {
  return systems.find((s) => s.id === id)?.name ?? id
}

export default async function CrosswalksIndexPage({
  searchParams,
}: {
  searchParams: Promise<{ source?: string; target?: string }>
}) {
  const { source, target } = await searchParams
  const [stats, systems] = await Promise.all([
    serverGetStats().catch(() => [] as CrosswalkStat[]),
    serverGetSystems().catch(() => [] as ClassificationSystem[]),
  ])

  const majorSet = new Set(MAJOR_SYSTEMS)
  const majorPairs = stats
    .filter(
      (s) =>
        majorSet.has(s.source_system) &&
        majorSet.has(s.target_system) &&
        s.edge_count > 0,
    )
    .sort((a, b) => b.edge_count - a.edge_count)

  const totalEdges = stats.reduce((acc, s) => acc + s.edge_count, 0)
  const totalPairs = stats.filter((s) => s.edge_count > 0).length

  const allStaticSystems = getStaticSystems()
  const staticStats = getStaticStats()
  const allSections = getStaticAllSections()
  const crosswalkedIds = new Set<string>()
  for (const st of staticStats) {
    crosswalkedIds.add(st.source_system)
    crosswalkedIds.add(st.target_system)
  }
  const explorerSystems = allStaticSystems.filter((s) =>
    crosswalkedIds.has(s.id),
  )

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      <section className="space-y-3">
        <CrosswalkExplorerClient
          systems={explorerSystems}
          stats={staticStats}
          allSections={allSections}
          initialSource={source}
          initialTarget={target}
        />
      </section>

      <header className="space-y-4">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
          <Network className="size-3.5" />
          Crosswalks
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Classification Crosswalks
        </h1>
        <p className="text-lg text-muted-foreground max-w-3xl">
          {totalEdges.toLocaleString()}+ equivalence edges across{' '}
          {totalPairs.toLocaleString()} system pairs. Translate codes between
          NAICS, ISIC, NACE, HS, CPC, SOC, ISCO, and more. Every mapping is
          sourced from an official concordance and carries a match type.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold">Major system pairs</h2>
        <ul className="grid sm:grid-cols-2 gap-3">
          {majorPairs.map((pair) => {
            const colorA = getSystemColor(pair.source_system)
            const colorB = getSystemColor(pair.target_system)
            return (
              <li key={`${pair.source_system}-${pair.target_system}`}>
                <Link
                  href={`/crosswalks/${pair.source_system}/to/${pair.target_system}`}
                  className="block rounded-xl border border-border bg-card px-4 py-4 hover:border-primary/50 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex items-center gap-2 text-sm font-semibold">
                    <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: colorA }} />
                    {systemLabel(systems, pair.source_system)}
                    <ArrowRight className="size-3.5 text-muted-foreground" />
                    <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: colorB }} />
                    {systemLabel(systems, pair.target_system)}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1.5">
                    {pair.edge_count.toLocaleString()} {pair.edge_count === 1 ? 'edge' : 'edges'}
                    {pair.exact_count > 0 && (
                      <span>, {pair.exact_count.toLocaleString()} exact</span>
                    )}
                  </div>
                </Link>
              </li>
            )
          })}
        </ul>
      </section>

      <section className="rounded-xl border border-border bg-card p-5 sm:p-6 space-y-3">
        <h2 className="text-sm font-semibold">Other crosswalk pairs</h2>
        <p className="text-xs text-muted-foreground">
          WoT also carries {Math.max(0, totalPairs - majorPairs.length).toLocaleString()}+
          pairs involving national derivatives (WZ, ATECO, NAF, CIIU variants,
          etc.) and domain taxonomies. Use the interactive graph above to
          browse any pair.
        </p>
      </section>
    </div>
  )
}

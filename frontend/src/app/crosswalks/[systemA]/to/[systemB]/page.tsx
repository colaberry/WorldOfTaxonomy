import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ArrowRight, Network } from 'lucide-react'
import {
  serverGetStats,
  serverGetSystems,
  serverListNodesUpToLevel,
} from '@/lib/server-api'
import type {
  ClassificationNode,
  ClassificationSystem,
  CrosswalkStat,
} from '@/lib/types'
import { MAJOR_SYSTEMS, isMajorSystem } from '../../../../codes/constants'
import { getSystemColor } from '@/lib/colors'

interface Props {
  params: Promise<{ systemA: string; systemB: string }>
}

export const revalidate = 3600

export async function generateStaticParams() {
  const stats = await serverGetStats().catch(() => [] as CrosswalkStat[])
  const majorSet = new Set(MAJOR_SYSTEMS)
  return stats
    .filter(
      (s) =>
        majorSet.has(s.source_system) &&
        majorSet.has(s.target_system) &&
        s.edge_count > 0,
    )
    .map((s) => ({ systemA: s.source_system, systemB: s.target_system }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { systemA, systemB } = await params
  try {
    const systems = await serverGetSystems()
    const sysA = systems.find((s) => s.id === systemA)
    const sysB = systems.find((s) => s.id === systemB)
    const aLabel = sysA?.name ?? systemA
    const bLabel = sysB?.name ?? systemB
    const aFull = sysA?.full_name ?? aLabel
    const bFull = sysB?.full_name ?? bLabel
    const title = `${aLabel} to ${bLabel} Crosswalk - Complete Code Mapping`
    const description = `Full ${aFull} to ${bFull} crosswalk. Browse sector-level mappings, translate individual codes, and download the complete concordance.`
    const canonical = `https://worldoftaxonomy.com/crosswalks/${systemA}/to/${systemB}`
    return {
      title,
      description,
      alternates: { canonical },
      openGraph: {
        title: `${aLabel} to ${bLabel} Crosswalk`,
        description,
        url: canonical,
        type: 'article',
      },
      keywords: [
        `${aLabel} to ${bLabel}`,
        `${aLabel} ${bLabel} crosswalk`,
        `${aLabel} ${bLabel} mapping`,
        `${aLabel} ${bLabel} concordance`,
        'classification crosswalk',
      ],
    }
  } catch {
    return { title: 'Classification Crosswalk - WorldOfTaxonomy' }
  }
}

export default async function CrosswalkPairPage({ params }: Props) {
  const { systemA, systemB } = await params
  if (!isMajorSystem(systemA) || !isMajorSystem(systemB) || systemA === systemB) {
    notFound()
  }

  let systems: ClassificationSystem[]
  let stats: CrosswalkStat[]
  let sourceSectors: ClassificationNode[]
  try {
    ;[systems, stats, sourceSectors] = await Promise.all([
      serverGetSystems(),
      serverGetStats(),
      serverListNodesUpToLevel(systemA, 1).catch(
        () => [] as ClassificationNode[],
      ),
    ])
  } catch {
    notFound()
  }

  const sysA = systems.find((s) => s.id === systemA)
  const sysB = systems.find((s) => s.id === systemB)
  if (!sysA || !sysB) notFound()

  const pairStat = stats.find(
    (s) => s.source_system === systemA && s.target_system === systemB,
  )
  const totalEdges = pairStat?.edge_count ?? 0

  const colorA = getSystemColor(systemA)
  const colorB = getSystemColor(systemB)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: 'https://worldoftaxonomy.com',
      },
      {
        '@type': 'ListItem',
        position: 2,
        name: 'Crosswalks',
        item: 'https://worldoftaxonomy.com/crosswalks',
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: `${sysA.name} to ${sysB.name}`,
        item: `https://worldoftaxonomy.com/crosswalks/${systemA}/to/${systemB}`,
      },
    ],
  }

  return (
    <article className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <nav className="text-xs text-muted-foreground" aria-label="Breadcrumb">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li><Link href="/" className="hover:text-foreground">Home</Link></li>
          <li aria-hidden="true">/</li>
          <li><Link href="/crosswalks" className="hover:text-foreground">Crosswalks</Link></li>
          <li aria-hidden="true">/</li>
          <li className="text-foreground font-medium">
            {sysA.name} to {sysB.name}
          </li>
        </ol>
      </nav>

      <header className="space-y-4">
        <div className="flex items-center gap-3 text-xs uppercase tracking-wide text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: colorA }} />
            {sysA.full_name ?? sysA.name}
          </span>
          <ArrowRight className="size-3" />
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: colorB }} />
            {sysB.full_name ?? sysB.name}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          {sysA.name} to {sysB.name} Crosswalk
        </h1>
        <p className="text-lg text-muted-foreground">
          Full concordance from {sysA.full_name ?? sysA.name} to {sysB.full_name ?? sysB.name}.
          {totalEdges > 0
            ? ` ${totalEdges.toLocaleString()} official equivalence ${totalEdges === 1 ? 'edge' : 'edges'}. Pick a sector below to see its mapping, or use the interactive crosswalk explorer for full-tree drill-down.`
            : ' Interactive drill-down available in the crosswalk explorer.'}
        </p>
        <div className="flex flex-wrap gap-3">
          <Link
            href={`/crosswalks?source=${systemA}&target=${systemB}`}
            className="inline-flex items-center gap-2 rounded-full border border-primary bg-primary text-primary-foreground px-4 py-2 text-sm hover:bg-primary/90"
          >
            <Network className="size-4" />
            Open interactive explorer
          </Link>
          <Link
            href={`/codes/${systemA}`}
            className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm hover:border-primary/50"
          >
            Browse {sysA.name} codes
          </Link>
        </div>
      </header>

      {sourceSectors.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold">
            {sysA.name} sectors mapped to {sysB.name}
          </h2>
          <ul className="grid sm:grid-cols-2 gap-2">
            {sourceSectors.map((node) => (
              <li key={node.code}>
                <Link
                  href={`/crosswalks/${systemA}/${encodeURIComponent(node.code)}/${systemB}`}
                  className="block rounded-lg border border-border bg-card px-4 py-3 hover:border-primary/50 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-xs text-muted-foreground">{node.code}</span>
                    <span className="text-sm font-medium">{node.title}</span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {sysA.name} {node.code} to {sysB.name} mapping
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  )
}

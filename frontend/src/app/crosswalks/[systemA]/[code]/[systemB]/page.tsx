import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ArrowRight, ArrowLeftRight, Layers, Network } from 'lucide-react'
import {
  serverGetNode,
  serverGetEquivalences,
  serverGetSystems,
  serverGetStats,
  serverListNodesUpToLevel,
} from '@/lib/server-api'
import type {
  ClassificationNode,
  ClassificationSystem,
  CrosswalkStat,
  Equivalence,
} from '@/lib/types'
import { MAJOR_SYSTEMS, isMajorSystem } from '../../../../codes/constants'
import { getSystemColor } from '@/lib/colors'

interface Props {
  params: Promise<{ systemA: string; code: string; systemB: string }>
}

export const revalidate = 3600
export const dynamicParams = true

export async function generateStaticParams() {
  // Only pre-render crosswalk pages for pairs that actually have edges
  // and where both sides are major systems. At level 1 (sectors) this
  // bounds the build to a few hundred pages; deeper codes are served
  // on-demand via ISR.
  const stats = await serverGetStats().catch(() => [] as CrosswalkStat[])
  const majorSet = new Set(MAJOR_SYSTEMS)
  const pairs = stats.filter(
    (s) =>
      majorSet.has(s.source_system) &&
      majorSet.has(s.target_system) &&
      s.edge_count > 0,
  )

  const params: Array<{ systemA: string; code: string; systemB: string }> = []
  const seenSourceCodes = new Map<string, ClassificationNode[]>()
  for (const pair of pairs) {
    let sourceSectors = seenSourceCodes.get(pair.source_system)
    if (!sourceSectors) {
      sourceSectors = await serverListNodesUpToLevel(pair.source_system, 1).catch(
        () => [] as ClassificationNode[],
      )
      seenSourceCodes.set(pair.source_system, sourceSectors)
    }
    for (const node of sourceSectors) {
      params.push({
        systemA: pair.source_system,
        code: encodeURIComponent(node.code),
        systemB: pair.target_system,
      })
    }
  }
  return params
}

function systemName(systems: ClassificationSystem[], id: string): string {
  return systems.find((s) => s.id === id)?.name ?? id
}

function systemFullName(systems: ClassificationSystem[], id: string): string {
  const s = systems.find((sys) => sys.id === id)
  return s?.full_name ?? s?.name ?? id
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { systemA, code, systemB } = await params
  const nodeCode = decodeURIComponent(code)
  try {
    const [node, systems] = await Promise.all([
      serverGetNode(systemA, nodeCode),
      serverGetSystems(),
    ])
    const sysA = systems.find((s) => s.id === systemA)
    const sysB = systems.find((s) => s.id === systemB)
    const aLabel = sysA?.name ?? systemA
    const bLabel = sysB?.name ?? systemB
    const aFull = sysA?.full_name ?? aLabel
    const bFull = sysB?.full_name ?? bLabel
    const title = `${aLabel} ${nodeCode} to ${bLabel} - ${node.title} Crosswalk`
    const description = node.description?.trim()
      ? `${aLabel} ${nodeCode} (${node.title}) mapped to ${bLabel}. ${node.description.trim().slice(0, 160)}`
      : `Crosswalk from ${aFull} code ${nodeCode} "${node.title}" to equivalent ${bFull} codes. Official mapping with match types and source notes.`
    const canonical = `https://worldoftaxonomy.com/crosswalks/${systemA}/${code}/${systemB}`
    return {
      title,
      description,
      alternates: { canonical },
      openGraph: {
        title: `${aLabel} ${nodeCode} to ${bLabel}`,
        description: `Crosswalk from ${aFull} code ${nodeCode} "${node.title}" to ${bFull}.`,
        url: canonical,
        type: 'article',
      },
      keywords: [
        `${aLabel} to ${bLabel}`,
        `${aLabel} ${nodeCode} ${bLabel}`,
        `${aLabel} ${bLabel} crosswalk`,
        `${aLabel} ${bLabel} mapping`,
        `${nodeCode} ${bLabel} equivalent`,
        'classification crosswalk',
      ],
    }
  } catch {
    return { title: 'Classification Crosswalk - World Of Taxonomy' }
  }
}

function buildJsonLd(
  sysA: ClassificationSystem,
  sysB: ClassificationSystem,
  node: ClassificationNode,
  edges: Equivalence[],
  url: string,
): object[] {
  const breadcrumb = {
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
        item: `https://worldoftaxonomy.com/crosswalks/${sysA.id}/to/${sysB.id}`,
      },
      {
        '@type': 'ListItem',
        position: 4,
        name: `${node.code} ${node.title}`,
        item: url,
      },
    ],
  }

  const definedTerm = {
    '@context': 'https://schema.org',
    '@type': 'DefinedTerm',
    name: `${sysA.name} ${node.code} to ${sysB.name}`,
    termCode: node.code,
    description:
      `Crosswalk mapping from ${sysA.full_name ?? sysA.name} code ${node.code} (${node.title}) to ${sysB.full_name ?? sysB.name}. ${edges.length} official ${edges.length === 1 ? 'equivalence' : 'equivalences'}.`,
    url,
    inDefinedTermSet: {
      '@type': 'DefinedTermSet',
      name: `${sysA.full_name ?? sysA.name} to ${sysB.full_name ?? sysB.name} crosswalk`,
      url: `https://worldoftaxonomy.com/crosswalks/${sysA.id}/to/${sysB.id}`,
    },
  }

  return [breadcrumb, definedTerm]
}

export default async function CrosswalkDetailPage({ params }: Props) {
  const { systemA, code, systemB } = await params
  if (systemA === systemB) {
    notFound()
  }
  const nodeCode = decodeURIComponent(code)

  let node: ClassificationNode
  let allEquivalences: Equivalence[]
  let systems: ClassificationSystem[]
  try {
    ;[node, allEquivalences, systems] = await Promise.all([
      serverGetNode(systemA, nodeCode),
      serverGetEquivalences(systemA, nodeCode),
      serverGetSystems(),
    ])
  } catch {
    notFound()
  }

  const sysA = systems.find((s) => s.id === systemA)
  const sysB = systems.find((s) => s.id === systemB)
  if (!sysA || !sysB) notFound()

  const edges = allEquivalences.filter((e) => e.target_system === systemB)
  const colorA = getSystemColor(systemA)
  const colorB = getSystemColor(systemB)
  const url = `https://worldoftaxonomy.com/crosswalks/${systemA}/${code}/${systemB}`
  const jsonLd = buildJsonLd(sysA, sysB, node, edges, url)

  const otherTargetSystems = Array.from(
    new Set(allEquivalences.map((e) => e.target_system)),
  )
    .filter((t) => t !== systemB && isMajorSystem(t))
    .slice(0, 8)

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
          <li>
            <Link
              href={`/crosswalks/${sysA.id}/to/${sysB.id}`}
              className="hover:text-foreground"
            >
              {sysA.name} to {sysB.name}
            </Link>
          </li>
          <li aria-hidden="true">/</li>
          <li className="text-foreground font-medium">
            {node.code} {node.title}
          </li>
        </ol>
      </nav>

      <header className="space-y-4">
        <div className="flex items-center gap-3 text-xs uppercase tracking-wide text-muted-foreground">
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: colorA }} />
            {systemFullName(systems, systemA)}
          </span>
          <ArrowRight className="size-3" />
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: colorB }} />
            {systemFullName(systems, systemB)}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          {sysA.name}{' '}
          <span className="font-mono text-primary">{node.code}</span>{' '}
          to {sysB.name}
        </h1>
        <p className="text-lg text-muted-foreground">
          {edges.length > 0
            ? `Crosswalk mapping from ${sysA.name} ${node.code} "${node.title}" to ${sysB.name}. ${edges.length} official ${edges.length === 1 ? 'equivalence' : 'equivalences'}.`
            : `No direct ${sysA.name} to ${sysB.name} mapping is available for code ${node.code}. Related crosswalks to other systems appear below.`}
        </p>
      </header>

      {edges.length > 0 && (
        <section className="rounded-xl border border-primary/30 bg-primary/5 p-5 sm:p-6 space-y-4">
          <div className="flex items-start gap-2">
            <Network className="size-4 text-primary mt-1" />
            <div>
              <h2 className="text-sm font-semibold">
                {sysA.name} {node.code} in {sysB.name}
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Each entry is an official equivalence edge. Click to see the
                full {sysB.name} definition, hierarchy, and its own crosswalks.
              </p>
            </div>
          </div>
          <ul className="divide-y divide-border rounded-lg border border-border bg-card overflow-hidden">
            {edges.map((edge, i) => (
              <li key={`${edge.target_code}-${i}`}>
                <Link
                  href={`/codes/${edge.target_system}/${encodeURIComponent(edge.target_code)}`}
                  className="flex items-start justify-between gap-4 px-4 py-3 hover:bg-muted/50 transition-colors group"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-sm font-semibold">
                        {edge.target_code}
                      </span>
                      {edge.match_type && (
                        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                          {edge.match_type}
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-foreground/90 mt-0.5 group-hover:text-primary transition-colors">
                      {edge.target_title ?? '(no title)'}
                    </div>
                    {edge.notes && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {edge.notes}
                      </p>
                    )}
                  </div>
                  <ArrowRight className="size-4 text-muted-foreground group-hover:text-primary mt-1 shrink-0" />
                </Link>
              </li>
            ))}
          </ul>
          <div className="text-xs text-muted-foreground">
            Reverse direction:{' '}
            <Link
              href={`/crosswalks/${sysB.id}/to/${sysA.id}`}
              className="text-primary underline"
            >
              {sysB.name} to {sysA.name}
            </Link>
          </div>
        </section>
      )}

      <section className="rounded-xl border border-border bg-card p-5 sm:p-6 space-y-3">
        <h2 className="text-sm font-semibold flex items-center gap-2">
          <Layers className="size-4 text-muted-foreground" />
          About {sysA.name} {node.code}
        </h2>
        <p className="text-sm text-foreground/90">
          <span className="font-mono text-xs">{node.code}</span>{' '}
          <span className="font-semibold">{node.title}</span>
          {node.description?.trim() && (
            <span className="block text-muted-foreground mt-1.5">
              {node.description.trim()}
            </span>
          )}
        </p>
        <div className="flex flex-wrap gap-2 pt-1">
          <Link
            href={`/codes/${systemA}/${encodeURIComponent(node.code)}`}
            className="inline-flex items-center gap-1.5 text-xs rounded-full border border-border bg-background px-3 py-1.5 hover:border-primary/50 hover:bg-muted/30"
          >
            Full {sysA.name} definition
            <ArrowRight className="size-3" />
          </Link>
        </div>
      </section>

      {otherTargetSystems.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <ArrowLeftRight className="size-4 text-muted-foreground" />
            {sysA.name} {node.code} in other classification systems
          </h2>
          <ul className="flex flex-wrap gap-2">
            {otherTargetSystems.map((t) => {
              const targetColor = getSystemColor(t)
              return (
                <li key={t}>
                  <Link
                    href={`/crosswalks/${systemA}/${encodeURIComponent(node.code)}/${t}`}
                    className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs hover:border-primary/50 hover:bg-muted/30 transition-colors"
                  >
                    <span className="inline-block size-2 rounded-full" style={{ backgroundColor: targetColor }} />
                    <span>{systemName(systems, t)}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </section>
      )}
    </article>
  )
}

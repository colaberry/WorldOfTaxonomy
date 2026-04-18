import Link from 'next/link'
import type {
  ClassificationNode,
  ClassificationSystem,
  Equivalence,
} from '@/lib/types'
import { getSystemColor } from '@/lib/colors'
import { ArrowRight, ExternalLink, Layers, Network } from 'lucide-react'

interface SectorPageProps {
  system: ClassificationSystem
  allSystems: ClassificationSystem[]
  node: ClassificationNode
  ancestors: ClassificationNode[]
  children: ClassificationNode[]
  siblings: ClassificationNode[]
  equivalences: Equivalence[]
}

function systemName(systems: ClassificationSystem[], id: string): string {
  return systems.find((s) => s.id === id)?.name ?? id
}

function systemFullName(systems: ClassificationSystem[], id: string): string {
  const s = systems.find((sys) => sys.id === id)
  return s?.full_name ?? s?.name ?? id
}

function groupEquivalencesByTarget(
  equivalences: Equivalence[],
): Array<{ target_system: string; edges: Equivalence[] }> {
  const map = new Map<string, Equivalence[]>()
  for (const e of equivalences) {
    const bucket = map.get(e.target_system) ?? []
    bucket.push(e)
    map.set(e.target_system, bucket)
  }
  return Array.from(map.entries())
    .map(([target_system, edges]) => ({ target_system, edges }))
    .sort((a, b) => b.edges.length - a.edges.length)
}

function buildFaqItems(
  system: ClassificationSystem,
  node: ClassificationNode,
  children: ClassificationNode[],
  ancestors: ClassificationNode[],
  equivalenceGroups: Array<{ target_system: string; edges: Equivalence[] }>,
  allSystems: ClassificationSystem[],
): Array<{ question: string; answer: string }> {
  const items: Array<{ question: string; answer: string }> = []
  const systemLabel = system.name

  const baseDef =
    node.description?.trim() ||
    `${systemLabel} code ${node.code} covers "${node.title}" at level ${node.level} of the ${systemLabel} hierarchy.`
  items.push({
    question: `What is ${systemLabel} ${node.code}?`,
    answer: `${systemLabel} ${node.code} is "${node.title}". ${baseDef}`,
  })

  if (children.length > 0) {
    const sample = children
      .slice(0, 6)
      .map((c) => `${c.code} ${c.title}`)
      .join('; ')
    items.push({
      question: `What does ${systemLabel} ${node.code} include?`,
      answer: `${node.code} ${node.title} contains ${children.length} direct ${children.length === 1 ? 'subcategory' : 'subcategories'}: ${sample}${children.length > 6 ? '; and more.' : '.'}`,
    })
  }

  if (equivalenceGroups.length > 0) {
    const mapped = equivalenceGroups
      .slice(0, 4)
      .map((g) => {
        const name = systemName(allSystems, g.target_system)
        const codes = g.edges
          .slice(0, 3)
          .map((e) => e.target_code)
          .join(', ')
        const more = g.edges.length > 3 ? `, +${g.edges.length - 3} more` : ''
        return `${name} (${codes}${more})`
      })
      .join('; ')
    items.push({
      question: `How does ${systemLabel} ${node.code} map to other classification systems?`,
      answer: `${node.code} ${node.title} has equivalents in ${mapped}. These crosswalks let you translate this code between ${systemLabel} and ${equivalenceGroups.length} other classification ${equivalenceGroups.length === 1 ? 'system' : 'systems'}.`,
    })
  }

  if (ancestors.length > 0) {
    const parent = ancestors[ancestors.length - 1]
    items.push({
      question: `What is the parent category of ${node.code}?`,
      answer: `${node.code} ${node.title} sits under ${parent.code} ${parent.title} in the ${systemLabel} hierarchy.`,
    })
  } else {
    items.push({
      question: `Where does ${node.code} sit in the ${systemLabel} hierarchy?`,
      answer: `${node.code} ${node.title} is a top-level ${node.level === 1 ? 'section / sector' : `level-${node.level} node`} in ${systemLabel}. It has no parent category.`,
    })
  }

  return items
}

function buildJsonLd(
  system: ClassificationSystem,
  node: ClassificationNode,
  faqItems: Array<{ question: string; answer: string }>,
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
        name: 'Codes',
        item: 'https://worldoftaxonomy.com/codes',
      },
      {
        '@type': 'ListItem',
        position: 3,
        name: system.name,
        item: `https://worldoftaxonomy.com/codes/${system.id}`,
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
    name: `${node.code} ${node.title}`,
    termCode: node.code,
    description:
      node.description?.trim() ||
      `${system.name} classification code ${node.code} - ${node.title}`,
    url,
    inDefinedTermSet: {
      '@type': 'DefinedTermSet',
      name: system.full_name ?? system.name,
      url: `https://worldoftaxonomy.com/codes/${system.id}`,
    },
  }

  const faqPage = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqItems.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.answer,
      },
    })),
  }

  return [breadcrumb, definedTerm, faqPage]
}

export function SectorPage({
  system,
  allSystems,
  node,
  ancestors,
  children,
  siblings,
  equivalences,
}: SectorPageProps) {
  const parent = ancestors.length > 0 ? ancestors[ancestors.length - 1] : null
  const color = getSystemColor(system.id)
  const url = `https://worldoftaxonomy.com/codes/${system.id}/${encodeURIComponent(node.code)}`
  const equivalenceGroups = groupEquivalencesByTarget(equivalences)
  const faqItems = buildFaqItems(
    system,
    node,
    children,
    ancestors,
    equivalenceGroups,
    allSystems,
  )
  const jsonLd = buildJsonLd(system, node, faqItems, url)

  return (
    <article className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Breadcrumb */}
      <nav className="text-xs text-muted-foreground" aria-label="Breadcrumb">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li><Link href="/" className="hover:text-foreground">Home</Link></li>
          <li aria-hidden="true">/</li>
          <li><Link href="/codes" className="hover:text-foreground">Codes</Link></li>
          <li aria-hidden="true">/</li>
          <li>
            <Link
              href={`/codes/${system.id}`}
              className="hover:text-foreground"
            >
              {system.name}
            </Link>
          </li>
          <li aria-hidden="true">/</li>
          <li className="text-foreground font-medium">
            {node.code} {node.title}
          </li>
        </ol>
      </nav>

      {/* Header */}
      <header className="space-y-4">
        <div className="flex items-center gap-2">
          <span
            className="inline-block size-2.5 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="text-xs uppercase tracking-wide text-muted-foreground">
            {systemFullName(allSystems, system.id)}
            {system.region ? ` - ${system.region}` : ''}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          <span className="font-mono text-primary">{node.code}</span>{' '}
          <span>{node.title}</span>
        </h1>
        <p className="text-lg text-muted-foreground">
          {node.description?.trim() ||
            `${system.name} classification code ${node.code} covers "${node.title}" at level ${node.level} of the ${system.name} hierarchy.`}
        </p>
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground pt-1">
          <span>Level {node.level}</span>
          {children.length > 0 && (
            <span>{children.length} direct {children.length === 1 ? 'subcategory' : 'subcategories'}</span>
          )}
          {equivalences.length > 0 && (
            <span>{equivalences.length} cross-system {equivalences.length === 1 ? 'mapping' : 'mappings'}</span>
          )}
        </div>
      </header>

      {/* Hierarchy */}
      {ancestors.length > 0 && (
        <section className="rounded-xl border border-border bg-card p-5 sm:p-6 space-y-3">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            <Layers className="size-4 text-muted-foreground" />
            Where {node.code} sits in the {system.name} hierarchy
          </h2>
          <ol className="text-sm space-y-1.5">
            {ancestors.map((a) => (
              <li key={a.code} className="flex items-baseline gap-2">
                <span className="text-muted-foreground">{'>'.repeat(Math.max(1, a.level))}</span>
                <Link
                  href={`/codes/${system.id}/${encodeURIComponent(a.code)}`}
                  className="hover:text-primary hover:underline"
                >
                  <span className="font-mono text-xs">{a.code}</span>{' '}
                  <span>{a.title}</span>
                </Link>
              </li>
            ))}
            <li className="flex items-baseline gap-2 font-semibold">
              <span className="text-muted-foreground">{'>'.repeat(Math.max(1, node.level))}</span>
              <span>
                <span className="font-mono text-xs">{node.code}</span>{' '}
                <span>{node.title}</span>
              </span>
            </li>
          </ol>
        </section>
      )}

      {/* Cross-system crosswalks (THE MOAT) */}
      {equivalenceGroups.length > 0 && (
        <section className="rounded-xl border border-primary/30 bg-primary/5 p-5 sm:p-6 space-y-4">
          <div className="flex items-start gap-2">
            <Network className="size-4 text-primary mt-1" />
            <div>
              <h2 className="text-sm font-semibold">
                {node.code} in other classification systems
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Equivalent and related codes across {equivalenceGroups.length} other {equivalenceGroups.length === 1 ? 'system' : 'systems'}. Click any code to see its full definition, hierarchy, and crosswalks.
              </p>
            </div>
          </div>
          <div className="grid gap-3">
            {equivalenceGroups.map((group) => {
              const targetColor = getSystemColor(group.target_system)
              const targetName = systemName(allSystems, group.target_system)
              return (
                <div
                  key={group.target_system}
                  className="rounded-lg border border-border bg-card overflow-hidden"
                >
                  <div
                    className="px-4 py-2 border-b border-border flex items-center justify-between text-xs"
                    style={{ backgroundColor: `${targetColor}15` }}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="inline-block size-2 rounded-full"
                        style={{ backgroundColor: targetColor }}
                      />
                      <span className="font-semibold">{targetName}</span>
                    </div>
                    <span className="text-muted-foreground">
                      {group.edges.length} {group.edges.length === 1 ? 'mapping' : 'mappings'}
                    </span>
                  </div>
                  <ul className="divide-y divide-border">
                    {group.edges.slice(0, 10).map((edge, i) => (
                      <li key={`${edge.target_system}-${edge.target_code}-${i}`}>
                        <Link
                          href={`/codes/${group.target_system}/${encodeURIComponent(edge.target_code)}`}
                          className="flex items-start justify-between gap-4 px-4 py-2.5 hover:bg-muted/50 transition-colors group"
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
                  {group.edges.length > 10 && (
                    <div className="px-4 py-2 text-xs text-muted-foreground border-t border-border bg-muted/30">
                      +{group.edges.length - 10} more mappings. View the full crosswalk on the{' '}
                      <Link
                        href={`/crosswalk-explorer?source=${system.id}&target=${group.target_system}`}
                        className="text-primary underline"
                      >
                        crosswalk explorer
                      </Link>
                      .
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Subcategories */}
      {children.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold">
            Subcategories of {node.code} {node.title}
          </h2>
          <ul className="grid sm:grid-cols-2 gap-2">
            {children.map((c) => (
              <li key={c.code}>
                <Link
                  href={`/codes/${system.id}/${encodeURIComponent(c.code)}`}
                  className="block rounded-lg border border-border bg-card px-4 py-3 hover:border-primary/50 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-xs text-muted-foreground">{c.code}</span>
                    <span className="text-sm font-medium">{c.title}</span>
                  </div>
                  {c.description && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {c.description}
                    </p>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Peer codes (siblings) */}
      {parent && siblings.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold">
            Other {system.name} codes under{' '}
            <Link
              href={`/codes/${system.id}/${encodeURIComponent(parent.code)}`}
              className="text-primary hover:underline"
            >
              {parent.code} {parent.title}
            </Link>
          </h2>
          <ul className="flex flex-wrap gap-2">
            {siblings.map((s) => (
              <li key={s.code}>
                <Link
                  href={`/codes/${system.id}/${encodeURIComponent(s.code)}`}
                  className="inline-flex items-baseline gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs hover:border-primary/50 hover:bg-muted/30 transition-colors"
                  title={s.title}
                >
                  <span className="font-mono font-semibold">{s.code}</span>
                  <span className="text-muted-foreground truncate max-w-[24ch]">
                    {s.title}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* FAQ */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">
          Frequently asked questions
        </h2>
        <dl className="divide-y divide-border rounded-xl border border-border bg-card">
          {faqItems.map((item) => (
            <div key={item.question} className="px-5 py-4 space-y-1.5">
              <dt className="text-sm font-semibold">{item.question}</dt>
              <dd className="text-sm text-muted-foreground">{item.answer}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* CTAs */}
      <section className="grid sm:grid-cols-2 gap-4">
        <Link
          href="/classify"
          className="rounded-xl border border-border bg-card p-5 hover:border-primary/50 transition-colors group"
        >
          <h3 className="text-sm font-semibold flex items-center gap-2">
            Classify my business
            <ArrowRight className="size-3.5 group-hover:translate-x-0.5 transition-transform" />
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            Describe your business in plain English and get matching codes across {system.name} and other major systems.
          </p>
        </Link>
        <Link
          href={`/system/${system.id}/node/${encodeURIComponent(node.code)}`}
          className="rounded-xl border border-border bg-card p-5 hover:border-primary/50 transition-colors group"
        >
          <h3 className="text-sm font-semibold flex items-center gap-2">
            Interactive browser
            <ArrowRight className="size-3.5 group-hover:translate-x-0.5 transition-transform" />
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            Open {node.code} in the full interactive explorer with tree view, search, and drill-downs.
          </p>
        </Link>
      </section>

      {/* Source */}
      {(system.authority || system.url) && (
        <footer className="text-xs text-muted-foreground border-t border-border pt-4 flex flex-wrap items-center gap-3">
          {system.authority && <span>Source: {system.authority}</span>}
          {system.url && (
            <a
              href={system.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 hover:text-foreground"
            >
              {system.full_name ?? system.name} official <ExternalLink className="size-3" />
            </a>
          )}
          {system.version && <span>Version: {system.version}</span>}
        </footer>
      )}
    </article>
  )
}

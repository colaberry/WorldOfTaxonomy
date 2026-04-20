import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ArrowRight, ExternalLink } from 'lucide-react'
import { serverGetSystem, serverGetSystems } from '@/lib/server-api'
import { getSystemColor } from '@/lib/colors'
import { MAJOR_SYSTEMS } from '../constants'

interface Props {
  params: Promise<{ system: string }>
}

export const revalidate = 3600

export function generateStaticParams() {
  return MAJOR_SYSTEMS.map((system) => ({ system }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { system } = await params
  try {
    const detail = await serverGetSystem(system)
    const canonical = `https://worldoftaxonomy.com/codes/${system}`
    return {
      title: `${detail.name} Codes - Sectors, Definitions, Crosswalks | WorldOfTaxonomy`,
      description: `Browse all ${detail.node_count.toLocaleString()} codes in ${detail.full_name ?? detail.name}. Every sector, with full definitions and cross-system mappings.`,
      openGraph: {
        title: `${detail.name} Classification Codes`,
        description: `${detail.full_name ?? detail.name} - ${detail.node_count.toLocaleString()} codes across ${detail.region ?? 'Global'}.`,
        url: canonical,
        type: 'website',
      },
      alternates: { canonical },
    }
  } catch {
    return { title: 'Classification System - WorldOfTaxonomy' }
  }
}

export default async function SystemCodeIndexPage({ params }: Props) {
  const { system } = await params

  let detail, allSystems
  try {
    ;[detail, allSystems] = await Promise.all([
      serverGetSystem(system),
      serverGetSystems(),
    ])
  } catch {
    notFound()
  }

  const color = getSystemColor(system)

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10">
      {/* Breadcrumb */}
      <nav className="text-xs text-muted-foreground" aria-label="Breadcrumb">
        <ol className="flex flex-wrap items-center gap-1.5">
          <li><Link href="/" className="hover:text-foreground">Home</Link></li>
          <li aria-hidden="true">/</li>
          <li><Link href="/codes" className="hover:text-foreground">Codes</Link></li>
          <li aria-hidden="true">/</li>
          <li className="text-foreground font-medium">{detail.name}</li>
        </ol>
      </nav>

      {/* Header */}
      <header className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: color }} />
          <span className="text-xs uppercase tracking-wide text-muted-foreground">
            {detail.region ?? 'Global'}
            {detail.authority ? ` - ${detail.authority}` : ''}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">{detail.full_name ?? detail.name}</h1>
        <p className="text-lg text-muted-foreground max-w-3xl">
          {detail.node_count.toLocaleString()} codes across {detail.roots.length}{' '}
          top-level {detail.roots.length === 1 ? 'section' : 'sections'}. Click any sector below to see its full definition, subcategories, and crosswalks to other classification systems.
        </p>
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground pt-1">
          {detail.version && <span>Version: {detail.version}</span>}
          {detail.source_date && <span>Source date: {detail.source_date}</span>}
          {detail.url && (
            <a
              href={detail.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 hover:text-foreground"
            >
              Official source <ExternalLink className="size-3" />
            </a>
          )}
        </div>
      </header>

      {/* Sectors grid */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold">
          Top-level {detail.roots.length === 1 ? 'section' : 'sections'}
        </h2>
        <ul className="grid sm:grid-cols-2 gap-3">
          {detail.roots.map((root) => (
            <li key={root.code}>
              <Link
                href={`/codes/${system}/${encodeURIComponent(root.code)}`}
                className="block rounded-xl border border-border bg-card p-4 hover:border-primary/50 hover:bg-muted/30 transition-colors group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-sm font-semibold text-primary">{root.code}</span>
                      <span className="text-sm font-medium">{root.title}</span>
                    </div>
                    {root.description && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-3">
                        {root.description}
                      </p>
                    )}
                  </div>
                  <ArrowRight className="size-4 text-muted-foreground group-hover:text-primary mt-1 shrink-0" />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* Cross-links */}
      <section className="rounded-xl border border-border bg-card p-5 space-y-2">
        <h2 className="text-sm font-semibold">Compare with other systems</h2>
        <p className="text-xs text-muted-foreground">
          Browse the same sectors in other major classification systems.
        </p>
        <div className="flex flex-wrap gap-2 pt-2">
          {MAJOR_SYSTEMS.filter((id) => id !== system).map((id) => {
            const s = allSystems.find((x) => x.id === id)
            return (
              <Link
                key={id}
                href={`/codes/${id}`}
                className="text-xs rounded-full border border-border bg-background px-3 py-1 hover:bg-muted transition-colors"
              >
                {s?.name ?? id}
              </Link>
            )
          })}
        </div>
      </section>
    </div>
  )
}

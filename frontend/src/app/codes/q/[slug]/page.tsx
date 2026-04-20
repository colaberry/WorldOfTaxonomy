import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ArrowRight, Sparkles } from 'lucide-react'
import { serverSearchFallback, serverGetSystems } from '@/lib/server-api'
import type { ClassificationNode, ClassificationSystem } from '@/lib/types'
import { getSystemColor } from '@/lib/colors'
import { MAJOR_SYSTEMS } from '../../constants'
import { QUERIES, getQuery } from '../queries'

interface Props {
  params: Promise<{ slug: string }>
}

export const revalidate = 86400

interface SystemResults {
  system: ClassificationSystem
  results: ClassificationNode[]
}

export function generateStaticParams() {
  return QUERIES.map((q) => ({ slug: q.slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const q = getQuery(slug)
  if (!q) return { title: 'Business Classification - WorldOfTaxonomy' }
  const canonical = `https://worldoftaxonomy.com/codes/q/${slug}`
  const title = `NAICS, ISIC, SIC, NACE codes for a ${q.query} | WorldOfTaxonomy`
  const description = `Industry and occupation codes that apply to a ${q.query}. ${q.hint}. Cross-mapped across NAICS, ISIC, SIC, NACE, SOC, and HS classifications.`
  return {
    title,
    description,
    openGraph: {
      title: `Classification codes for a ${q.query}`,
      description,
      url: canonical,
      type: 'article',
    },
    alternates: { canonical },
    keywords: [
      `${q.query} NAICS code`,
      `${q.query} industry code`,
      `${q.query} classification`,
      `NAICS code for ${q.query}`,
      `ISIC code for ${q.query}`,
    ],
  }
}

function buildFaq(
  q: { query: string; hint: string },
  results: SystemResults[],
): Array<{ question: string; answer: string }> {
  const items: Array<{ question: string; answer: string }> = []
  for (const r of results) {
    if (r.results.length === 0) continue
    const top = r.results[0]
    items.push({
      question: `What ${r.system.name} code applies to a ${q.query}?`,
      answer: `The closest ${r.system.name} match for a ${q.query} is ${top.code} ${top.title}.${r.results.length > 1 ? ` Other candidates include ${r.results.slice(1, 3).map((n) => `${n.code} ${n.title}`).join(' and ')}.` : ''}`,
    })
  }
  items.push({
    question: `How accurate are these classifications?`,
    answer: `These are the top full-text matches from each system's official code titles and descriptions. For filings that require a legally precise classification (taxes, regulatory registrations, customs), confirm with the relevant authority or a qualified professional. Use the classifier for faster iteration and the code detail pages for definitions.`,
  })
  return items
}

function buildJsonLd(
  q: { slug: string; query: string; hint: string },
  faq: Array<{ question: string; answer: string }>,
  url: string,
): object[] {
  const breadcrumb = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://worldoftaxonomy.com' },
      { '@type': 'ListItem', position: 2, name: 'Codes', item: 'https://worldoftaxonomy.com/codes' },
      { '@type': 'ListItem', position: 3, name: 'Business types', item: 'https://worldoftaxonomy.com/codes/q' },
      { '@type': 'ListItem', position: 4, name: q.query, item: url },
    ],
  }
  const faqPage = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faq.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: { '@type': 'Answer', text: item.answer },
    })),
  }
  return [breadcrumb, faqPage]
}

export default async function QueryPage({ params }: Props) {
  const { slug } = await params
  const q = getQuery(slug)
  if (!q) notFound()

  const [allSystems, ...perSystemResults] = await Promise.all([
    serverGetSystems().catch(() => [] as ClassificationSystem[]),
    ...MAJOR_SYSTEMS.map((id) =>
      serverSearchFallback(q.query, id, q.keywords, 3).catch(() => [] as ClassificationNode[]),
    ),
  ])

  const systemResults: SystemResults[] = MAJOR_SYSTEMS.map((id, i) => {
    const system = allSystems.find((s) => s.id === id)
    if (!system) return null
    return { system, results: perSystemResults[i] as ClassificationNode[] }
  }).filter((x): x is SystemResults => x !== null)

  const withMatches = systemResults.filter((r) => r.results.length > 0)
  const hasAny = withMatches.length > 0

  const url = `https://worldoftaxonomy.com/codes/q/${q.slug}`
  const faq = buildFaq(q, systemResults)
  const jsonLd = buildJsonLd(q, faq, url)

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
          <li><Link href="/codes/q" className="hover:text-foreground">By business type</Link></li>
          <li aria-hidden="true">/</li>
          <li className="text-foreground font-medium capitalize">{q.query}</li>
        </ol>
      </nav>

      {/* Header */}
      <header className="space-y-4">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Classification codes for a <span className="capitalize">{q.query}</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-3xl">
          {q.hint}. Below are the closest matches in NAICS, ISIC, SIC, NACE, SOC,
          and other major classification systems. Click any code for its full
          definition, subcategories, and crosswalks across every system.
        </p>
      </header>

      {!hasAny && (
        <div className="rounded-xl border border-border bg-card p-6 text-sm">
          <p className="font-medium">No strong matches on these major systems.</p>
          <p className="text-muted-foreground mt-2">
            Try the{' '}
            <Link href="/classify" className="text-primary underline">free classifier</Link>
            {' '}with a more specific description, or browse{' '}
            <Link href="/codes" className="text-primary underline">all classification systems</Link>.
          </p>
        </div>
      )}

      {/* Per-system results */}
      {hasAny && (
        <section className="grid gap-4">
          {systemResults.map(({ system, results }) => {
            const color = getSystemColor(system.id)
            return (
              <div
                key={system.id}
                className="rounded-xl border border-border bg-card overflow-hidden"
              >
                <div
                  className="px-5 py-3 border-b border-border flex items-center justify-between"
                  style={{ backgroundColor: `${color}12` }}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-block size-2.5 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="font-semibold text-sm">{system.name}</span>
                    <span className="text-xs text-muted-foreground">
                      · {system.region ?? 'Global'}
                    </span>
                  </div>
                  <Link
                    href={`/codes/${system.id}`}
                    className="text-xs text-muted-foreground hover:text-foreground hover:underline"
                  >
                    Browse all →
                  </Link>
                </div>
                {results.length === 0 ? (
                  <div className="px-5 py-4 text-sm text-muted-foreground">
                    No strong match in {system.name}.
                  </div>
                ) : (
                  <ul className="divide-y divide-border">
                    {results.map((n, i) => (
                      <li key={`${system.id}-${n.code}`}>
                        <Link
                          href={`/codes/${system.id}/${encodeURIComponent(n.code)}`}
                          className="flex items-start justify-between gap-4 px-5 py-3 hover:bg-muted/50 transition-colors group"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-baseline gap-2">
                              <span className="font-mono text-sm font-semibold">{n.code}</span>
                              {i === 0 && (
                                <span className="text-[10px] uppercase tracking-wide font-semibold text-primary bg-primary/10 rounded px-1.5 py-0.5">
                                  Top match
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-foreground/90 mt-0.5 group-hover:text-primary transition-colors">
                              {n.title}
                            </div>
                            {n.description && (
                              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                {n.description}
                              </p>
                            )}
                          </div>
                          <ArrowRight className="size-4 text-muted-foreground group-hover:text-primary mt-1 shrink-0" />
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )
          })}
        </section>
      )}

      {/* FAQ */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Frequently asked questions</h2>
        <dl className="divide-y divide-border rounded-xl border border-border bg-card">
          {faq.map((item) => (
            <div key={item.question} className="px-5 py-4 space-y-1.5">
              <dt className="text-sm font-semibold">{item.question}</dt>
              <dd className="text-sm text-muted-foreground">{item.answer}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Upgrade CTA */}
      <section className="rounded-xl border border-primary/30 bg-primary/5 p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <Sparkles className="size-5 text-primary mt-0.5" />
          <div className="flex-1 space-y-2">
            <h3 className="font-semibold">Need a classification for a different business?</h3>
            <p className="text-sm text-muted-foreground">
              Describe any business in plain English and we&apos;ll return the matching codes.
            </p>
            <Link
              href="/classify"
              className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
            >
              Try the classifier <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </section>
    </article>
  )
}

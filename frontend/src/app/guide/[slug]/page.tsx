import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { getWikiMeta, getWikiContent, renderWikiHtml, getWikiSlugs } from '@/lib/wiki'
import { WikiArticle } from '@/components/wiki/WikiArticle'

interface Props {
  params: Promise<{ slug: string }>
}

export function generateStaticParams() {
  return getWikiSlugs().map((slug) => ({ slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const meta = getWikiMeta()
  const entry = meta.find((e) => e.slug === slug)

  if (!entry) {
    return { title: 'Guide Not Found - World Of Taxonomy' }
  }

  return {
    title: `${entry.title} - World Of Taxonomy`,
    description: entry.description,
    openGraph: {
      title: entry.title,
      description: entry.description,
      url: `https://worldoftaxonomy.com/guide/${slug}`,
      type: 'article',
    },
    alternates: { canonical: `https://worldoftaxonomy.com/guide/${slug}` },
  }
}

export default async function GuideSlugPage({ params }: Props) {
  const { slug } = await params
  const meta = getWikiMeta()
  const entry = meta.find((e) => e.slug === slug)

  if (!entry) notFound()

  const markdown = getWikiContent(slug)
  if (!markdown) notFound()

  const html = await renderWikiHtml(markdown)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: entry.title,
    description: entry.description,
    url: `https://worldoftaxonomy.com/guide/${slug}`,
    publisher: {
      '@type': 'Organization',
      name: 'World Of Taxonomy',
      url: 'https://worldoftaxonomy.com',
    },
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <WikiArticle title={entry.title} html={html} slug={slug} />
    </>
  )
}

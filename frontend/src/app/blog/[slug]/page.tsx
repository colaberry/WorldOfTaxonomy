import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { getBlogMeta, getBlogContent, renderBlogHtml, getBlogSlugs } from '@/lib/blog'
import { BlogArticle } from '@/components/blog/BlogArticle'

interface Props {
  params: Promise<{ slug: string }>
}

export function generateStaticParams() {
  return getBlogSlugs().map((slug) => ({ slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params
  const meta = getBlogMeta()
  const entry = meta.find((e) => e.slug === slug)

  if (!entry) {
    return { title: 'Post Not Found - World Of Taxonomy' }
  }

  return {
    title: `${entry.title} - World Of Taxonomy`,
    description: entry.description,
    openGraph: {
      title: entry.title,
      description: entry.description,
      url: `https://worldoftaxonomy.com/blog/${slug}`,
      type: 'article',
      publishedTime: entry.date,
      authors: [entry.author],
      tags: entry.tags,
    },
    alternates: { canonical: `https://worldoftaxonomy.com/blog/${slug}` },
  }
}

export default async function BlogSlugPage({ params }: Props) {
  const { slug } = await params
  const meta = getBlogMeta()
  const entry = meta.find((e) => e.slug === slug)

  if (!entry) notFound()

  const markdown = getBlogContent(slug)
  if (!markdown) notFound()

  const html = await renderBlogHtml(markdown)

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: entry.title,
    description: entry.description,
    datePublished: entry.date,
    author: {
      '@type': 'Person',
      name: entry.author,
    },
    url: `https://worldoftaxonomy.com/blog/${slug}`,
    publisher: {
      '@type': 'Organization',
      name: 'World Of Taxonomy',
      url: 'https://worldoftaxonomy.com',
    },
    keywords: entry.tags,
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <BlogArticle
        title={entry.title}
        html={html}
        slug={slug}
        date={entry.date}
        author={entry.author}
        tags={entry.tags}
      />
    </>
  )
}

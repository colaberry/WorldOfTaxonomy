import type { Metadata } from 'next'
import Link from 'next/link'
import { getBlogMeta } from '@/lib/blog'
import { Newspaper, Rss } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Blog - World Of Taxonomy',
  description:
    'News, insights, and updates from the World Of Taxonomy team on classification systems, crosswalks, and the global taxonomy knowledge graph.',
  openGraph: {
    title: 'Blog - World Of Taxonomy',
    description: 'News and insights on classification systems and crosswalks.',
    url: 'https://worldoftaxonomy.com/blog',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/blog' },
}

export default function BlogPage() {
  const posts = getBlogMeta()

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <Newspaper className="h-7 w-7 text-primary" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Blog</h1>
            <p className="text-muted-foreground text-sm mt-0.5">
              News, insights, and deep dives on classification systems and the global taxonomy knowledge graph.
            </p>
          </div>
        </div>
        <a
          href="/feed.xml"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors"
          title="RSS Feed"
        >
          <Rss className="h-4 w-4" />
          <span className="hidden sm:inline">RSS</span>
        </a>
      </div>

      <div className="grid gap-4">
        {posts.map((post) => (
          <Link
            key={post.slug}
            href={`/blog/${post.slug}`}
            className="block p-5 rounded-lg border border-border/50 bg-card hover:bg-secondary/30 transition-colors group"
          >
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
              <time dateTime={post.date}>
                {new Date(post.date + 'T00:00:00').toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </time>
              <span className="text-border">|</span>
              <span>{post.author}</span>
            </div>
            <h2 className="text-lg font-semibold group-hover:text-primary transition-colors">
              {post.title}
            </h2>
            <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">{post.description}</p>
            {post.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {post.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 text-xs rounded-full bg-secondary text-muted-foreground"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}

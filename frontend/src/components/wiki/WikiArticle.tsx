'use client'

import { useEffect, useRef } from 'react'
import Link from 'next/link'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { MermaidBlock } from './MermaidBlock'

interface WikiArticleProps {
  title: string
  html: string
  slug: string
}

export function WikiArticle({ title, html, slug }: WikiArticleProps) {
  const contentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!contentRef.current) return

    // Find all <pre><code class="language-mermaid"> blocks and render them
    const codeBlocks = contentRef.current.querySelectorAll('code.language-mermaid')
    codeBlocks.forEach((block) => {
      const pre = block.parentElement
      if (!pre || pre.tagName !== 'PRE') return

      const mermaidCode = block.textContent || ''
      const container = document.createElement('div')
      container.className = 'mermaid-container my-6'
      container.setAttribute('data-mermaid', mermaidCode)
      pre.replaceWith(container)
    })
  }, [html])

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/guide"
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          All Guides
        </Link>
      </div>

      <h1 className="text-2xl font-bold tracking-tight mb-8">{title}</h1>

      <article
        ref={contentRef}
        className="prose prose-sm dark:prose-invert max-w-none
          prose-headings:font-semibold prose-headings:tracking-tight
          prose-h2:text-xl prose-h2:mt-10 prose-h2:mb-4
          prose-h3:text-lg prose-h3:mt-8 prose-h3:mb-3
          prose-p:text-muted-foreground prose-p:leading-relaxed
          prose-a:text-primary prose-a:no-underline hover:prose-a:underline
          prose-code:text-sm prose-code:bg-secondary/50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
          prose-pre:bg-secondary/30 prose-pre:border prose-pre:border-border/50
          prose-table:text-sm
          prose-th:text-left prose-th:font-semibold prose-th:border-b prose-th:border-border
          prose-td:border-b prose-td:border-border/30 prose-td:py-2
          prose-li:text-muted-foreground"
        dangerouslySetInnerHTML={{ __html: html }}
      />

      <MermaidBlock />

      <div className="mt-12 pt-6 border-t border-border/50 flex items-center justify-between">
        <Link
          href="/guide"
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Back to all guides
        </Link>
        <a
          href={`https://github.com/ramdhanyk/World Of Taxonomy/edit/main/wiki/${slug}.md`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Edit on GitHub
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>
    </div>
  )
}

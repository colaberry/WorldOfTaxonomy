'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { search, getSystems } from '@/lib/api'
import Link from 'next/link'
import { Search } from 'lucide-react'

export default function ExplorePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ExploreContent />
    </Suspense>
  )
}

function ExploreContent() {
  const searchParams = useSearchParams()
  const initialQuery = searchParams.get('q') || ''

  const [query, setQuery] = useState(initialQuery)
  const [selectedSystem, setSelectedSystem] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState(initialQuery)

  // Auto-search when arriving with ?q= param
  useEffect(() => {
    const q = searchParams.get('q')
    if (q) {
      setQuery(q)
      setSearchTerm(q)
    }
  }, [searchParams])

  const { data: systems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
  })

  const { data: results, isLoading } = useQuery({
    queryKey: ['search', searchTerm, selectedSystem],
    queryFn: () => search(searchTerm, selectedSystem || undefined, 50),
    enabled: searchTerm.length >= 2,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchTerm(query)
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Explore Classifications</h1>
        <p className="text-sm text-muted-foreground">
          Search across all industry classification systems
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for industries, e.g. 'hospital', 'mining', 'software'..."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-card border border-border/50 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
          />
        </div>
        <select
          value={selectedSystem}
          onChange={(e) => setSelectedSystem(e.target.value)}
          className="px-3 py-2.5 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <option value="">All Systems</option>
          {systems?.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <button
          type="submit"
          className="px-6 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Search
        </button>
      </form>

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {results && results.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground mb-3">
            {results.length} result{results.length !== 1 ? 's' : ''} for &ldquo;{searchTerm}&rdquo;
          </p>
          {results.map((node, i) => (
            <Link
              key={`${node.system_id}-${node.code}-${i}`}
              href={`/system/${node.system_id}/node/${node.code}`}
              className="block p-3 rounded-lg hover:bg-card/80 border border-transparent hover:border-border/50 transition-colors"
            >
              <div className="flex items-baseline gap-2">
                <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-secondary text-muted-foreground shrink-0">
                  {node.system_id}
                </span>
                <span className="text-xs font-mono text-muted-foreground">{node.code}</span>
                <span className="text-sm">{node.title}</span>
              </div>
              {node.description && (
                <p className="text-xs text-muted-foreground mt-1 ml-[calc(0.375rem+0.75rem+0.5rem)] line-clamp-2">
                  {node.description}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}

      {results && results.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-sm">No results found for &ldquo;{searchTerm}&rdquo;</p>
        </div>
      )}

      {!searchTerm && (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-sm">Enter a search term to explore industry classifications</p>
        </div>
      )}
    </div>
  )
}

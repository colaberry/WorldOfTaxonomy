'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { search, getSystems } from '@/lib/api'
import { getCategoryForSystem } from '@/lib/categories'
import Link from 'next/link'
import { Search, LayoutList, Layers } from 'lucide-react'

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
  const [grouped, setGrouped] = useState(false)

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
    queryFn: () => search(searchTerm, selectedSystem || undefined, 100),
    enabled: searchTerm.length >= 2,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchTerm(query)
  }

  // Group results by system
  const groupedResults: Record<string, typeof results> = {}
  if (results && grouped) {
    for (const node of results) {
      if (!groupedResults[node.system_id]) groupedResults[node.system_id] = []
      groupedResults[node.system_id]!.push(node)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Explore Classifications</h1>
        <p className="text-sm text-muted-foreground">
          Search across all 82 classification systems and 532,651 codes
        </p>
      </div>

      {/* Search form */}
      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search: hospital, mining, software, A01B, 3412..."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-card border border-border/50 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
          />
        </div>
        <select
          value={selectedSystem}
          onChange={(e) => setSelectedSystem(e.target.value)}
          className="px-3 py-2.5 rounded-lg bg-card border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 sm:w-44"
        >
          <option value="">All Systems</option>
          {systems
            ?.slice()
            .sort((a, b) => a.name.localeCompare(b.name))
            .map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
        </select>
        <button
          type="submit"
          className="px-5 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Search
        </button>
      </form>

      {/* Results header with toggle */}
      {results && results.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">{results.length}</span> result{results.length !== 1 ? 's' : ''} for &ldquo;{searchTerm}&rdquo;
            {selectedSystem && (
              <span className="ml-1">in <span className="font-medium">{selectedSystem}</span></span>
            )}
          </p>
          <div className="flex items-center gap-1 p-0.5 rounded-md bg-secondary">
            <button
              onClick={() => setGrouped(false)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                !grouped ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
              }`}
            >
              <LayoutList className="h-3 w-3" />
              Flat
            </button>
            <button
              onClick={() => setGrouped(true)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                grouped ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground'
              }`}
            >
              <Layers className="h-3 w-3" />
              Grouped
            </button>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Flat results */}
      {results && results.length > 0 && !grouped && (
        <div className="space-y-0.5">
          {results.map((node, i) => {
            const cat = getCategoryForSystem(node.system_id)
            return (
              <Link
                key={`${node.system_id}-${node.code}-${i}`}
                href={`/system/${node.system_id}/node/${encodeURIComponent(node.code)}`}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-card border border-transparent hover:border-border/50 transition-colors group"
              >
                <div
                  className="w-1 h-full min-h-[1.5rem] rounded-full shrink-0 mt-0.5"
                  style={{ backgroundColor: cat.accent }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded shrink-0"
                      style={{ backgroundColor: `${cat.accent}18`, color: cat.accent }}
                    >
                      {node.system_id}
                    </span>
                    <span className="text-xs font-mono text-muted-foreground">{node.code}</span>
                    <span className="text-sm font-medium group-hover:text-primary transition-colors truncate">
                      {node.title}
                    </span>
                  </div>
                  {node.description && (
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                      {node.description}
                    </p>
                  )}
                </div>
              </Link>
            )
          })}
        </div>
      )}

      {/* Grouped results */}
      {results && results.length > 0 && grouped && (
        <div className="space-y-6">
          {Object.entries(groupedResults)
            .sort(([, a], [, b]) => (b?.length ?? 0) - (a?.length ?? 0))
            .map(([systemId, nodes]) => {
              const cat = getCategoryForSystem(systemId)
              const sys = systems?.find((s) => s.id === systemId)
              return (
                <div key={systemId}>
                  <div
                    className="flex items-center gap-2 mb-2 pb-2 border-b border-border/30"
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: cat.accent }}
                    />
                    <span className="text-sm font-semibold">{sys?.name ?? systemId}</span>
                    <span className="text-xs text-muted-foreground">
                      {nodes?.length} match{(nodes?.length ?? 0) !== 1 ? 'es' : ''}
                    </span>
                    <Link
                      href={`/system/${systemId}`}
                      className="ml-auto text-xs text-muted-foreground hover:text-primary transition-colors"
                    >
                      Browse system
                    </Link>
                  </div>
                  <div className="space-y-0.5 pl-4">
                    {nodes?.map((node, i) => (
                      <Link
                        key={`${node.code}-${i}`}
                        href={`/system/${systemId}/node/${encodeURIComponent(node.code)}`}
                        className="flex items-baseline gap-2 py-1.5 px-2 rounded hover:bg-card transition-colors group"
                      >
                        <span className="text-xs font-mono text-muted-foreground w-20 shrink-0">
                          {node.code}
                        </span>
                        <span className="text-sm group-hover:text-primary transition-colors">
                          {node.title}
                        </span>
                      </Link>
                    ))}
                  </div>
                </div>
              )
            })}
        </div>
      )}

      {results && results.length === 0 && (
        <div className="text-center py-16 text-muted-foreground space-y-2">
          <Search className="h-8 w-8 mx-auto opacity-30" />
          <p className="text-sm">No results for &ldquo;{searchTerm}&rdquo;</p>
          <p className="text-xs">Try a broader term or select a different system</p>
        </div>
      )}

      {!searchTerm && (
        <div className="text-center py-16 space-y-3 text-muted-foreground">
          <Search className="h-8 w-8 mx-auto opacity-30" />
          <p className="text-sm">Enter a keyword, code, or phrase to search</p>
          <div className="flex flex-wrap gap-2 justify-center text-xs">
            {['hospital', 'mining', 'software development', 'A01B', '3412', 'physician'].map((term) => (
              <button
                key={term}
                onClick={() => { setQuery(term); setSearchTerm(term) }}
                className="px-3 py-1.5 rounded-full bg-secondary hover:bg-secondary/70 transition-colors font-mono"
              >
                {term}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

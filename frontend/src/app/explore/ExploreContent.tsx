'use client'

import { Suspense, useState, useEffect, useCallback, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { search, getSystems, getStats } from '@/lib/api'
import {
  SYSTEM_CATEGORIES,
  groupSystemsByCategory,
  getCategoryForSystem,
  DOMAIN_SECTORS,
  getDomainSector,
  LIFE_SCIENCES_SECTORS,
  getLifeSciencesSector,
} from '@/lib/categories'
import { getSystemColor } from '@/lib/colors'
import { useCountryFilter } from '@/lib/useCountryFilter'
import { CountryFilterBar } from '@/components/CountryFilterBar'
import Link from 'next/link'
import {
  Search, X, ChevronDown, ChevronRight, Leaf,
  Globe, GitBranch, Network, ArrowUpRight,
} from 'lucide-react'
import type {
  ClassificationNodeWithContext, ClassificationSystem, CrosswalkStat,
} from '@/lib/types'

const EXAMPLE_QUERIES = ['hospital', 'mining', 'software', 'physician', 'logistics', 'agriculture']
const INITIAL_VISIBLE = 5

interface ExploreContentProps {
  initialSystems: ClassificationSystem[] | null
  initialStats: CrosswalkStat[] | null
}

export function ExploreWrapper(props: ExploreContentProps) {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ExploreInner {...props} />
    </Suspense>
  )
}

function ExploreInner({ initialSystems, initialStats }: ExploreContentProps) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const initialQuery = searchParams.get('q') || ''
  const activeCat = searchParams.get('cat') ?? ''
  const activeSectorId = searchParams.get('sector') ?? ''

  const [query, setQuery] = useState(initialQuery)
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery)
  const [selectedSystem, setSelectedSystem] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [expanded, setExpanded] = useState<Record<string, number>>({})
  const [openCats, setOpenCats] = useState<Set<string>>(new Set())

  useEffect(() => {
    const q = searchParams.get('q')
    if (q) { setQuery(q); setDebouncedQuery(q) }
  }, [searchParams])

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 300)
    return () => clearTimeout(t)
  }, [query])

  useEffect(() => {
    setCategoryFilter('all')
    setExpanded({})
  }, [debouncedQuery, selectedSystem])

  const { data: systemsAll } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
    initialData: initialSystems ?? undefined,
    staleTime: 0,
  })

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    initialData: initialStats ?? undefined,
    staleTime: 0,
  })

  const {
    country,
    setCountry,
    countries,
    countriesError,
    countrySystemIds,
    countrySystemsError,
    selectedCountry,
  } = useCountryFilter()

  const systems = useMemo(() => {
    if (!systemsAll) return systemsAll
    if (!country || !countrySystemIds) return systemsAll
    return systemsAll.filter((s) => countrySystemIds.has(s.id))
  }, [systemsAll, country, countrySystemIds])

  useEffect(() => {
    if (country && selectedSystem && countrySystemIds && !countrySystemIds.has(selectedSystem)) {
      setSelectedSystem('')
    }
  }, [country, countrySystemIds, selectedSystem])

  const { data: results, isLoading, isFetching } = useQuery({
    queryKey: ['search', debouncedQuery, selectedSystem, country],
    queryFn: async () => {
      const raw = await search(debouncedQuery, selectedSystem || undefined, 200, true)
      if (country && countrySystemIds) {
        return raw.filter((r) => countrySystemIds.has(r.system_id))
      }
      return raw
    },
    enabled: debouncedQuery.length >= 2 && (!country || countrySystemIds !== null),
    staleTime: 2 * 60 * 1000,
  })

  const isSearching = debouncedQuery.length >= 2

  const handleClear = () => {
    setQuery('')
    setDebouncedQuery('')
    setSelectedSystem('')
    setCategoryFilter('all')
    setExpanded({})
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Explore Classifications</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {selectedCountry ? (
            <>
              Scoped to <span className="font-medium text-foreground">{selectedCountry.title}</span>
              {' '}&middot; {systems?.length ?? '...'} applicable systems
            </>
          ) : isSearching
            ? `Searching across all ${systems?.length ?? '...'} classification systems`
            : `All ${systems?.length ?? '...'} classification systems across ${SYSTEM_CATEGORIES.length} categories`}
        </p>
      </div>

      {/* Country filter */}
      <CountryFilterBar
        country={country}
        countries={countries}
        countriesError={countriesError ?? countrySystemsError}
        onChange={setCountry}
      />

      {/* Search bar - always visible */}
      <div className="max-w-4xl">
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search codes, titles, descriptions..."
              className="w-full pl-10 pr-9 py-2.5 rounded-lg bg-card border border-border/50 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
            />
            {query && (
              <button
                onClick={handleClear}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
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
        </div>
      </div>

      {isSearching ? (
        <SearchView
          results={results}
          systems={systems}
          debouncedQuery={debouncedQuery}
          isLoading={isLoading}
          isFetching={isFetching}
          categoryFilter={categoryFilter}
          setCategoryFilter={setCategoryFilter}
          expanded={expanded}
          setExpanded={setExpanded}
        />
      ) : (
        <BrowseView
          systems={systems}
          stats={stats}
          activeCat={activeCat}
          activeSectorId={activeSectorId}
          router={router}
          setQuery={setQuery}
          setDebouncedQuery={setDebouncedQuery}
          openCats={openCats}
          setOpenCats={setOpenCats}
        />
      )}
    </div>
  )
}

// ─── Search view ─────────────────────────────────────────────────────────────

function SearchView({
  results,
  systems,
  debouncedQuery,
  isLoading,
  isFetching,
  categoryFilter,
  setCategoryFilter,
  expanded,
  setExpanded,
}: {
  results: ClassificationNodeWithContext[] | undefined
  systems: ClassificationSystem[] | undefined
  debouncedQuery: string
  isLoading: boolean
  isFetching: boolean
  categoryFilter: string
  setCategoryFilter: (v: string) => void
  expanded: Record<string, number>
  setExpanded: React.Dispatch<React.SetStateAction<Record<string, number>>>
}) {
  const categoryBuckets = (() => {
    if (!results) return []
    const seen = new Map<string, ClassificationNodeWithContext[]>()
    for (const node of results) {
      const cat = getCategoryForSystem(node.system_id)
      if (!seen.has(cat.id)) seen.set(cat.id, [])
      seen.get(cat.id)!.push(node)
    }
    const buckets: { catId: string; nodes: ClassificationNodeWithContext[] }[] = []
    for (const cat of SYSTEM_CATEGORIES) {
      if (seen.has(cat.id)) buckets.push({ catId: cat.id, nodes: seen.get(cat.id)! })
    }
    return buckets
  })()

  const activeBuckets =
    categoryFilter === 'all'
      ? categoryBuckets
      : categoryBuckets.filter((b) => b.catId === categoryFilter)

  const totalCount = results?.length ?? 0
  const handleExpand = useCallback((catId: string, total: number) => {
    setExpanded((prev) => ({ ...prev, [catId]: total }))
  }, [setExpanded])

  const isEmpty = debouncedQuery.length >= 2 && !isLoading && results?.length === 0

  return (
    <div className="max-w-4xl space-y-6">

      {/* Category filter pills */}
      {categoryBuckets.length > 1 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => setCategoryFilter('all')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              categoryFilter === 'all'
                ? 'bg-foreground text-background'
                : 'bg-secondary text-muted-foreground hover:text-foreground'
            }`}
          >
            All
            <span className="font-mono opacity-70">{totalCount}</span>
          </button>
          {categoryBuckets.map(({ catId, nodes }) => {
            const cat = SYSTEM_CATEGORIES.find((c) => c.id === catId)!
            return (
              <button
                key={catId}
                onClick={() => setCategoryFilter(catId === categoryFilter ? 'all' : catId)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  categoryFilter === catId
                    ? 'text-white'
                    : 'bg-secondary text-muted-foreground hover:text-foreground'
                }`}
                style={categoryFilter === catId ? { backgroundColor: cat.accent } : {}}
              >
                {cat.label}
                <span className="font-mono opacity-70">{nodes.length}</span>
              </button>
            )
          })}
        </div>
      )}

      {(isLoading || isFetching) && debouncedQuery.length >= 2 && (
        <div className="flex justify-center py-8">
          <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!isLoading && !isFetching && activeBuckets.length > 0 && (
        <div className="space-y-8">
          {activeBuckets.map(({ catId, nodes }) => {
            const cat = SYSTEM_CATEGORIES.find((c) => c.id === catId)!

            if (catId === 'domain' || catId === 'lifesciences') {
              const isDomain = catId === 'domain'
              const sectorDefs = isDomain ? DOMAIN_SECTORS : LIFE_SCIENCES_SECTORS
              const getSector = isDomain
                ? (id: string) => getDomainSector(id)
                : (id: string) => getLifeSciencesSector(id)

              const sectorMap = new Map<string, typeof nodes>()
              for (const node of nodes) {
                const sector = getSector(node.system_id)
                const key = sector?.id ?? '_other'
                if (!sectorMap.has(key)) sectorMap.set(key, [])
                sectorMap.get(key)!.push(node)
              }
              const orderedSectors: Array<{ sectorId: string; sectorNodes: typeof nodes }> = []
              for (const sector of sectorDefs) {
                if (sectorMap.has(sector.id)) {
                  orderedSectors.push({ sectorId: sector.id, sectorNodes: sectorMap.get(sector.id)! })
                }
              }
              if (sectorMap.has('_other')) {
                orderedSectors.push({ sectorId: '_other', sectorNodes: sectorMap.get('_other')! })
              }

              return (
                <section key={catId}>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: cat.accent }} />
                    <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{cat.label}</span>
                    <span className="text-xs text-muted-foreground font-mono">
                      {nodes.length} match{nodes.length !== 1 ? 'es' : ''}
                    </span>
                    <div className="flex-1 h-px bg-border/30" />
                  </div>
                  <div className="space-y-4">
                    {orderedSectors.map(({ sectorId, sectorNodes }) => {
                      const sectorDef = sectorDefs.find((s) => s.id === sectorId)
                      const expandKey = `${catId}_${sectorId}`
                      const visible = expanded[expandKey] ?? INITIAL_VISIBLE
                      const shown = sectorNodes.slice(0, visible)
                      const remaining = sectorNodes.length - shown.length
                      return (
                        <div key={sectorId}>
                          <div className="flex items-center gap-1.5 mb-1.5">
                            <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: sectorDef?.accent ?? cat.accent }} />
                            <span className="text-[11px] font-semibold text-muted-foreground/80">{sectorDef?.label ?? 'Other'}</span>
                            <span className="text-[11px] text-muted-foreground/50 font-mono">{sectorNodes.length}</span>
                          </div>
                          <div className="space-y-0.5 pl-3">
                            {shown.map((node, i) => (
                              <ResultRow
                                key={`${node.system_id}-${node.code}-${i}`}
                                node={node}
                                systems={systems ?? []}
                                query={debouncedQuery}
                              />
                            ))}
                          </div>
                          {remaining > 0 && (
                            <button
                              onClick={() => handleExpand(expandKey, sectorNodes.length)}
                              className="mt-1.5 flex items-center gap-1.5 pl-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
                            >
                              <ChevronDown className="h-3.5 w-3.5" />
                              Show {remaining} more in {sectorDef?.label ?? 'Other'}
                            </button>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </section>
              )
            }

            const visible = expanded[catId] ?? INITIAL_VISIBLE
            const shown = nodes.slice(0, visible)
            const remaining = nodes.length - shown.length

            return (
              <section key={catId}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: cat.accent }} />
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{cat.label}</span>
                  <span className="text-xs text-muted-foreground font-mono">
                    {nodes.length} match{nodes.length !== 1 ? 'es' : ''}
                  </span>
                  <div className="flex-1 h-px bg-border/30" />
                </div>
                <div className="space-y-0.5">
                  {shown.map((node, i) => (
                    <ResultRow
                      key={`${node.system_id}-${node.code}-${i}`}
                      node={node}
                      systems={systems ?? []}
                      query={debouncedQuery}
                    />
                  ))}
                </div>
                {remaining > 0 && (
                  <button
                    onClick={() => handleExpand(catId, nodes.length)}
                    className="mt-2 flex items-center gap-1.5 pl-3 text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <ChevronDown className="h-3.5 w-3.5" />
                    Show {remaining} more in {cat.label}
                  </button>
                )}
              </section>
            )
          })}
        </div>
      )}

      {isEmpty && (
        <div className="text-center py-16 text-muted-foreground space-y-2">
          <Search className="h-8 w-8 mx-auto opacity-30" />
          <p className="text-sm">No results for &ldquo;{debouncedQuery}&rdquo;</p>
          <p className="text-xs">Try a broader term or select a different system</p>
        </div>
      )}
    </div>
  )
}

// ─── Browse view (former Dashboard) ──────────────────────────────────────────

function BrowseView({
  systems,
  stats,
  activeCat,
  activeSectorId,
  router,
  setQuery,
  setDebouncedQuery,
  openCats,
  setOpenCats,
}: {
  systems: ClassificationSystem[] | undefined
  stats: CrosswalkStat[] | undefined
  activeCat: string
  activeSectorId: string
  router: ReturnType<typeof useRouter>
  setQuery: (v: string) => void
  setDebouncedQuery: (v: string) => void
  openCats: Set<string>
  setOpenCats: React.Dispatch<React.SetStateAction<Set<string>>>
}) {
  const totalNodes = systems?.reduce((sum, s) => sum + s.node_count, 0) ?? 0
  const totalEdges = stats?.reduce((sum, s) => sum + s.edge_count, 0) ?? 0
  const grouped = systems ? groupSystemsByCategory(systems) : []
  const maxNodes = systems ? Math.max(...systems.map((s) => s.node_count)) : 1

  const allDomainSystems = grouped.find((g) => g.category.id === 'domain')?.systems ?? []
  const domainSectorsPresent = DOMAIN_SECTORS.filter((sector) =>
    allDomainSystems.some((s) =>
      s.id === 'domain_adv_materials' ? sector.id === 'materials' : s.id.startsWith(sector.prefix)
    )
  )
  const traditionalSectors = domainSectorsPresent.filter((s) => s.group === 'traditional')
  const emergingSectors = domainSectorsPresent.filter((s) => s.group === 'emerging')

  const allLSSystems = grouped.find((g) => g.category.id === 'lifesciences')?.systems ?? []
  const lsSectorsPresent = LIFE_SCIENCES_SECTORS.filter((sector) =>
    allLSSystems.some((s) => getLifeSciencesSector(s.id)?.id === sector.id)
  )

  const activeSectorDef = activeSectorId
    ? (DOMAIN_SECTORS.find((s) => s.id === activeSectorId)
       ?? LIFE_SCIENCES_SECTORS.find((s) => s.id === activeSectorId)
       ?? null)
    : null

  function sectorSystemCount(sectorId: string): number {
    const domainDef = DOMAIN_SECTORS.find((s) => s.id === sectorId)
    if (domainDef) {
      return allDomainSystems.filter((s) =>
        s.id === 'domain_adv_materials' ? domainDef.id === 'materials' : s.id.startsWith(domainDef.prefix)
      ).length
    }
    const lsDef = LIFE_SCIENCES_SECTORS.find((s) => s.id === sectorId)
    if (lsDef) {
      return allLSSystems.filter((s) => getLifeSciencesSector(s.id)?.id === lsDef.id).length
    }
    return 0
  }

  function filterBySector(catSystems: ClassificationSystem[], catId: string) {
    if (!activeSectorId) return catSystems
    if (catId === 'domain') {
      const def = DOMAIN_SECTORS.find((s) => s.id === activeSectorId)
      if (!def) return catSystems
      return catSystems.filter((s) =>
        s.id === 'domain_adv_materials' ? def.id === 'materials' : s.id.startsWith(def.prefix)
      )
    }
    if (catId === 'lifesciences') {
      return catSystems.filter((s) => getLifeSciencesSector(s.id)?.id === activeSectorId)
    }
    return catSystems
  }

  function handleSectorClick(sectorId: string, catId: string) {
    if (sectorId === activeSectorId) {
      router.push(`/explore?cat=${catId}`)
    } else {
      router.push(`/explore?cat=${catId}&sector=${sectorId}`)
    }
  }

  const topCrosswalks = (() => {
    if (!stats) return []
    const seen = new Set<string>()
    return stats
      .filter((s) => {
        const key = [s.source_system, s.target_system].sort().join('|')
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      .sort((a, b) => b.edge_count - a.edge_count)
      .slice(0, 12)
  })()

  return (
    <div className="space-y-10">

      {/* Example query suggestions */}
      <div className="max-w-4xl">
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span>Try:</span>
          {EXAMPLE_QUERIES.map((term) => (
            <button
              key={term}
              onClick={() => { setQuery(term); setDebouncedQuery(term) }}
              className="px-2.5 py-1 rounded-full bg-secondary hover:bg-secondary/70 transition-colors font-mono"
            >
              {term}
            </button>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { icon: Globe,     value: systems?.length ?? 0, label: 'Classification Systems', mono: false, href: '/explore' },
          { icon: GitBranch, value: totalNodes,            label: 'Total Nodes',            mono: true,  href: '/explore' },
          { icon: Network,   value: totalEdges,            label: 'Crosswalk Edges',        mono: true,  href: '/crosswalks' },
        ].map(({ icon: Icon, value, label, mono, href }) => (
          <Link key={label} href={href} className="p-5 rounded-xl bg-card border border-border/50 space-y-1 hover:border-border hover:shadow-sm transition-all group">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Icon className="h-4 w-4" />
              <span className="text-xs font-medium">{label}</span>
              <ArrowUpRight className="h-3 w-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div className={`text-3xl font-bold ${mono ? 'font-mono tabular-nums' : ''}`}>
              {mono ? value.toLocaleString() : value}
            </div>
          </Link>
        ))}
      </div>

      {/* Category filter tabs */}
      <div className="flex flex-wrap gap-2">
        <Link
          href="/explore"
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            !activeCat
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-muted-foreground hover:text-foreground'
          }`}
        >
          All
        </Link>
        {SYSTEM_CATEGORIES.map((cat) => {
          const g = grouped.find((g) => g.category.id === cat.id)
          if (!g || g.systems.length === 0) return null
          return (
            <Link
              key={cat.id}
              href={`/explore?cat=${cat.id}`}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                activeCat === cat.id
                  ? 'text-white'
                  : 'bg-secondary text-muted-foreground hover:text-foreground'
              }`}
              style={activeCat === cat.id ? { backgroundColor: cat.accent } : {}}
            >
              {cat.label}
              <span className="ml-1.5 opacity-60">{g.systems.length}</span>
            </Link>
          )
        })}
      </div>

      {/* Domain sector sub-filter */}
      {activeCat === 'domain' && domainSectorsPresent.length > 0 && (
        <div className="space-y-2 rounded-xl border border-border/50 bg-card/50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Filter by sector</span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 mb-2">
            <button
              onClick={() => router.push('/explore?cat=domain')}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                !activeSectorId
                  ? 'bg-foreground text-background'
                  : 'bg-secondary text-muted-foreground hover:text-foreground'
              }`}
            >
              All
              <span className="ml-1 font-mono opacity-70">{allDomainSystems.length}</span>
            </button>
          </div>

          {traditionalSectors.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">Traditional</p>
              <div className="flex flex-wrap gap-1.5">
                {traditionalSectors.slice().sort((a, b) => a.label.localeCompare(b.label)).map((sector) => (
                  <button
                    key={sector.id}
                    onClick={() => handleSectorClick(sector.id, 'domain')}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                      activeSectorId === sector.id
                        ? 'text-white'
                        : 'bg-secondary text-muted-foreground hover:text-foreground'
                    }`}
                    style={activeSectorId === sector.id ? { backgroundColor: sector.accent } : {}}
                  >
                    {sector.label}
                    <span className="ml-1 font-mono opacity-70">{sectorSystemCount(sector.id)}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {emergingSectors.length > 0 && (
            <div className="space-y-1.5 mt-2">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">Emerging Tech</p>
              <div className="flex flex-wrap gap-1.5">
                {emergingSectors.slice().sort((a, b) => a.label.localeCompare(b.label)).map((sector) => (
                  <button
                    key={sector.id}
                    onClick={() => handleSectorClick(sector.id, 'domain')}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                      activeSectorId === sector.id
                        ? 'text-white'
                        : 'bg-secondary text-muted-foreground hover:text-foreground'
                    }`}
                    style={activeSectorId === sector.id ? { backgroundColor: sector.accent } : {}}
                  >
                    {sector.label}
                    <span className="ml-1 font-mono opacity-70">{sectorSystemCount(sector.id)}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Life Sciences sector sub-filter */}
      {activeCat === 'lifesciences' && lsSectorsPresent.length > 0 && (
        <div className="space-y-2 rounded-xl border border-border/50 bg-card/50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Filter by sector</span>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 mb-2">
            <button
              onClick={() => router.push('/explore?cat=lifesciences')}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                !activeSectorId
                  ? 'bg-foreground text-background'
                  : 'bg-secondary text-muted-foreground hover:text-foreground'
              }`}
            >
              All
              <span className="ml-1 font-mono opacity-70">{allLSSystems.length}</span>
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {lsSectorsPresent.map((sector) => (
              <button
                key={sector.id}
                onClick={() => handleSectorClick(sector.id, 'lifesciences')}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                  activeSectorId === sector.id
                    ? 'text-white'
                    : 'bg-secondary text-muted-foreground hover:text-foreground'
                }`}
                style={activeSectorId === sector.id ? { backgroundColor: sector.accent } : {}}
              >
                {sector.label}
                <span className="ml-1 font-mono opacity-70">{sectorSystemCount(sector.id)}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Systems grouped by category */}
      <div className="space-y-3">
        {grouped
          .filter((g) => !activeCat || g.category.id === activeCat)
          .map(({ category: cat, systems: catSystems }) => {
            const displaySystems = (cat.id === 'domain' || cat.id === 'lifesciences')
              ? filterBySector(catSystems, cat.id)
              : catSystems
            const sectorLabel = activeSectorDef && (cat.id === 'domain' || cat.id === 'lifesciences')
              ? ` - ${activeSectorDef.label}`
              : ''
            const isOpen = activeCat === cat.id || openCats.has(cat.id)
            const toggle = () => {
              setOpenCats((prev) => {
                const next = new Set(prev)
                if (next.has(cat.id)) next.delete(cat.id)
                else next.add(cat.id)
                return next
              })
            }
            return (
              <div key={cat.id} className="rounded-xl border border-border/50 overflow-hidden">
                <button
                  type="button"
                  onClick={toggle}
                  aria-expanded={isOpen}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted/20 transition-colors"
                >
                  {isOpen ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                  <div
                    className="w-3 h-3 rounded-sm shrink-0"
                    style={{ backgroundColor: activeSectorDef && (cat.id === 'domain' || cat.id === 'lifesciences') ? activeSectorDef.accent : cat.accent }}
                  />
                  <h2 className="text-base font-semibold">{cat.label}{sectorLabel}</h2>
                  <span className="text-xs text-muted-foreground">
                    {displaySystems.length} system{displaySystems.length !== 1 ? 's' : ''} &middot;{' '}
                    {displaySystems.reduce((s, x) => s + x.node_count, 0).toLocaleString()} nodes
                  </span>
                </button>

                {isOpen && (
                  <div className="border-t border-border/40">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-muted/40 border-b border-border/40">
                          <th className="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">System</th>
                          <th className="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground hidden sm:table-cell">Region</th>
                          <th className="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground w-20">Nodes</th>
                          <th className="px-4 py-2.5 w-36 hidden md:table-cell" />
                        </tr>
                      </thead>
                      <tbody>
                        {displaySystems
                          .slice()
                          .sort((a, b) => a.name.localeCompare(b.name))
                          .map((sys) => {
                            const pct = maxNodes > 0 ? (sys.node_count / maxNodes) * 100 : 0
                            const color = sys.tint_color || cat.accent
                            return (
                              <tr
                                key={sys.id}
                                className="border-b border-border/30 last:border-0 hover:bg-muted/20 transition-colors"
                              >
                                <td className="px-4 py-3">
                                  <Link
                                    href={`/system/${sys.id}`}
                                    className="flex items-center gap-2 group"
                                  >
                                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
                                    <span className="font-medium group-hover:text-primary transition-colors">
                                      {sys.name}
                                    </span>
                                    <ArrowUpRight className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                                  </Link>
                                </td>
                                <td className="px-4 py-3 text-xs text-muted-foreground hidden sm:table-cell">
                                  {sys.region ?? '-'}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-xs tabular-nums">
                                  {sys.node_count.toLocaleString()}
                                </td>
                                <td className="px-4 py-3 hidden md:table-cell">
                                  <div className="h-1.5 rounded-full bg-muted overflow-hidden w-full">
                                    <div
                                      className="h-full rounded-full transition-all"
                                      style={{ width: `${Math.max(pct, 1)}%`, backgroundColor: color }}
                                    />
                                  </div>
                                </td>
                              </tr>
                            )
                          })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )
          })}
      </div>

      {/* Top crosswalks */}
      {!activeCat && topCrosswalks.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-base font-semibold">Top Crosswalk Connections</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {topCrosswalks.map((s, i) => (
              <div
                key={i}
                className="flex items-center justify-between px-4 py-3 rounded-lg bg-card border border-border/50"
              >
                <div className="flex items-center gap-2 text-xs font-mono min-w-0">
                  <span className="truncate text-muted-foreground">{s.source_system}</span>
                  <span className="text-border shrink-0">&#8644;</span>
                  <span className="truncate text-muted-foreground">{s.target_system}</span>
                </div>
                <span className="text-xs font-mono font-semibold tabular-nums shrink-0 ml-2">
                  {s.edge_count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Single result row ───────────────────────────────────────────────────────

function ResultRow({
  node,
  systems,
  query,
}: {
  node: ClassificationNodeWithContext
  systems: { id: string; name: string }[]
  query: string
}) {
  const sysName = systems.find((s) => s.id === node.system_id)?.name ?? node.system_id
  const sysColor = getSystemColor(node.system_id)
  const parent = node.ancestors && node.ancestors.length > 0
    ? node.ancestors[node.ancestors.length - 1]
    : null
  const grandparent = node.ancestors && node.ancestors.length > 1
    ? node.ancestors[node.ancestors.length - 2]
    : null

  return (
    <Link
      href={`/system/${node.system_id}/node/${encodeURIComponent(node.code)}`}
      className="flex items-start gap-3 px-3 py-2.5 rounded-lg hover:bg-card border border-transparent hover:border-border/40 transition-all group"
    >
      <span className="shrink-0 w-4 pt-1 flex justify-center">
        {node.is_leaf && <Leaf className="h-3 w-3 text-emerald-500/60" />}
      </span>
      <div className="flex items-center gap-1.5 shrink-0 w-28 pt-0.5">
        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: sysColor }} />
        <span className="text-[11px] font-medium truncate" style={{ color: sysColor }}>{sysName}</span>
      </div>
      <span className="font-mono text-xs text-muted-foreground shrink-0 w-20 pt-0.5 group-hover:text-foreground/70 transition-colors">
        {node.code}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-foreground/85 group-hover:text-foreground transition-colors truncate">
          <Highlight text={node.title} query={query} />
        </p>
        {parent && (
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {grandparent ? (
              <>{grandparent.title} <span className="opacity-50">›</span> {parent.title}</>
            ) : (
              parent.title
            )}
          </p>
        )}
      </div>
    </Link>
  )
}

function Highlight({ text, query }: { text: string; query: string }) {
  if (!query || query.length < 2) return <>{text}</>
  try {
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    const parts = text.split(re)
    return (
      <>
        {parts.map((part, i) =>
          re.test(part) ? (
            <mark key={i} className="bg-primary/20 text-foreground rounded-sm px-0.5">
              {part}
            </mark>
          ) : (
            part
          )
        )}
      </>
    )
  } catch {
    return <>{text}</>
  }
}

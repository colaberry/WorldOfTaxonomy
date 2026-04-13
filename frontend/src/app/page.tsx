'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSystems, getStats } from '@/lib/api'
import { GalaxyView } from '@/components/visualizations/GalaxyView'
import { WorldMap } from '@/components/visualizations/WorldMap'
import { IndustryMap } from '@/components/IndustryMap'
import { SYSTEM_CATEGORIES, groupSystemsByCategory, getCategoryForSystem } from '@/lib/categories'
import Link from 'next/link'
import { Globe, GitBranch, Network, ArrowRight, Search } from 'lucide-react'

export default function HomePage() {
  const [galaxyCat, setGalaxyCat] = useState('')

  const { data: systems, isLoading: loadingSystems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
  })

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  })

  const totalNodes = systems?.reduce((sum, s) => sum + s.node_count, 0) ?? 0
  const totalEdges = stats?.reduce((sum, s) => sum + s.edge_count, 0) ?? 0
  const grouped = systems ? groupSystemsByCategory(systems) : []

  return (
    <div className="flex flex-col gap-12 pb-12">

      {/* ── Hero ── */}
      <section className="relative overflow-hidden bg-gradient-to-b from-card/80 to-background border-b border-border/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-14 sm:py-20 flex flex-col items-center text-center gap-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border/60 bg-secondary/50 text-xs text-muted-foreground font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            {loadingSystems ? '...' : `${systems?.length ?? 82} systems live`}
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-tight max-w-3xl">
            The Global Classification
            <span className="text-primary"> Knowledge Graph</span>
          </h1>

          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl leading-relaxed">
            A unified graph connecting industry, geography, trade, occupations, health,
            patents, and more - spanning every major classification standard worldwide.
          </p>

          {/* Stat pills */}
          <div className="flex flex-wrap gap-3 justify-center">
            {[
              { icon: Globe,     value: loadingSystems ? '...' : (systems?.length ?? 82).toString(),     label: 'Systems' },
              { icon: GitBranch, value: loadingSystems ? '...' : totalNodes.toLocaleString(),            label: 'Nodes' },
              { icon: Network,   value: loadingStats   ? '...' : totalEdges.toLocaleString(),            label: 'Connections' },
            ].map(({ icon: Icon, value, label }) => (
              <div
                key={label}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-card border border-border/50 shadow-sm"
              >
                <Icon className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold font-mono tabular-nums">{value}</span>
                <span className="text-xs text-muted-foreground">{label}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-3 flex-wrap justify-center">
            <Link
              href="/explore"
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              <Search className="h-4 w-4" />
              Search all codes
            </Link>
            <Link
              href="/dashboard"
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-secondary text-secondary-foreground text-sm font-medium hover:bg-secondary/80 transition-colors"
            >
              Browse systems
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── World Map ── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 w-full space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Global Coverage</h2>
            <p className="text-sm text-muted-foreground">Countries colored by taxonomy coverage depth</p>
          </div>
          <Link
            href="/dashboard"
            className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
          >
            View all systems <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        <WorldMap />
      </div>

      {/* ── Galaxy View ── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 w-full space-y-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-lg font-semibold tracking-tight">Classification Galaxy</h2>
            <p className="text-sm text-muted-foreground">
              Each orb is a classification system - size reflects node count, edges show crosswalk connections
            </p>
          </div>
        </div>

        {/* Category filter tabs */}
        {systems && (
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setGalaxyCat('')}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                !galaxyCat
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-muted-foreground hover:text-foreground'
              }`}
            >
              All
            </button>
            {SYSTEM_CATEGORIES.map((cat) => {
              const count = systems.filter((s) => getCategoryForSystem(s.id).id === cat.id).length
              if (count === 0) return null
              return (
                <button
                  key={cat.id}
                  onClick={() => setGalaxyCat(galaxyCat === cat.id ? '' : cat.id)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    galaxyCat === cat.id
                      ? 'text-white'
                      : 'bg-secondary text-muted-foreground hover:text-foreground'
                  }`}
                  style={galaxyCat === cat.id ? { backgroundColor: cat.accent } : {}}
                >
                  {cat.label}
                  <span className="ml-1 opacity-60">{count}</span>
                </button>
              )
            })}
          </div>
        )}

        {loadingSystems || loadingStats ? (
          <div className="w-full aspect-[16/10] max-h-[600px] rounded-xl bg-card border border-border/50 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3 text-muted-foreground">
              <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-sm">Loading galaxy...</span>
            </div>
          </div>
        ) : systems && stats ? (
          <GalaxyView
            systems={galaxyCat ? systems.filter((s) => getCategoryForSystem(s.id).id === galaxyCat) : systems}
            stats={stats}
          />
        ) : null}

        <p className="text-center text-xs text-muted-foreground">
          Click any system to explore its hierarchy. Drag to rearrange.
        </p>
      </div>

      {/* ── Browse by Category ── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 w-full space-y-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Browse by Category</h2>
          <p className="text-sm text-muted-foreground">
            {SYSTEM_CATEGORIES.length} categories spanning every classification domain
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {SYSTEM_CATEGORIES.map((cat) => {
            const group = grouped.find((g) => g.category.id === cat.id)
            const systemCount = group?.systems.length ?? 0
            const nodeCount = group?.systems.reduce((s, sys) => s + sys.node_count, 0) ?? 0
            if (systemCount === 0 && !loadingSystems) return null
            return (
              <Link
                key={cat.id}
                href={`/dashboard?cat=${cat.id}`}
                className="group flex flex-col gap-2 p-4 rounded-xl border border-border/50 bg-card hover:border-border hover:shadow-sm transition-all"
                style={{ borderLeftColor: cat.accent, borderLeftWidth: 3 }}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm font-semibold leading-tight">{cat.label}</span>
                  <ArrowRight
                    className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 shrink-0 mt-0.5 transition-opacity"
                  />
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                  {cat.description}
                </p>
                <div className="flex items-center gap-3 mt-auto pt-1">
                  <span className="text-xs font-mono" style={{ color: cat.accent }}>
                    {loadingSystems ? '...' : systemCount} systems
                  </span>
                  <span className="text-xs text-muted-foreground font-mono">
                    {loadingSystems ? '' : nodeCount.toLocaleString()} nodes
                  </span>
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* ── Industry Sectors ── */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 w-full space-y-4">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Browse by Industry Sector</h2>
          <p className="text-sm text-muted-foreground">
            Jump directly into a sector across all classification systems
          </p>
        </div>
        <IndustryMap />
      </div>
    </div>
  )
}

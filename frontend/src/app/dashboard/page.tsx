'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { getSystems, getStats } from '@/lib/api'
import { groupSystemsByCategory, SYSTEM_CATEGORIES } from '@/lib/categories'
import Link from 'next/link'
import { Globe, GitBranch, Network, ArrowUpRight } from 'lucide-react'

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  )
}

function DashboardContent() {
  const searchParams = useSearchParams()
  const activeCat = searchParams.get('cat') ?? ''

  const { data: systems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
  })

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  })

  const totalNodes = systems?.reduce((sum, s) => sum + s.node_count, 0) ?? 0
  const totalEdges = stats?.reduce((sum, s) => sum + s.edge_count, 0) ?? 0
  const grouped = systems ? groupSystemsByCategory(systems) : []
  const maxNodes = systems ? Math.max(...systems.map((s) => s.node_count)) : 1

  // Top crosswalk pairs (deduplicated, sorted by edge count)
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-10">

      {/* ── Page header ── */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Systems Overview</h1>
        <p className="text-sm text-muted-foreground mt-1">
          All {systems?.length ?? 82} classification systems across 8 categories
        </p>
      </div>

      {/* ── Summary stats ── */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { icon: Globe,     value: systems?.length ?? 0, label: 'Classification Systems', mono: false },
          { icon: GitBranch, value: totalNodes,            label: 'Total Nodes',            mono: true  },
          { icon: Network,   value: totalEdges,            label: 'Crosswalk Edges',        mono: true  },
        ].map(({ icon: Icon, value, label, mono }) => (
          <div key={label} className="p-5 rounded-xl bg-card border border-border/50 space-y-1">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Icon className="h-4 w-4" />
              <span className="text-xs font-medium">{label}</span>
            </div>
            <div className={`text-3xl font-bold ${mono ? 'font-mono tabular-nums' : ''}`}>
              {mono ? value.toLocaleString() : value}
            </div>
          </div>
        ))}
      </div>

      {/* ── Category filter tabs ── */}
      <div className="flex flex-wrap gap-2">
        <Link
          href="/dashboard"
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
              href={`/dashboard?cat=${cat.id}`}
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

      {/* ── Systems grouped by category ── */}
      <div className="space-y-8">
        {grouped
          .filter((g) => !activeCat || g.category.id === activeCat)
          .map(({ category: cat, systems: catSystems }) => (
            <div key={cat.id}>
              {/* Category header */}
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-3 h-3 rounded-sm shrink-0"
                  style={{ backgroundColor: cat.accent }}
                />
                <h2 className="text-base font-semibold">{cat.label}</h2>
                <span className="text-xs text-muted-foreground">
                  {catSystems.length} system{catSystems.length !== 1 ? 's' : ''} &middot;{' '}
                  {catSystems.reduce((s, x) => s + x.node_count, 0).toLocaleString()} nodes
                </span>
              </div>

              {/* Systems table */}
              <div className="rounded-xl border border-border/50 overflow-hidden">
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
                    {catSystems
                      .slice()
                      .sort((a, b) => b.node_count - a.node_count)
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
                                <span
                                  className="w-2.5 h-2.5 rounded-full shrink-0"
                                  style={{ backgroundColor: color }}
                                />
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
                            {/* Visual bar */}
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
            </div>
          ))}
      </div>

      {/* ── Top crosswalks ── */}
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

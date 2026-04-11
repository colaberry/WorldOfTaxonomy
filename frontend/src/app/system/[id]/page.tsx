'use client'

import { use } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSystem, getStats, getSystems } from '@/lib/api'
import Link from 'next/link'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { getSystemColor } from '@/lib/colors'
import { SectorTreemap } from '@/components/visualizations/SectorTreemap'
import { CrosswalkNetwork } from '@/components/visualizations/CrosswalkNetwork'

export default function SystemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)

  const { data: system, isLoading } = useQuery({
    queryKey: ['system', id],
    queryFn: () => getSystem(id),
  })

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  })

  const { data: allSystems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Loading system...</span>
        </div>
      </div>
    )
  }

  if (!system) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <p className="text-muted-foreground">System not found</p>
      </div>
    )
  }

  // Deduplicate: treat crosswalk pairs as undirected - stats API returns both directions
  const seen = new Set<string>()
  const systemStats = (stats ?? [])
    .filter((s) => s.source_system === id || s.target_system === id)
    .filter((s) => {
      const partner = s.source_system === id ? s.target_system : s.source_system
      if (seen.has(partner)) return false
      seen.add(partner)
      return true
    })

  const totalEdges = systemStats.reduce((sum, s) => sum + s.edge_count, 0)

  const connections = systemStats.map((s) => {
    const partnerId = s.source_system === id ? s.target_system : s.source_system
    const partner = allSystems?.find((sys) => sys.id === partnerId)
    return {
      systemId: partnerId,
      systemName: partner?.name ?? partnerId,
      edgeCount: s.edge_count,
      exactCount: s.exact_count,
    }
  })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex items-center gap-3">
          <span
            className="w-3 h-3 rounded-full shrink-0"
            style={{ backgroundColor: system.tint_color || '#3B82F6' }}
          />
          <h1 className="text-2xl font-semibold tracking-tight">{system.name}</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-1">Full Name</div>
          <div className="text-sm font-medium">{system.full_name}</div>
        </div>
        <div className="p-4 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-1">Region</div>
          <div className="text-sm font-medium">{system.region}</div>
        </div>
        <div className="p-4 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-1">Codes</div>
          <div className="text-sm font-medium font-mono">{system.node_count.toLocaleString()}</div>
        </div>
        <div className="p-4 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-1">Crosswalk Edges</div>
          <div className="text-sm font-medium font-mono">{totalEdges.toLocaleString()}</div>
        </div>
      </div>

      {system.authority && (
        <div className="p-4 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-1">Authority</div>
          <div className="text-sm">
            {system.authority}
            {system.url && (
              <a
                href={system.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 ml-2 text-primary hover:underline"
              >
                Visit <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>
      )}

      {system.roots && system.roots.length > 0 && (
        <SectorTreemap systemId={id} roots={system.roots} />
      )}

      <div>
        <h2 className="text-lg font-semibold mb-3">Top-Level Sectors</h2>
        {system.roots && system.roots.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {system.roots.map((root) => (
              <Link
                key={root.code}
                href={`/system/${id}/node/${root.code}`}
                className="p-3 rounded-lg bg-card border border-border/50 hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-baseline gap-2">
                  <span className="text-xs font-mono text-muted-foreground">{root.code}</span>
                  <span className="text-sm group-hover:text-primary transition-colors">
                    {root.title}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No root nodes found.</p>
        )}
      </div>

      {connections.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Crosswalk Connections</h2>

          {connections.length >= 3 && system ? (
            // Network diagram for well-connected systems (3+ partners)
            <div className="rounded-xl border border-border/50 bg-card/30 overflow-hidden">
              <CrosswalkNetwork currentSystem={system} connections={connections} />
            </div>
          ) : (
            // Simple list for sparsely-connected systems (1–2 partners)
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {connections.map((c) => {
                const otherColor = getSystemColor(c.systemId)
                return (
                  <Link
                    key={c.systemId}
                    href={`/system/${c.systemId}`}
                    className="p-3 rounded-lg bg-card border border-border/50 hover:border-border transition-colors flex items-center gap-3"
                  >
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: otherColor }} />
                    <span className="text-sm">{c.systemName}</span>
                    <div className="ml-auto text-right">
                      <span className="text-xs font-mono text-muted-foreground block">
                        {c.edgeCount.toLocaleString()} edges
                      </span>
                      {c.exactCount > 0 && (
                        <span className="text-xs text-emerald-400">{c.exactCount} exact</span>
                      )}
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

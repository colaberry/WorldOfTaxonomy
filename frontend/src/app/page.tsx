'use client'

import { useQuery } from '@tanstack/react-query'
import { getSystems, getStats } from '@/lib/api'
import { GalaxyView } from '@/components/visualizations/GalaxyView'
import { WorldMap } from '@/components/visualizations/WorldMap'
import { IndustryMap } from '@/components/IndustryMap'
import { Globe, GitBranch, Network } from 'lucide-react'

export default function HomePage() {
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

  return (
    <div className="flex flex-col gap-10 px-4 sm:px-6 py-6 max-w-7xl mx-auto w-full">
      {/* World Map - primary entry point */}
      <div className="space-y-3">
        <div className="text-center space-y-1">
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">
            World of Taxonomy
          </h1>
          <p className="text-sm text-muted-foreground max-w-xl mx-auto">
            A unified knowledge graph connecting classification systems from every country.
            Explore {loadingSystems ? '...' : (systems?.length ?? 0)} global standards covering 500,000+ codes.
          </p>
        </div>
        <WorldMap />
      </div>

      {/* Divider */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-border/50" />
        <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Quick Stats</span>
        <div className="flex-1 h-px bg-border/50" />
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-3 sm:gap-4 max-w-lg mx-auto w-full">
        <div className="flex flex-col items-center gap-1 p-3 rounded-lg bg-card border border-border/50">
          <Globe className="h-4 w-4 text-primary" />
          <span className="text-lg sm:text-xl font-semibold font-mono tabular-nums">
            {loadingSystems ? '...' : systems?.length ?? 0}
          </span>
          <span className="text-[10px] sm:text-xs text-muted-foreground">Systems</span>
        </div>
        <div className="flex flex-col items-center gap-1 p-3 rounded-lg bg-card border border-border/50">
          <GitBranch className="h-4 w-4 text-primary" />
          <span className="text-lg sm:text-xl font-semibold font-mono tabular-nums">
            {loadingSystems ? '...' : totalNodes.toLocaleString()}
          </span>
          <span className="text-[10px] sm:text-xs text-muted-foreground">Codes</span>
        </div>
        <div className="flex flex-col items-center gap-1 p-3 rounded-lg bg-card border border-border/50">
          <Network className="h-4 w-4 text-primary" />
          <span className="text-lg sm:text-xl font-semibold font-mono tabular-nums">
            {loadingStats ? '...' : totalEdges.toLocaleString()}
          </span>
          <span className="text-[10px] sm:text-xs text-muted-foreground">Edges</span>
        </div>
      </div>

      {/* Industry Map - primary entry point */}
      <IndustryMap />

      {/* Divider */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-border/50" />
        <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Classification Standards</span>
        <div className="flex-1 h-px bg-border/50" />
      </div>

      {/* Galaxy View */}
      <div className="w-full">
        {loadingSystems || loadingStats ? (
          <div className="w-full aspect-[16/10] max-h-[600px] rounded-lg bg-card border border-border/50 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3 text-muted-foreground">
              <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-sm">Loading galaxy...</span>
            </div>
          </div>
        ) : systems && stats ? (
          <GalaxyView systems={systems} stats={stats} />
        ) : null}
      </div>

      <p className="text-center text-xs text-muted-foreground pb-4">
        Click any system to explore its classification hierarchy. Drag to rearrange.
      </p>
    </div>
  )
}

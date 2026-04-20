'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { getSystems, getStats } from '@/lib/api'
import { CrosswalkGraph } from './CrosswalkGraph'
import { ArrowRight } from 'lucide-react'

interface Props {
  topN?: number
  height?: number
  linkToExplorer?: boolean
}

export function CrosswalkRingPreview({ topN = 250, height = 560, linkToExplorer = true }: Props) {
  const { data: systems, isLoading: loadingSystems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
    staleTime: 5 * 60 * 1000,
  })

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    staleTime: 5 * 60 * 1000,
  })

  const loading = loadingSystems || loadingStats

  const graph = systems && stats ? (
    <div className="pointer-events-none w-full h-full">
      <CrosswalkGraph mode="system" systems={systems} stats={stats} topN={topN} />
    </div>
  ) : (
    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
      {loading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Loading crosswalk graph...</span>
        </div>
      ) : (
        <span className="text-sm">Unable to load classification graph.</span>
      )}
    </div>
  )

  const container = (
    <div
      className="relative w-full rounded-xl border border-border/50 bg-background overflow-hidden"
      style={{ height }}
    >
      {graph}
      {linkToExplorer && (
        <div className="absolute bottom-3 right-3 pointer-events-auto">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-card/90 border border-border/50 text-[11px] font-medium shadow-sm">
            Explore crosswalks <ArrowRight className="h-3 w-3" />
          </span>
        </div>
      )}
    </div>
  )

  if (!linkToExplorer) return container

  return (
    <Link href="/crosswalks" className="block group">
      {container}
    </Link>
  )
}

'use client'

import { useQuery } from '@tanstack/react-query'
import { getSystem, getStats, getSystems } from '@/lib/api'
import Link from 'next/link'
import { ArrowLeft, ExternalLink, Download, Lock, AlertTriangle } from 'lucide-react'
import { getSystemColor } from '@/lib/colors'
import { getToken } from '@/lib/auth'
import { CrosswalkNetwork } from '@/components/visualizations/CrosswalkNetwork'
import { NodeTree } from '@/components/NodeTree'
import { RadialDendrogram } from '@/components/visualizations/RadialDendrogram'
import type { SystemDetail as SystemDetailType, CrosswalkStat, ClassificationSystem } from '@/lib/types'
import type { TreeNodeData } from '@/lib/tree-data'

const GITHUB_REPO = 'https://github.com/colaberry/WorldOfTaxonomy'

interface SystemDetailProps {
  id: string
  initialSystem?: SystemDetailType | null
  initialStats?: CrosswalkStat[] | null
  initialSystems?: ClassificationSystem[] | null
  initialTreeNodes?: TreeNodeData[] | null
}

export function SystemDetail({ id, initialSystem, initialStats, initialSystems, initialTreeNodes }: SystemDetailProps) {
  const { data: system, isLoading } = useQuery({
    queryKey: ['system', id],
    queryFn: () => getSystem(id),
    initialData: initialSystem ?? undefined,
    staleTime: 0,
  })

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    initialData: initialStats ?? undefined,
    staleTime: 0,
  })

  const { data: allSystems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
    initialData: initialSystems ?? undefined,
    staleTime: 0,
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

  const issueUrl = `${GITHUB_REPO}/issues/new?template=data_issue.yml&title=${encodeURIComponent(`[Data] ${system.name}`)}&labels=data-issue`

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex items-center gap-3 flex-wrap">
          <span
            className="w-3 h-3 rounded-full shrink-0"
            style={{ backgroundColor: system.tint_color || '#3B82F6' }}
          />
          <h1 className="text-2xl font-semibold tracking-tight">{system.name}</h1>
          <span
            className={`inline-flex items-center gap-1 text-[11px] font-medium uppercase tracking-wide px-2 py-0.5 rounded-full border ${
              system.category === 'domain'
                ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30'
                : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30'
            }`}
            title={
              system.category === 'domain'
                ? 'Domain taxonomy: a plain-language on-ramp curated by WorldOfTaxonomy.'
                : 'Official standard: published by a government, intergovernmental body, or standards authority.'
            }
          >
            {system.category === 'domain' ? 'Domain taxonomy' : 'Official standard'}
          </span>
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

      {/* Download row */}
      <DownloadRow systemId={id} connections={connections} />

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

      {system.data_provenance && (
        <div className="p-4 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-2">Data Provenance</div>
          <div className="flex flex-wrap items-center gap-3">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
              system.data_provenance === 'official_download' ? 'bg-emerald-500/10 text-emerald-500' :
              system.data_provenance === 'structural_derivation' ? 'bg-blue-500/10 text-blue-500' :
              system.data_provenance === 'manual_transcription' ? 'bg-amber-500/10 text-amber-500' :
              'bg-purple-500/10 text-purple-500'
            }`}>
              {system.data_provenance === 'official_download' && 'Official Download'}
              {system.data_provenance === 'structural_derivation' && 'Structural Derivation'}
              {system.data_provenance === 'manual_transcription' && 'Manual Transcription'}
              {system.data_provenance === 'expert_curated' && 'Expert Curated'}
            </span>
            {system.license && (
              <span className="text-xs text-muted-foreground">License: {system.license}</span>
            )}
            {system.source_date && (
              <span className="text-xs text-muted-foreground">Verified: {system.source_date}</span>
            )}
            {system.source_url && (
              <a
                href={system.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
              >
                Source <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold mb-3">Hierarchy Explorer</h2>
        {system.roots && system.roots.length > 0 ? (
          <NodeTree
            systemId={id}
            roots={system.roots}
            systems={allSystems ?? []}
          />
        ) : (
          <p className="text-sm text-muted-foreground">No root nodes found.</p>
        )}
      </div>

      {initialTreeNodes && initialTreeNodes.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Structure Overview</h2>
          <RadialDendrogram
            systemId={id}
            initialNodes={initialTreeNodes}
            systemColor={system.tint_color ?? undefined}
          />
        </div>
      )}

      {connections.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Crosswalk Connections</h2>

          {connections.length >= 3 && system ? (
            <div className="rounded-xl border border-border/50 bg-card/30 overflow-hidden">
              <CrosswalkNetwork currentSystem={system} connections={connections} />
            </div>
          ) : (
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

      {/* Report a data issue link */}
      <div className="flex items-center gap-2 pt-2">
        <a
          href={issueUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          Report a data issue
        </a>
      </div>
    </div>
  )
}

// ---- Download Row ----

interface Connection {
  systemId: string
  systemName: string
  edgeCount: number
  exactCount: number
}

function DownloadRow({
  systemId,
  connections,
}: {
  systemId: string
  connections: Connection[]
}) {
  const token = getToken()

  async function triggerDownload(url: string, filename: string) {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) return
    const blob = await res.blob()
    const href = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = href
    a.download = filename
    a.click()
    URL.revokeObjectURL(href)
  }

  if (!token) {
    return (
      <div className="flex items-center gap-2 p-3 rounded-lg bg-card border border-border/50 text-sm text-muted-foreground">
        <Lock className="h-4 w-4 shrink-0" />
        <span>
          <a href="/login" className="text-primary hover:underline">Sign in</a>
          {' '}to download nodes or crosswalk data as CSV.
        </span>
      </div>
    )
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() =>
          triggerDownload(
            `/api/v1/systems/${systemId}/export.csv`,
            `${systemId}_nodes.csv`,
          )
        }
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border/50 hover:border-primary/50 text-xs font-medium transition-colors"
      >
        <Download className="h-3.5 w-3.5" />
        All nodes (.csv)
      </button>

      {connections.map((c) => (
        <button
          key={c.systemId}
          onClick={() =>
            triggerDownload(
              `/api/v1/systems/${systemId}/crosswalk/${c.systemId}/export.csv`,
              `${systemId}_to_${c.systemId}_crosswalk.csv`,
            )
          }
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border/50 hover:border-primary/50 text-xs font-medium transition-colors"
        >
          <Download className="h-3.5 w-3.5" />
          {c.systemName} crosswalk (.csv)
        </button>
      ))}
    </div>
  )
}

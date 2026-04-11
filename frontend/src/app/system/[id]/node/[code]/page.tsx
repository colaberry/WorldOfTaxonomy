'use client'

import { use } from 'react'
import Link from 'next/link'
import { Fragment } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Copy, Leaf } from 'lucide-react'
import { getNode, getChildren, getAncestors, getEquivalences, getSystems } from '@/lib/api'
import { getSectorColor, getSystemColor } from '@/lib/colors'
import type { Equivalence } from '@/lib/types'

// Typography scale per DESIGN.md: hierarchy depth encoded in type
function titleClass(level: number): string {
  if (level <= 1) return 'font-serif text-2xl sm:text-3xl tracking-tight'
  if (level === 2) return 'font-semibold text-xl sm:text-2xl'
  if (level === 3) return 'font-medium text-lg'
  if (level === 4) return 'text-base'
  return 'font-mono text-sm'
}

export default function NodeDetailPage({
  params,
}: {
  params: Promise<{ id: string; code: string }>
}) {
  const { id, code } = use(params)
  const nodeCode = decodeURIComponent(code)

  const { data: node, isLoading } = useQuery({
    queryKey: ['node', id, nodeCode],
    queryFn: () => getNode(id, nodeCode),
  })

  const { data: ancestors } = useQuery({
    queryKey: ['ancestors', id, nodeCode],
    queryFn: () => getAncestors(id, nodeCode),
    enabled: !!node,
  })

  const { data: children } = useQuery({
    queryKey: ['children', id, nodeCode],
    queryFn: () => getChildren(id, nodeCode),
    enabled: !!node && !node.is_leaf,
  })

  const { data: equivalences } = useQuery({
    queryKey: ['equivalences', id, nodeCode],
    queryFn: () => getEquivalences(id, nodeCode),
    enabled: !!node,
  })

  const { data: systems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!node) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <p className="text-muted-foreground">Node not found</p>
      </div>
    )
  }

  const sectorColor = getSectorColor(node.sector_code ?? node.code)
  const systemName = systems?.find((s) => s.id === id)?.name ?? id
  const apiEndpoint = `/api/v1/systems/${id}/nodes/${nodeCode}`

  // Group equivalences by target system
  const equivBySystem = (equivalences ?? []).reduce<Record<string, Equivalence[]>>(
    (acc, e) => {
      ;(acc[e.target_system] ??= []).push(e)
      return acc
    },
    {}
  )

  const hasEquivalences = Object.keys(equivBySystem).length > 0
  const hasChildren = !node.is_leaf && children && children.length > 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">

      {/* Breadcrumb */}
      <nav className="flex items-center gap-1 flex-wrap text-sm text-muted-foreground">
        <Link href="/" className="hover:text-foreground transition-colors">Home</Link>
        <ChevronRight className="h-3.5 w-3.5 shrink-0" />
        <Link href={`/system/${id}`} className="hover:text-foreground transition-colors">
          {systemName}
        </Link>
        {ancestors?.slice(0, -1).map((a) => (
          <Fragment key={a.code}>
            <ChevronRight className="h-3.5 w-3.5 shrink-0" />
            <Link
              href={`/system/${id}/node/${encodeURIComponent(a.code)}`}
              className="font-mono hover:text-foreground transition-colors"
            >
              {a.code}
            </Link>
          </Fragment>
        ))}
        <ChevronRight className="h-3.5 w-3.5 shrink-0" />
        <span className="text-foreground font-mono">{nodeCode}</span>
      </nav>

      {/* Node hero */}
      <div
        className="p-5 sm:p-6 rounded-xl border border-border/50 space-y-3"
        style={{ backgroundColor: `${sectorColor}08` }}
      >
        {/* Code + badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className="font-mono text-base px-2.5 py-0.5 rounded-md border"
            style={{
              color: sectorColor,
              borderColor: `${sectorColor}40`,
              backgroundColor: `${sectorColor}12`,
            }}
          >
            {nodeCode}
          </span>
          {node.is_leaf && (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Leaf className="h-3 w-3" />
              Leaf
            </span>
          )}
          <span className="text-xs text-muted-foreground font-mono">
            Level {node.level}
          </span>
        </div>

        {/* Title - typography encodes depth per DESIGN.md */}
        <h1
          className={titleClass(node.level)}
          style={{ color: node.level <= 1 ? sectorColor : undefined }}
        >
          {node.title}
        </h1>

        {node.description && (
          <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
            {node.description}
          </p>
        )}

        {/* Inline API endpoint - MCP-first per DESIGN.md Risk 4 */}
        <div className="flex items-center gap-2 pt-1 flex-wrap">
          <span className="font-mono text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            GET
          </span>
          <code className="font-mono text-xs text-muted-foreground">{apiEndpoint}</code>
          <button
            onClick={() => navigator.clipboard.writeText(apiEndpoint)}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Copy endpoint"
          >
            <Copy className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Children + Equivalences grid */}
      <div className={`grid grid-cols-1 gap-6 ${!node.is_leaf ? 'lg:grid-cols-2' : ''}`}>

        {/* Children panel */}
        {!node.is_leaf && (
          <div className="space-y-2">
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              Sub-classifications
              {children && (
                <span className="font-mono normal-case font-normal">{children.length}</span>
              )}
            </h2>
            <div className="space-y-0.5">
              {hasChildren ? (
                children.map((child) => (
                  <Link
                    key={child.code}
                    href={`/system/${id}/node/${encodeURIComponent(child.code)}`}
                    className="flex items-baseline gap-3 px-3 py-2 rounded-lg hover:bg-card border border-transparent hover:border-border/50 transition-all group"
                  >
                    <span className="font-mono text-xs text-muted-foreground shrink-0 w-16 group-hover:text-foreground transition-colors">
                      {child.code}
                    </span>
                    <span className="text-sm group-hover:text-foreground transition-colors truncate">
                      {child.title}
                    </span>
                    {child.is_leaf && (
                      <Leaf className="h-3 w-3 text-emerald-500/40 shrink-0 ml-auto" />
                    )}
                  </Link>
                ))
              ) : (
                <div className="px-3 py-4 text-sm text-muted-foreground">
                  Loading…
                </div>
              )}
            </div>
          </div>
        )}

        {/* Equivalences panel */}
        <div className="space-y-2">
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
            Cross-system equivalences
            {equivalences && (
              <span className="font-mono normal-case font-normal">{equivalences.length}</span>
            )}
          </h2>

          {hasEquivalences ? (
            <div className="space-y-4">
              {Object.entries(equivBySystem).map(([sysId, edges]) => {
                const sysColor = getSystemColor(sysId)
                const sysName = systems?.find((s) => s.id === sysId)?.name ?? sysId
                return (
                  <div key={sysId}>
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: sysColor }}
                      />
                      <span className="text-xs font-medium">{sysName}</span>
                    </div>
                    <div className="space-y-0.5">
                      {edges.map((e) => (
                        <Link
                          key={`${e.target_system}-${e.target_code}`}
                          href={`/system/${e.target_system}/node/${encodeURIComponent(e.target_code)}`}
                          className="flex items-baseline gap-3 px-3 py-2 rounded-lg hover:bg-card border border-transparent hover:border-border/50 transition-all group"
                        >
                          <span
                            className="font-mono text-xs shrink-0 w-16 opacity-70 group-hover:opacity-100 transition-opacity"
                            style={{ color: sysColor }}
                          >
                            {e.target_code}
                          </span>
                          <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors truncate">
                            {e.target_title}
                          </span>
                          <span
                            className={`ml-auto text-xs px-1.5 py-0.5 rounded shrink-0 ${
                              e.match_type === 'exact'
                                ? 'bg-emerald-500/10 text-emerald-400'
                                : e.match_type === 'partial'
                                  ? 'bg-amber-500/10 text-amber-400'
                                  : 'bg-blue-500/10 text-blue-400'
                            }`}
                          >
                            {e.match_type}
                          </span>
                        </Link>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="px-3 py-4 rounded-lg border border-border/50 bg-card/50">
              <p className="text-sm text-muted-foreground">
                {equivalences === undefined
                  ? 'Loading…'
                  : 'No cross-system equivalences mapped for this node.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ChevronDown, ArrowRight, Network } from 'lucide-react'
import { getSystem } from '@/lib/api'
import type { ClassificationNode, ClassificationSystem } from '@/lib/types'

export interface CrosswalkBadge {
  target_system: string
  target_name: string
  edge_count: number
  color: string
}

interface Props {
  system: ClassificationSystem
  systemColor: string
  crosswalks: CrosswalkBadge[]
}

export function SystemCard({ system, systemColor, crosswalks }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [roots, setRoots] = useState<ClassificationNode[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const totalEdges = crosswalks.reduce((acc, c) => acc + c.edge_count, 0)

  async function toggle() {
    const next = !expanded
    setExpanded(next)
    if (next && roots === null && !loading) {
      setLoading(true)
      setError(null)
      try {
        const detail = await getSystem(system.id)
        setRoots(detail.roots)
      } catch {
        setError('Could not load sectors')
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <div
      className="rounded-xl border border-border bg-card overflow-hidden transition-colors hover:border-primary/40"
      style={{ boxShadow: expanded ? `inset 3px 0 0 0 ${systemColor}` : undefined }}
    >
      <button
        onClick={toggle}
        className="w-full flex items-start gap-3 p-5 text-left"
        aria-expanded={expanded}
      >
        <span
          className="inline-block size-3 rounded-full mt-1.5 shrink-0"
          style={{ backgroundColor: systemColor }}
        />
        <div className="flex-1 min-w-0 space-y-1.5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="text-base font-semibold truncate">
                {system.full_name ?? system.name}
              </h3>
              <p className="text-xs text-muted-foreground mt-0.5">
                {system.region ?? 'Global'}
                {system.authority ? ` · ${system.authority}` : ''}
                {system.version ? ` · ${system.version}` : ''}
              </p>
            </div>
            <ChevronDown
              className={`size-4 text-muted-foreground shrink-0 mt-1 transition-transform ${expanded ? 'rotate-180' : ''}`}
            />
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span>{system.node_count.toLocaleString()} codes</span>
            {totalEdges > 0 && (
              <span className="inline-flex items-center gap-1">
                <Network className="size-3" />
                {totalEdges.toLocaleString()} crosswalk {totalEdges === 1 ? 'edge' : 'edges'}
              </span>
            )}
          </div>
          {crosswalks.length > 0 && (
            <div className="flex items-center gap-1 pt-0.5">
              {crosswalks.slice(0, 10).map((c) => (
                <span
                  key={c.target_system}
                  className="inline-block size-2 rounded-full"
                  style={{ backgroundColor: c.color }}
                  title={`${c.target_name} - ${c.edge_count.toLocaleString()} edges`}
                />
              ))}
              {crosswalks.length > 10 && (
                <span className="text-[10px] text-muted-foreground ml-1">
                  +{crosswalks.length - 10}
                </span>
              )}
            </div>
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border/60 bg-muted/20 p-5 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Top-level sectors
              </h4>
              <Link
                href={`/codes/${system.id}`}
                className="text-xs text-primary hover:underline inline-flex items-center gap-1"
              >
                Full {system.name} page
                <ArrowRight className="size-3" />
              </Link>
            </div>
            {loading && (
              <div className="text-xs text-muted-foreground">Loading sectors...</div>
            )}
            {error && (
              <div className="text-xs text-destructive">{error}</div>
            )}
            {roots && roots.length > 0 && (
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {roots.map((node) => (
                  <li key={node.code}>
                    <Link
                      href={`/codes/${system.id}/${encodeURIComponent(node.code)}`}
                      className="flex items-baseline gap-2 rounded-md px-2 py-1.5 hover:bg-background border border-transparent hover:border-border transition-colors"
                    >
                      <span className="font-mono text-[11px] text-muted-foreground shrink-0">
                        {node.code}
                      </span>
                      <span className="text-sm truncate">{node.title}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            {roots && roots.length === 0 && (
              <div className="text-xs text-muted-foreground">
                No top-level sectors available.
              </div>
            )}
          </div>

          {crosswalks.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                Crosswalks to
              </h4>
              <ul className="flex flex-wrap gap-1.5">
                {crosswalks.map((c) => (
                  <li key={c.target_system}>
                    <Link
                      href={`/crosswalks/${system.id}/to/${c.target_system}`}
                      className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-2.5 py-1 text-xs hover:border-primary/50"
                    >
                      <span
                        className="inline-block size-2 rounded-full"
                        style={{ backgroundColor: c.color }}
                      />
                      {c.target_name}
                      <span className="text-muted-foreground">
                        {c.edge_count.toLocaleString()}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

'use client'

import { useState, useEffect, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { ChevronRight, Leaf, Wand2, Loader2 } from 'lucide-react'
import { getChildren, getEquivalences, generateTaxonomy, acceptGeneratedTaxonomy } from '@/lib/api'
import { getSectorColor, getSystemColor } from '@/lib/colors'
import { isLoggedIn } from '@/lib/auth'
import type { ClassificationNode, ClassificationSystem, Equivalence, GeneratedNode } from '@/lib/types'

const STORAGE_PREFIX = 'wot:tree:'

function storageKey(systemId: string): string {
  return `${STORAGE_PREFIX}${systemId}`
}

function loadExpanded(systemId: string): Set<string> {
  if (typeof window === 'undefined') return new Set()
  try {
    const raw = window.sessionStorage.getItem(storageKey(systemId))
    if (!raw) return new Set()
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? new Set(arr.filter((s): s is string => typeof s === 'string')) : new Set()
  } catch {
    return new Set()
  }
}

function persistExpanded(systemId: string, expanded: Set<string>): void {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(storageKey(systemId), JSON.stringify(Array.from(expanded)))
  } catch {
    // storage full or blocked; ignore
  }
}

interface NodeRowProps {
  systemId: string
  node: ClassificationNode
  systems: ClassificationSystem[]
  expanded: Set<string>
  toggleExpanded: (code: string) => void
}

function NodeRow({ systemId, node, systems, expanded, toggleExpanded }: NodeRowProps) {
  const isExpanded = expanded.has(node.code)
  const [loggedIn, setLoggedIn] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [loginRequired, setLoginRequired] = useState(false)
  const [suggestions, setSuggestions] = useState<GeneratedNode[] | null>(null)
  const [selected, setSelected] = useState<number[]>([])
  const [accepting, setAccepting] = useState(false)
  const [dismissedCodes, setDismissedCodes] = useState<Set<string>>(new Set())
  const queryClient = useQueryClient()

  useEffect(() => {
    const devMode = typeof window !== 'undefined' && window.location.hostname === 'localhost'
    setLoggedIn(isLoggedIn() || devMode)
  }, [])

  const { data: children, isFetching: loadingChildren } = useQuery({
    queryKey: ['tree-children', systemId, node.code],
    queryFn: () => getChildren(systemId, node.code),
    enabled: isExpanded && !node.is_leaf,
    staleTime: 5 * 60 * 1000,
  })

  const { data: equivalences } = useQuery({
    queryKey: ['equivalences', systemId, node.code],
    queryFn: () => getEquivalences(systemId, node.code),
    enabled: isExpanded,
    staleTime: 5 * 60 * 1000,
  })

  const sectorColor = getSectorColor(node.sector_code ?? node.code)

  const chips: Equivalence[] = []
  if (equivalences) {
    const seen = new Set<string>()
    for (const e of equivalences) {
      if (!seen.has(e.target_system)) {
        seen.add(e.target_system)
        chips.push(e)
        if (chips.length >= 3) break
      }
    }
  }
  const totalSystems = equivalences
    ? new Set(equivalences.map((e) => e.target_system)).size
    : 0
  const hiddenCount = totalSystems - chips.length

  async function handleGenerate(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    if (!loggedIn) {
      setLoginRequired(true)
      setSuggestions(null)
      return
    }
    setLoginRequired(false)
    setGenerating(true)
    try {
      const result = await generateTaxonomy(systemId, node.code)
      const fresh = result.nodes.filter((s) => !dismissedCodes.has(s.code))
      setSuggestions((prev) => {
        if (!prev || prev.length === 0) {
          setSelected(fresh.map((_, i) => i))
          return fresh
        }
        const seen = new Set(prev.map((s) => s.code))
        const merged = [...prev, ...fresh.filter((s) => !seen.has(s.code))]
        const firstNewIdx = prev.length
        const addedIdxs = merged
          .map((_, i) => i)
          .filter((i) => i >= firstNewIdx)
        setSelected((prevSel) => Array.from(new Set([...prevSel, ...addedIdxs])))
        return merged
      })
    } catch {
      setSuggestions((prev) => prev ?? [])
    } finally {
      setGenerating(false)
    }
  }

  function handleDismissItem(idx: number) {
    if (!suggestions) return
    const code = suggestions[idx].code
    setDismissedCodes((prev) => {
      const next = new Set(prev)
      next.add(code)
      return next
    })
    setSuggestions((prev) => (prev ? prev.filter((_, i) => i !== idx) : prev))
    setSelected((prev) =>
      prev.filter((x) => x !== idx).map((x) => (x > idx ? x - 1 : x))
    )
  }

  async function handleAccept() {
    if (!suggestions) return
    const chosen = suggestions.filter((_, i) => selected.includes(i))
    if (chosen.length === 0) return
    setAccepting(true)
    try {
      await acceptGeneratedTaxonomy(systemId, node.code, chosen)
      setSuggestions(null)
      setSelected([])
      queryClient.invalidateQueries({ queryKey: ['tree-children', systemId, node.code] })
      queryClient.invalidateQueries({ queryKey: ['node', systemId, node.code] })
    } finally {
      setAccepting(false)
    }
  }

  function handleToggle(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    if (!node.is_leaf) toggleExpanded(node.code)
  }

  return (
    <div>
      {/* Row */}
      <div className="group flex items-center gap-2 px-2 py-1.5 rounded-lg transition-colors hover:bg-card/70">
        {/* Expand toggle / leaf icon */}
        {!node.is_leaf ? (
          <button
            type="button"
            onClick={handleToggle}
            aria-label={isExpanded ? 'Collapse' : 'Expand'}
            aria-expanded={isExpanded}
            className="w-4 h-4 flex items-center justify-center shrink-0 text-muted-foreground hover:text-foreground cursor-pointer"
          >
            <ChevronRight
              className={`h-3.5 w-3.5 transition-transform duration-150 ${
                isExpanded ? 'rotate-90' : ''
              }`}
            />
          </button>
        ) : (
          <span className="w-4 h-4 flex items-center justify-center shrink-0 text-muted-foreground">
            <Leaf className="h-3 w-3 text-emerald-500/50" />
          </span>
        )}

        {/* Code + title = navigation link */}
        <Link
          href={`/system/${systemId}/node/${encodeURIComponent(node.code)}`}
          className="flex items-center gap-2 flex-1 min-w-0"
          title="Open node detail"
        >
          <span
            className="font-mono text-xs px-1.5 py-0.5 rounded shrink-0"
            style={{ color: sectorColor, backgroundColor: `${sectorColor}18` }}
          >
            {node.code}
          </span>
          <span className="text-sm min-w-0 truncate text-foreground/75 group-hover:text-foreground transition-colors">
            {node.title}
          </span>
        </Link>

        {/* Inline action: magic wand */}
        <button
          type="button"
          onClick={handleGenerate}
          title={loggedIn ? 'Generate AI sub-classifications' : 'Sign in to generate AI sub-classifications'}
          className="shrink-0 flex items-center justify-center hover:scale-110 transition-transform"
          style={{ color: generating ? '#d97706' : '#b8860b' }}
        >
          {generating ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Wand2 className="h-3.5 w-3.5" />
          )}
        </button>

        {/* Equivalence chips */}
        {chips.length > 0 && (
          <div className="hidden sm:flex items-center gap-1 shrink-0">
            {chips.map((e) => {
              const sys = systems.find((s) => s.id === e.target_system)
              const sysColor = getSystemColor(e.target_system)
              const prefix = sys?.name.split(' ')[0] ?? e.target_system.split('_')[0].toUpperCase()
              return (
                <Link
                  key={`${e.target_system}-${e.target_code}`}
                  href={`/system/${e.target_system}/node/${encodeURIComponent(e.target_code)}`}
                  title={`${sys?.name ?? e.target_system}: ${e.target_code}${e.target_title ? ` - ${e.target_title}` : ''} (${e.match_type})`}
                  className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[11px] font-mono hover:opacity-70 transition-opacity"
                  style={{ color: sysColor, backgroundColor: `${sysColor}15` }}
                >
                  <span className="opacity-60">{prefix}</span>
                  <span className="ml-0.5">{e.target_code}</span>
                </Link>
              )
            })}
            {hiddenCount > 0 && (
              <span className="text-[11px] text-muted-foreground">+{hiddenCount}</span>
            )}
          </div>
        )}
      </div>

      {/* Login required panel */}
      {loginRequired && (
        <div className="mx-2 my-1 px-3 py-2 rounded-lg border border-dashed border-purple-500/40 bg-purple-500/5 text-xs text-purple-400/80 flex items-center justify-between">
          <span>
            <Link href="/sign-in" className="underline hover:text-purple-300">Sign in</Link>
            {' '}to generate AI sub-classifications
          </span>
          <button
            onClick={() => setLoginRequired(false)}
            className="ml-3 text-muted-foreground hover:text-foreground"
          >
            x
          </button>
        </div>
      )}

      {/* AI suggestion panel */}
      {suggestions !== null && (
        <div className="mx-2 my-1 rounded-lg border border-dashed border-purple-500/40 bg-purple-500/5">
          <div className="px-3 py-2 border-b border-purple-500/20 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-purple-400/70">
              AI-Suggested Sub-classifications
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSelected(suggestions.map((_, i) => i))}
                className="text-[11px] text-purple-400/60 hover:text-purple-300"
              >
                All
              </button>
              <button
                onClick={() => {
                  setSuggestions(null)
                  setSelected([])
                  setDismissedCodes(new Set())
                }}
                className="text-[11px] text-muted-foreground hover:text-foreground"
              >
                Dismiss
              </button>
            </div>
          </div>

          {suggestions.length === 0 ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">No suggestions returned.</div>
          ) : (
            <>
              <ul className="px-3 py-1 space-y-0.5">
                {suggestions.map((s, i) => (
                  <li key={s.code} className="flex items-start gap-2 py-1 group/sug">
                    <input
                      type="checkbox"
                      checked={selected.includes(i)}
                      onChange={() =>
                        setSelected((prev) =>
                          prev.includes(i) ? prev.filter((x) => x !== i) : [...prev, i]
                        )
                      }
                      className="mt-0.5 shrink-0 accent-purple-500"
                    />
                    <span
                      className="font-mono text-[11px] px-1.5 py-0.5 rounded shrink-0"
                      style={{ color: '#a855f7', backgroundColor: '#a855f718' }}
                    >
                      {s.code}
                    </span>
                    <div className="flex-1 min-w-0">
                      <span className="text-xs text-foreground/80">{s.title}</span>
                      {s.reason && (
                        <p className="text-[11px] text-muted-foreground/80 mt-0.5 italic leading-snug">
                          {s.reason}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDismissItem(i)}
                      title="Reject this suggestion (kept dismissed for this session)"
                      className="shrink-0 text-muted-foreground/50 hover:text-rose-400 opacity-0 group-hover/sug:opacity-100 transition-opacity text-xs px-1"
                    >
                      x
                    </button>
                  </li>
                ))}
              </ul>

              <div className="px-3 pb-2 pt-1">
                <button
                  onClick={handleAccept}
                  disabled={selected.length === 0 || accepting}
                  className="px-3 py-1 rounded text-xs bg-purple-600/80 hover:bg-purple-600 text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
                >
                  {accepting && <Loader2 className="h-3 w-3 animate-spin" />}
                  Accept {selected.length > 0 ? selected.length : ''}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Children with guide line */}
      {isExpanded && !node.is_leaf && (
        <div className="ml-3 pl-3 border-l border-border/25">
          {loadingChildren ? (
            <div className="py-2 pl-1 text-xs text-muted-foreground animate-pulse">
              Loading...
            </div>
          ) : children && children.length > 0 ? (
            children.map((child) => (
              <NodeRow
                key={child.code}
                systemId={systemId}
                node={child}
                systems={systems}
                expanded={expanded}
                toggleExpanded={toggleExpanded}
              />
            ))
          ) : (
            <div className="py-2 pl-1 text-xs text-muted-foreground">
              No sub-classifications
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function NodeTree({
  systemId,
  roots,
  systems,
}: {
  systemId: string
  roots: ClassificationNode[]
  systems: ClassificationSystem[]
}) {
  const [expanded, setExpanded] = useState<Set<string>>(() => loadExpanded(systemId))

  useEffect(() => {
    persistExpanded(systemId, expanded)
  }, [systemId, expanded])

  const toggleExpanded = useCallback((code: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(code)) {
        next.delete(code)
      } else {
        next.add(code)
      }
      return next
    })
  }, [])

  return (
    <div className="rounded-xl border border-border/50 bg-card/20 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2.5 border-b border-border/40 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Hierarchy Explorer
        </span>
        <span className="text-xs text-muted-foreground hidden sm:block">
          Chevron to expand - click title to open
        </span>
      </div>

      {/* Rows */}
      <div className="p-2">
        {roots.map((root) => (
          <NodeRow
            key={root.code}
            systemId={systemId}
            node={root}
            systems={systems}
            expanded={expanded}
            toggleExpanded={toggleExpanded}
          />
        ))}
      </div>
    </div>
  )
}

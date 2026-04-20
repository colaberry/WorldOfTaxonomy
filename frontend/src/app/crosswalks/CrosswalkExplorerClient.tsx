'use client'

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import type { CrosswalkSectionsResponse, CrosswalkGraphResponse } from '@/lib/types'

async function fetchLocalGraph(
  source: string, target: string, limit = 1000, section?: string,
): Promise<CrosswalkGraphResponse> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (section) params.set('section', section)
  const res = await fetch(`/api/crosswalk/${source}/${target}/graph?${params}`)
  return res.json()
}
import type {
  CrosswalkGraphHandle,
  SelectedSystemNode,
} from '@/components/visualizations/CrosswalkGraph'
import { getCategoryForSystem } from '@/lib/categories'
import type { ClassificationSystem, CrosswalkStat } from '@/lib/types'
import {
  Network, GitCompareArrows, Loader2, ChevronDown, ArrowLeft,
  Search, X, ExternalLink, ChevronRight, Layers,
} from 'lucide-react'

type Mode = 'system' | 'sections' | 'code'

const SECTION_THRESHOLD = 50 // Show sections view when total edges exceed this

interface Props {
  systems: ClassificationSystem[]
  stats: CrosswalkStat[]
  allSections: Record<string, CrosswalkSectionsResponse>
  initialSource?: string
  initialTarget?: string
}

export default function CrosswalkExplorerClient({ systems, stats, allSections, initialSource, initialTarget }: Props) {
  const router = useRouter()
  const graphRef = useRef<CrosswalkGraphHandle>(null)
  const [mode, setMode] = useState<Mode>('system')
  const [sourceSystem, setSourceSystem] = useState(initialSource ?? '')
  const [targetSystem, setTargetSystem] = useState(initialTarget ?? '')
  const [loadPair, setLoadPair] = useState<{ source: string; target: string } | null>(
    initialSource && initialTarget ? { source: initialSource, target: initialTarget } : null,
  )
  const [activeSection, setActiveSection] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState<SelectedSystemNode | null>(null)

  // Lazy-load Cytoscape.js (~300KB) - shell paints immediately, graph loads after
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [GraphComp, setGraphComp] = useState<any>(null)
  useEffect(() => {
    import('@/components/visualizations/CrosswalkGraph').then(mod => {
      setGraphComp(() => mod.CrosswalkGraph)
    })
  }, [])

  // Systems pre-filtered server-side, just sort for dropdowns
  const crosswalkedSystems = useMemo(() => {
    return [...systems].sort((a, b) => a.name.localeCompare(b.name))
  }, [systems])

  // Search results filtered from crosswalked systems
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return []
    const q = searchQuery.toLowerCase()
    return crosswalkedSystems
      .filter((s) => s.name.toLowerCase().includes(q) || s.id.toLowerCase().includes(q))
      .slice(0, 8)
  }, [searchQuery, crosswalkedSystems])

  // Available targets for chosen source
  const availableTargets = useMemo(() => {
    if (!sourceSystem) return []
    const targets = new Set<string>()
    for (const st of stats) {
      if (st.source_system === sourceSystem) targets.add(st.target_system)
      if (st.target_system === sourceSystem) targets.add(st.source_system)
    }
    return crosswalkedSystems.filter((s) => targets.has(s.id))
  }, [sourceSystem, stats, crosswalkedSystems])

  // Sections: instant lookup from props (no network request)
  const sectionsData = loadPair
    ? (allSections[`${loadPair.source}___${loadPair.target}`]
      ?? allSections[`${loadPair.target}___${loadPair.source}`]
      ?? null)
    : null
  const sectionsLoading = false

  // Pre-warm graph route handler while user reads sections table
  useEffect(() => {
    if (loadPair) {
      fetch(`/api/crosswalk/${loadPair.source}/${loadPair.target}/graph?limit=1`).catch(() => {})
    }
  }, [loadPair])

  // Code-level graph query (with optional section filter)
  const {
    data: graphData,
    isLoading: graphLoading,
    error: graphError,
  } = useQuery({
    queryKey: ['crosswalk-graph', loadPair?.source, loadPair?.target, activeSection],
    queryFn: () => fetchLocalGraph(
      loadPair!.source,
      loadPair!.target,
      1000,
      activeSection ?? undefined,
    ),
    enabled: !!loadPair && (!!activeSection || mode === 'code'),
  })

  function handleEdgeClick(source: string, target: string) {
    setSourceSystem(source)
    setTargetSystem(target)
    setLoadPair({ source, target })
    setActiveSection(null)
    setMode('sections')
    setSelectedNode(null)
  }

  function handleLoadGraph() {
    if (sourceSystem && targetSystem) {
      setLoadPair({ source: sourceSystem, target: targetSystem })
      setActiveSection(null)
      setMode('sections')
    }
  }

  function handleSectionClick(sectionCode: string) {
    // Accordion toggle: click same section to collapse, different to expand
    setActiveSection((prev) => (prev === sectionCode ? null : sectionCode))
  }

  function handleBackToSystem() {
    setMode('system')
    setLoadPair(null)
    setSelectedNode(null)
    setActiveSection(null)
  }

  function handleNodeClick(system: string, code: string) {
    router.push(`/system/${system}/node/${encodeURIComponent(code)}`)
  }

  const handleNodeSelect = useCallback((node: SelectedSystemNode | null) => {
    setSelectedNode(node)
  }, [])

  function handleSearchSelect(systemId: string) {
    setSearchQuery('')
    graphRef.current?.focusNode(systemId)
  }

  // Auto-switch: when sections data loads, decide whether to show sections or go straight to code
  const shouldShowSections = sectionsData && sectionsData.total_edges > SECTION_THRESHOLD
  if (mode === 'sections' && sectionsData && !shouldShowSections && !sectionsLoading) {
    if (mode === 'sections') {
      setTimeout(() => {
        setActiveSection(null)
        setMode('code')
      }, 0)
    }
  }

  const sourceName = systems.find((s) => s.id === (loadPair?.source ?? sourceSystem))?.name ?? loadPair?.source ?? sourceSystem
  const targetName = systems.find((s) => s.id === (loadPair?.target ?? targetSystem))?.name ?? loadPair?.target ?? targetSystem
  const activeSectionTitle = activeSection && sectionsData
    ? sectionsData.sections.find((s) => s.source_section === activeSection)?.source_title ?? activeSection
    : activeSection

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Header bar */}
      <div className="border-b border-border/50 bg-card/80 backdrop-blur-sm px-4 sm:px-6 py-3">
        <div className="max-w-7xl mx-auto space-y-3">
          {/* Row 1: Title + mode toggle + stats */}
          <div className="flex items-center gap-3 flex-wrap">
            {mode !== 'system' && (
              <button
                onClick={handleBackToSystem}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                title="Back to system graph"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="hidden sm:inline">Back</span>
              </button>
            )}
            <h1 className="text-lg font-semibold tracking-tight">
              Crosswalk Explorer
            </h1>

            {/* Breadcrumb context */}
            {mode !== 'system' && loadPair && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span className="hidden sm:inline">{sourceName}</span>
                <ChevronRight className="h-3 w-3 hidden sm:block" />
                <span className="hidden sm:inline">{targetName}</span>
                {activeSection && (
                  <>
                    <ChevronRight className="h-3 w-3" />
                    <span className="text-foreground font-medium">{activeSectionTitle}</span>
                  </>
                )}
              </div>
            )}

            {/* Mode toggle */}
            <div className="flex rounded-lg border border-border/50 overflow-hidden text-xs">
              <button
                className={`px-3 py-1.5 transition-colors ${
                  mode === 'system'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card text-muted-foreground hover:text-foreground'
                }`}
                onClick={() => { setMode('system'); setLoadPair(null); setSelectedNode(null); setActiveSection(null) }}
              >
                <Network className="h-3.5 w-3.5 inline mr-1" />
                Systems
              </button>
              <button
                className={`px-3 py-1.5 transition-colors ${
                  mode === 'sections' || mode === 'code'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-card text-muted-foreground hover:text-foreground'
                }`}
                onClick={() => {
                  if (loadPair) {
                    setMode(shouldShowSections ? 'sections' : 'code')
                  } else {
                    setMode('sections')
                  }
                }}
              >
                <GitCompareArrows className="h-3.5 w-3.5 inline mr-1" />
                Code-level
              </button>
            </div>

            {/* System mode: search box */}
            {mode === 'system' && (
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Find a system..."
                  className="pl-8 pr-8 py-1.5 rounded-md bg-secondary border border-border/50 text-sm w-52 focus:outline-none focus:ring-2 focus:ring-primary/50 placeholder:text-muted-foreground/60"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
                {searchResults.length > 0 && (
                  <div className="absolute top-full left-0 mt-1 w-72 bg-popover border border-border/50 rounded-lg shadow-lg z-30 py-1 max-h-64 overflow-y-auto">
                    {searchResults.map((s) => {
                      const cat = getCategoryForSystem(s.id)
                      return (
                        <button
                          key={s.id}
                          onClick={() => handleSearchSelect(s.id)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-secondary/50 transition-colors text-left"
                        >
                          <span
                            className="w-2.5 h-2.5 rounded-sm shrink-0"
                            style={{ backgroundColor: s.tint_color || cat.accent }}
                          />
                          <span className="truncate flex-1">{s.name}</span>
                          <span className="text-[10px] font-mono text-muted-foreground shrink-0">
                            {s.node_count >= 1000
                              ? `${(s.node_count / 1000).toFixed(0)}k`
                              : s.node_count}
                          </span>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Stats badges */}
            <div className="sm:ml-auto text-xs text-muted-foreground">
              {mode === 'system' && (
                <>
                  {new Set([...stats.map((s) => s.source_system), ...stats.map((s) => s.target_system)]).size} systems
                  {' - '}
                  {stats.reduce((sum, s) => sum + s.edge_count, 0).toLocaleString()} edges
                </>
              )}
              {mode === 'sections' && sectionsData && !activeSection && (
                <>
                  {sectionsData.sections.length} sections - {sectionsData.total_edges.toLocaleString()} total edges
                </>
              )}
              {mode === 'sections' && activeSection && graphData && (
                <>
                  {graphData.nodes.length} nodes, {graphData.edges.length} edges
                  {graphData.truncated && ` (${graphData.total_edges} total)`}
                </>
              )}
              {mode === 'code' && graphData && (
                <>
                  {graphData.nodes.length} nodes, {graphData.edges.length} edges
                  {graphData.truncated && ` (${graphData.total_edges} total)`}
                </>
              )}
            </div>
          </div>

          {/* Row 2: Load graph controls - always visible */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="relative">
              <select
                value={sourceSystem}
                onChange={(e) => {
                  setSourceSystem(e.target.value)
                  setTargetSystem('')
                  setLoadPair(null)
                }}
                className="appearance-none pl-3 pr-7 py-1.5 rounded-md bg-secondary border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 cursor-pointer min-w-[180px]"
              >
                <option value="">Source system...</option>
                {crosswalkedSystems.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            </div>

            <span className="text-muted-foreground text-xs">to</span>

            <div className="relative">
              <select
                value={targetSystem}
                onChange={(e) => {
                  setTargetSystem(e.target.value)
                  setLoadPair(null)
                }}
                disabled={!sourceSystem}
                className="appearance-none pl-3 pr-7 py-1.5 rounded-md bg-secondary border border-border/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 cursor-pointer disabled:opacity-50 min-w-[180px]"
              >
                <option value="">Target system...</option>
                {availableTargets.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            </div>

            <button
              onClick={handleLoadGraph}
              disabled={!sourceSystem || !targetSystem}
              className="px-4 py-1.5 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Load graph
            </button>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 relative bg-background">
        {/* SYSTEM MODE: Ring visualization */}
        {mode === 'system' && GraphComp ? (
          <GraphComp
            ref={graphRef}
            mode="system"
            systems={systems}
            stats={stats}
            onEdgeClick={handleEdgeClick}
            onNodeSelect={handleNodeSelect}
          />
        ) : mode === 'system' ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Loading visualization...</span>
          </div>
        ) : null}

        {/* SECTIONS MODE: Table of section groupings */}
        {mode === 'sections' && sectionsLoading && (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Loading sections...</span>
          </div>
        )}

        {mode === 'sections' && !sectionsLoading && !loadPair && (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <GitCompareArrows className="h-10 w-10 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              Select two systems above and click &ldquo;Load graph&rdquo; to visualize crosswalk edges.
            </p>
          </div>
        )}

        {mode === 'sections' && sectionsData && shouldShowSections && (
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6">
            <div className="flex items-center gap-2 mb-4">
              <Layers className="h-4 w-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold">
                {sectionsData.total_edges.toLocaleString()} edges grouped into {sectionsData.sections.length} sections
              </h2>
              <span className="text-xs text-muted-foreground">- click a section to explore its mappings</span>
            </div>
            <div className="border border-border/50 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-card/50 border-b border-border/50">
                    <th className="text-left px-4 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wider">
                      {sourceName}
                    </th>
                    <th className="text-left px-4 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wider">
                      {targetName}
                    </th>
                    <th className="text-right px-4 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wider">
                      Edges
                    </th>
                    <th className="text-right px-4 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wider">
                      Match
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {sectionsData.sections.map((sec) => {
                    const exactPct = sec.edge_count > 0 ? Math.round((sec.exact_count / sec.edge_count) * 100) : 0
                    const isExpanded = activeSection === sec.source_section
                    return (
                      <React.Fragment key={`${sec.source_section}-${sec.target_section}`}>
                        <tr
                          onClick={() => handleSectionClick(sec.source_section)}
                          className={`cursor-pointer transition-colors group ${
                            isExpanded ? 'bg-secondary/70' : 'hover:bg-secondary/50'
                          }`}
                        >
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <ChevronRight className={`h-3.5 w-3.5 text-muted-foreground transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                              <span className="font-mono text-xs text-primary/80">{sec.source_section}</span>
                              <span className="text-foreground group-hover:text-primary transition-colors">{sec.source_title}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs text-primary/80">{sec.target_section}</span>
                              <span className="text-muted-foreground">{sec.target_title}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className="font-mono text-sm">{sec.edge_count.toLocaleString()}</span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              exactPct === 100 ? 'bg-emerald-500/10 text-emerald-400' :
                              exactPct >= 50 ? 'bg-amber-500/10 text-amber-400' :
                              'bg-blue-500/10 text-blue-400'
                            }`}>
                              {exactPct}% exact
                            </span>
                          </td>
                        </tr>
                        {isExpanded && (
                          <tr>
                            <td colSpan={4} className="p-0">
                              <div className="border-t border-border/30" style={{ height: 500 }}>
                                {graphLoading || !GraphComp ? (
                                  <div className="flex items-center justify-center h-full">
                                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                    <span className="ml-2 text-sm text-muted-foreground">Loading graph...</span>
                                  </div>
                                ) : graphError ? (
                                  <div className="flex items-center justify-center h-full">
                                    <p className="text-sm text-destructive">Failed to load graph.</p>
                                  </div>
                                ) : graphData && graphData.edges.length > 0 ? (
                                  <GraphComp
                                    mode="code"
                                    data={graphData}
                                    onNodeClick={handleNodeClick}
                                  />
                                ) : (
                                  <div className="flex items-center justify-center h-full">
                                    <p className="text-sm text-muted-foreground">No crosswalk edges in this section.</p>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* CODE MODE: Full graph for small crosswalks (< SECTION_THRESHOLD edges) */}
        {mode === 'code' && (graphLoading || !GraphComp) && (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Loading crosswalk graph...</span>
          </div>
        )}

        {mode === 'code' && graphError && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-destructive">
              Failed to load graph. Please try another pair.
            </p>
          </div>
        )}

        {mode === 'code' && graphData && graphData.edges.length > 0 && GraphComp && (
          <GraphComp
            mode="code"
            data={graphData}
            onNodeClick={handleNodeClick}
          />
        )}

        {mode === 'code' && graphData && graphData.edges.length === 0 && !graphLoading && (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <GitCompareArrows className="h-10 w-10 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              No crosswalk edges found.
            </p>
          </div>
        )}

        {/* Selected node info panel (system mode) */}
        {mode === 'system' && selectedNode && (
          <div className="absolute bottom-3 left-3 z-10 bg-card/95 border border-border/50 rounded-lg shadow-lg p-4 w-80 max-h-[50vh] overflow-y-auto">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold">{selectedNode.name}</h3>
                <p className="text-[11px] text-muted-foreground">
                  {selectedNode.nodeCount.toLocaleString()} nodes - {selectedNode.category}
                </p>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => router.push(`/system/${selectedNode.id}`)}
                  className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                  title="View system"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => {
                    setSelectedNode(null)
                    graphRef.current?.resetView()
                  }}
                  className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                  title="Close"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div className="space-y-1.5">
              <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">
                Connected systems ({selectedNode.connectedSystems.length})
              </p>
              {selectedNode.connectedSystems.map((conn) => (
                <button
                  key={conn.id}
                  onClick={() => handleEdgeClick(selectedNode.id, conn.id)}
                  className="w-full flex items-center justify-between gap-2 px-2 py-1.5 rounded-md text-left hover:bg-secondary/50 transition-colors group"
                >
                  <span className="text-xs truncate">{conn.name}</span>
                  <span className="text-[10px] font-mono text-muted-foreground shrink-0 group-hover:text-primary transition-colors">
                    {conn.edgeCount.toLocaleString()} edges
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Hint overlay (system mode) */}
        {mode === 'system' && !selectedNode && (
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 z-10 bg-card/90 border border-border/50 rounded-lg px-4 py-2 text-xs text-muted-foreground pointer-events-none">
            Click a system to see connections - click an edge for code-level mappings
          </div>
        )}
      </div>
    </div>
  )
}

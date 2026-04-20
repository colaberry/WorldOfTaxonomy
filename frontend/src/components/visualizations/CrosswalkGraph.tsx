'use client'

import {
  useRef, useEffect, useCallback, useImperativeHandle, forwardRef,
} from 'react'
import { useTheme } from 'next-themes'
import cytoscape from 'cytoscape'
import type {
  ClassificationSystem,
  CrosswalkStat,
  CrosswalkGraphResponse,
} from '@/lib/types'
import { getCategoryForSystem, SYSTEM_CATEGORIES } from '@/lib/categories'
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

// -- Public types ----------------------------------------------------------

export interface SelectedSystemNode {
  id: string
  name: string
  nodeCount: number
  category: string
  connectedSystems: { id: string; name: string; edgeCount: number }[]
}

interface SystemGraphProps {
  mode: 'system'
  systems: ClassificationSystem[]
  stats: CrosswalkStat[]
  onEdgeClick?: (source: string, target: string) => void
  onNodeSelect?: (node: SelectedSystemNode | null) => void
  topN?: number
}

interface CodeGraphProps {
  mode: 'code'
  data: CrosswalkGraphResponse
  onNodeClick?: (system: string, code: string) => void
}

type Props = SystemGraphProps | CodeGraphProps

export interface CrosswalkGraphHandle {
  focusNode: (id: string) => void
  resetView: () => void
}

// -- Helpers ---------------------------------------------------------------

function getCategoryColor(systemId: string): string {
  return getCategoryForSystem(systemId).accent
}

function logSize(count: number, min: number, max: number): number {
  if (count <= 0) return min
  const v = Math.log10(count + 1)
  return Math.max(min, Math.min(max, min + v * ((max - min) / 6)))
}

// -- Position: ring of all crosswalked systems, grouped by category --------

function computeSystemRingPositions(
  systems: ClassificationSystem[],
  stats: CrosswalkStat[],
  w: number,
  h: number,
) {
  const statsIds = new Set<string>()
  for (const st of stats) { statsIds.add(st.source_system); statsIds.add(st.target_system) }

  const crosswalked = systems.filter((s) => statsIds.has(s.id))

  // Group by category for adjacency on the ring
  const byCategory = new Map<string, ClassificationSystem[]>()
  for (const s of crosswalked) {
    const cat = getCategoryForSystem(s.id)
    let arr = byCategory.get(cat.id)
    if (!arr) { arr = []; byCategory.set(cat.id, arr) }
    arr.push(s)
  }

  // Sort in SYSTEM_CATEGORIES order so ring ordering is stable and predictable
  const catOrder = SYSTEM_CATEGORIES.map((c) => c.id)
  const catEntries = Array.from(byCategory.entries())
    .sort((a, b) => catOrder.indexOf(a[0]) - catOrder.indexOf(b[0]))

  const ordered: ClassificationSystem[] = []
  for (const [, catSystems] of catEntries) {
    catSystems.sort((a, b) => b.node_count - a.node_count)
    ordered.push(...catSystems)
  }

  const cx = w / 2
  const cy = h / 2
  const R = Math.min(w, h) * 0.42
  const positions = new Map<string, { x: number; y: number }>()
  const n = ordered.length

  ordered.forEach((s, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2
    positions.set(s.id, { x: cx + R * Math.cos(angle), y: cy + R * Math.sin(angle) })
  })

  return { positions, ordered }
}

// -- Component -------------------------------------------------------------

export const CrosswalkGraph = forwardRef<CrosswalkGraphHandle, Props>(
  function CrosswalkGraph(props, ref) {
    const containerRef = useRef<HTMLDivElement>(null)
    const tooltipRef = useRef<HTMLDivElement>(null)
    const cyRef = useRef<cytoscape.Core | null>(null)
    const { resolvedTheme } = useTheme()
    const isDark = resolvedTheme === 'dark'

    // Stable ref to avoid re-render loops from callback props
    const propsRef = useRef(props)
    propsRef.current = props

    // -- Tooltip via DOM (no React state / no re-render) --

    function showTooltip(x: number, y: number, title: string, lines?: string[]) {
      const el = tooltipRef.current
      if (!el) return
      el.style.display = 'block'
      el.style.left = `${x}px`
      el.style.top = `${y}px`
      let html = `<div class="font-medium">${title}</div>`
      if (lines) {
        for (const line of lines) {
          html += `<div class="text-muted-foreground">${line}</div>`
        }
      }
      el.innerHTML = html
    }

    function hideTooltip() {
      const el = tooltipRef.current
      if (el) el.style.display = 'none'
    }

    // -- Highlight helpers --

    function highlightNeighborhood(cy: cytoscape.Core, node: cytoscape.NodeSingular) {
      const hood = node.closedNeighborhood()
      cy.elements().addClass('dimmed').removeClass('highlighted')
      hood.removeClass('dimmed').addClass('highlighted')
      node.addClass('focused')
    }

    function clearHighlight(cy: cytoscape.Core) {
      cy.elements().removeClass('dimmed highlighted focused')
    }

    function buildSelectedInfo(cy: cytoscape.Core, node: cytoscape.NodeSingular): SelectedSystemNode {
      const connected: SelectedSystemNode['connectedSystems'] = []
      node.connectedEdges().forEach((edge) => {
        const other = edge.source().id() === node.id() ? edge.target() : edge.source()
        connected.push({
          id: other.id(),
          name: other.data('label'),
          edgeCount: edge.data('edgeCount') ?? 0,
        })
      })
      connected.sort((a, b) => b.edgeCount - a.edgeCount)
      return {
        id: node.id(),
        name: node.data('label'),
        nodeCount: node.data('nodeCount') ?? 0,
        category: node.data('categoryLabel') ?? '',
        connectedSystems: connected,
      }
    }

    // -- Imperative handle (search focus, reset) --

    useImperativeHandle(ref, () => ({
      focusNode(id: string) {
        const cy = cyRef.current
        if (!cy) return
        const node = cy.getElementById(id)
        if (node.empty()) return
        highlightNeighborhood(cy, node)
        cy.animate({ center: { eles: node }, zoom: 1.5 }, { duration: 400 })
        if (propsRef.current.mode === 'system' && propsRef.current.onNodeSelect) {
          propsRef.current.onNodeSelect(buildSelectedInfo(cy, node))
        }
      },
      resetView() {
        const cy = cyRef.current
        if (!cy) return
        clearHighlight(cy)
        cy.animate({ fit: { eles: cy.elements(), padding: 30 } }, { duration: 300 })
      },
    }))

    // -- Build & render Cytoscape --

    useEffect(() => {
      const container = containerRef.current
      if (!container) return

      const rect = container.getBoundingClientRect()
      const w = rect.width || 1200
      const h = rect.height || 700

      const bgColor = isDark ? '#09090b' : '#ffffff'
      const textColor = isDark ? '#fafafa' : '#09090b'
      const edgeColor = isDark ? 'rgba(161,161,170,0.28)' : 'rgba(113,113,122,0.32)'
      const edgeHighlight = isDark ? '#818cf8' : '#6366f1'
      const dimOpacity = 0.08

      const p = propsRef.current

      // ================================================================
      // CODE-LEVEL GRAPH
      // ================================================================
      if (p.mode === 'code') {
        const { data } = p
        const elements: cytoscape.ElementDefinition[] = []

        for (const node of data.nodes) {
          const isSource = node.system === data.source_system
          elements.push({
            group: 'nodes',
            data: {
              id: node.id, shortLabel: node.code, system: node.system,
              code: node.code, title: node.title,
              color: getCategoryColor(node.system), isSource,
            },
          })
        }
        for (let i = 0; i < data.edges.length; i++) {
          const edge = data.edges[i]
          elements.push({
            group: 'edges',
            data: { id: `edge_${i}`, source: edge.source, target: edge.target, matchType: edge.match_type },
          })
        }

        if (elements.length === 0) return

        const cy = cytoscape({
          container,
          elements,
          style: [
            {
              selector: 'node',
              style: {
                'background-color': 'data(color)', 'background-opacity': 0.9,
                label: 'data(shortLabel)', 'text-valign': 'bottom', 'text-halign': 'center',
                'font-size': '11px', color: textColor, width: 34, height: 34,
                'border-width': 2, 'border-color': bgColor,
                'text-outline-color': bgColor, 'text-outline-width': 2, 'text-margin-y': 5,
              } as cytoscape.Css.Node,
            },
            {
              selector: 'node[?isSource]',
              style: {
                shape: 'round-rectangle' as cytoscape.Css.NodeShape, width: 44, height: 44, 'font-size': '12px',
              } as cytoscape.Css.Node,
            },
            {
              selector: 'edge',
              style: { 'line-color': edgeColor, 'curve-style': 'bezier', width: 2.5, opacity: 1 } as cytoscape.Css.Edge,
            },
            { selector: 'edge[matchType="exact"]', style: { 'line-color': '#22c55e', width: 3 } as cytoscape.Css.Edge },
            { selector: 'edge[matchType="partial"]', style: { 'line-color': '#f59e0b', width: 2.5 } as cytoscape.Css.Edge },
            { selector: 'edge[matchType="broad"]', style: { 'line-color': '#3b82f6', width: 2 } as cytoscape.Css.Edge },
          ] as cytoscape.StylesheetStyle[],
          layout: {
            name: 'cose', animate: false,
            nodeRepulsion: () => 12000, idealEdgeLength: () => 100,
            gravity: 0.4, numIter: 400, padding: 40, nodeDimensionsIncludeLabels: true,
          },
          minZoom: 0.05, maxZoom: 6, wheelSensitivity: 0.3,
        })

        cy.on('layoutstop', () => { cy.fit(undefined, 30); cy.nodes().lock() })

        cy.on('mouseover', 'node', (evt) => {
          const node = evt.target; const pos = node.renderedPosition()
          container.style.cursor = 'pointer'
          showTooltip(pos.x, pos.y - 28, `${node.data('system')}: ${node.data('code')}`, [node.data('title'), 'Click to view details'])
        })
        cy.on('mouseout', 'node', () => { hideTooltip(); container.style.cursor = 'default' })

        if (p.onNodeClick) {
          const onNodeClick = p.onNodeClick
          cy.on('tap', 'node', (evt) => {
            const node = evt.target
            if (node.data('system') && node.data('code')) onNodeClick(node.data('system'), node.data('code'))
          })
        }

        cyRef.current = cy
        return () => { cy.destroy(); cyRef.current = null; hideTooltip() }
      }

      // ================================================================
      // SYSTEM MODE: ring of all crosswalked systems
      // ================================================================
      const { systems, stats, topN } = p
      let filteredSystems = systems
      let filteredStats = stats
      if (topN && topN > 0) {
        const degree = new Map<string, number>()
        for (const st of stats) {
          degree.set(st.source_system, (degree.get(st.source_system) ?? 0) + st.edge_count)
          degree.set(st.target_system, (degree.get(st.target_system) ?? 0) + st.edge_count)
        }
        const top = new Set(
          systems
            .filter((s) => degree.has(s.id))
            .sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0))
            .slice(0, topN)
            .map((s) => s.id),
        )
        filteredSystems = systems.filter((s) => top.has(s.id))
        filteredStats = stats.filter((st) => top.has(st.source_system) && top.has(st.target_system))
      }
      const { positions, ordered } = computeSystemRingPositions(filteredSystems, filteredStats, w, h)
      const elements: cytoscape.ElementDefinition[] = []

      for (const s of ordered) {
        const cat = getCategoryForSystem(s.id)
        const size = logSize(s.node_count, 10, 18)
        elements.push({
          group: 'nodes',
          data: {
            id: s.id, label: s.name, nodeCount: s.node_count,
            color: s.tint_color || cat.accent, categoryLabel: cat.label,
            systemId: s.id, size,
          },
          position: positions.get(s.id),
        })
      }

      // Edges from stats (deduped: each pair appears once)
      const nodeIds = new Set(ordered.map((s) => s.id))
      const edgeMap = new Map<string, {
        source: string; target: string; count: number; exact: number; partial: number
      }>()
      for (const st of stats) {
        if (!nodeIds.has(st.source_system) || !nodeIds.has(st.target_system)) continue
        const key = [st.source_system, st.target_system].sort().join('|')
        const existing = edgeMap.get(key)
        if (existing) {
          existing.count += st.edge_count
          existing.exact += st.exact_count
          existing.partial += st.partial_count
        } else {
          edgeMap.set(key, {
            source: st.source_system, target: st.target_system,
            count: st.edge_count, exact: st.exact_count, partial: st.partial_count,
          })
        }
      }
      for (const [key, edge] of edgeMap) {
        elements.push({
          group: 'edges',
          data: {
            id: `se_${key}`, source: edge.source, target: edge.target,
            edgeCount: edge.count, exact: edge.exact, partial: edge.partial,
            weight: Math.max(1, Math.log2(edge.count + 1)),
          },
        })
      }

      if (elements.length === 0) return

      const cy = cytoscape({
        container,
        elements,
        style: [
          {
            selector: 'node',
            style: {
              'background-color': 'data(color)', 'background-opacity': 0.85,
              width: 'data(size)', height: 'data(size)',
              'border-width': 1.5, 'border-color': bgColor, 'border-opacity': 0.6,
              label: '', // clean ring - names appear on hover/click
              'transition-property': 'opacity, border-color, border-width',
              'transition-duration': 200,
            } as cytoscape.Css.Node,
          },
          {
            selector: 'edge',
            style: {
              'line-color': edgeColor, 'curve-style': 'straight',
              width: 'mapData(weight, 1, 16, 0.6, 2.4)', opacity: 0.9,
              'target-arrow-shape': 'none',
              'transition-property': 'opacity, line-color, width',
              'transition-duration': 200,
            } as cytoscape.Css.Edge,
          },
          // Dimmed / highlighted / focused states
          { selector: '.dimmed', style: { opacity: dimOpacity } as cytoscape.Css.Node },
          { selector: '.highlighted', style: { opacity: 1 } as cytoscape.Css.Node },
          {
            selector: 'node.highlighted',
            style: {
              opacity: 1,
              label: 'data(label)', 'font-size': '9px', color: textColor,
              'text-outline-color': bgColor, 'text-outline-width': 1.5,
              'text-valign': 'center', 'text-halign': 'center',
              'text-wrap': 'wrap', 'text-max-width': '80px',
            } as cytoscape.Css.Node,
          },
          {
            selector: 'edge.highlighted',
            style: { 'line-color': edgeHighlight, opacity: 0.8, width: 4 } as cytoscape.Css.Edge,
          },
          {
            selector: '.focused',
            style: {
              'border-width': 3, 'border-color': edgeHighlight, 'border-opacity': 1,
              opacity: 1, 'z-index': 20,
              label: 'data(label)', 'font-size': '11px', 'font-weight': 600,
              color: textColor,
              'text-outline-color': bgColor, 'text-outline-width': 2.5,
              'text-valign': 'center', 'text-halign': 'center',
              'text-wrap': 'wrap', 'text-max-width': '100px',
            } as cytoscape.Css.Node,
          },
        ] as cytoscape.StylesheetStyle[],
        layout: { name: 'preset' },
        minZoom: 0.1, maxZoom: 5, wheelSensitivity: 0.3,
      })

      cy.nodes().lock()
      cy.fit(undefined, 40)

      // -- Hover: tooltip on node --
      cy.on('mouseover', 'node', (evt) => {
        const node = evt.target; const pos = node.renderedPosition()
        container.style.cursor = 'pointer'
        const nc = node.data('nodeCount')
        const degree = node.connectedEdges().length
        showTooltip(pos.x, pos.y - (node.data('size') / 2 + 14), node.data('label'), [
          `${nc?.toLocaleString()} nodes`,
          node.data('categoryLabel'),
          `${degree} crosswalk connections`,
          'Click to highlight connections',
        ])
      })
      cy.on('mouseout', 'node', () => { hideTooltip(); container.style.cursor = 'default' })

      // -- Hover: tooltip on edge --
      cy.on('mouseover', 'edge', (evt) => {
        const edge = evt.target; const midpoint = edge.midpoint()
        const zoom = cy.zoom(); const pan = cy.pan()
        const rx = midpoint.x * zoom + pan.x; const ry = midpoint.y * zoom + pan.y
        container.style.cursor = 'pointer'
        const src = edge.source().data('label'); const tgt = edge.target().data('label')
        showTooltip(rx, ry - 10, `${src} / ${tgt}`, [
          `${edge.data('edgeCount')?.toLocaleString()} crosswalk edges`,
          `${edge.data('exact')?.toLocaleString()} exact, ${edge.data('partial')?.toLocaleString()} partial`,
          'Click to explore code-level mappings',
        ])
        if (!edge.hasClass('highlighted')) {
          edge.style({ 'line-color': edgeHighlight, width: 5, opacity: 0.9 })
        }
      })
      cy.on('mouseout', 'edge', (evt) => {
        hideTooltip(); container.style.cursor = 'default'
        if (!evt.target.hasClass('highlighted')) evt.target.removeStyle('line-color width opacity')
      })

      // -- Click: node -> highlight neighborhood + info panel --
      cy.on('tap', 'node', (evt) => {
        const node = evt.target
        highlightNeighborhood(cy, node)
        if (propsRef.current.mode === 'system' && propsRef.current.onNodeSelect) {
          propsRef.current.onNodeSelect(buildSelectedInfo(cy, node))
        }
        cy.animate({ center: { eles: node } }, { duration: 300 })
      })

      // -- Click: edge -> code-level view --
      cy.on('tap', 'edge', (evt) => {
        const edge = evt.target
        if (propsRef.current.mode === 'system' && propsRef.current.onEdgeClick) {
          propsRef.current.onEdgeClick(edge.source().id(), edge.target().id())
        }
      })

      // -- Click: background -> clear selection --
      cy.on('tap', (evt) => {
        if (evt.target === cy) {
          clearHighlight(cy); hideTooltip()
          if (propsRef.current.mode === 'system' && propsRef.current.onNodeSelect) {
            propsRef.current.onNodeSelect(null)
          }
        }
      })

      cyRef.current = cy
      return () => { cy.destroy(); cyRef.current = null; hideTooltip() }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
      isDark,
      props.mode,
      props.mode === 'code' ? props.data : null,
      props.mode === 'system' ? props.systems : null,
      props.mode === 'system' ? props.stats : null,
    ])

    // -- Zoom controls --
    const handleZoomIn = useCallback(() => { cyRef.current?.zoom(cyRef.current.zoom() * 1.3) }, [])
    const handleZoomOut = useCallback(() => { cyRef.current?.zoom(cyRef.current.zoom() / 1.3) }, [])
    const handleFit = useCallback(() => {
      const cy = cyRef.current; if (!cy) return
      clearHighlight(cy)
      cy.animate({ fit: { eles: cy.elements(), padding: 30 } }, { duration: 300 })
      if (propsRef.current.mode === 'system' && propsRef.current.onNodeSelect) {
        propsRef.current.onNodeSelect(null)
      }
    }, [])

    return (
      <div className="relative w-full h-full">
        <div ref={containerRef} className="w-full h-full" />

        {/* Tooltip (DOM-managed, no React re-render) */}
        <div
          ref={tooltipRef}
          className="absolute pointer-events-none z-20 px-3 py-2 rounded-lg bg-popover border border-border/50 text-popover-foreground shadow-lg max-w-xs text-[11px]"
          style={{ display: 'none', transform: 'translate(-50%, -100%)' }}
        />

        {/* Code-level legend */}
        {props.mode === 'code' && (
          <div className="absolute top-3 left-3 flex flex-col gap-1 z-10 bg-card/95 border border-border/50 rounded-lg p-3 text-[11px]">
            <span className="font-semibold text-foreground text-xs mb-0.5">Match type</span>
            <span className="flex items-center gap-2"><span className="w-4 h-1 bg-green-500 rounded" /> exact</span>
            <span className="flex items-center gap-2"><span className="w-4 h-1 bg-amber-500 rounded" /> partial</span>
            <span className="flex items-center gap-2"><span className="w-4 h-1 bg-blue-500 rounded" /> broad</span>
          </div>
        )}

        {/* Zoom controls */}
        <div className="absolute bottom-3 right-3 flex flex-col gap-1 z-10">
          <button onClick={handleZoomIn} className="p-1.5 rounded-md bg-card/90 border border-border/50 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors" title="Zoom in">
            <ZoomIn className="h-4 w-4" />
          </button>
          <button onClick={handleZoomOut} className="p-1.5 rounded-md bg-card/90 border border-border/50 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors" title="Zoom out">
            <ZoomOut className="h-4 w-4" />
          </button>
          <button onClick={handleFit} className="p-1.5 rounded-md bg-card/90 border border-border/50 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors" title="Reset view">
            <Maximize2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    )
  },
)

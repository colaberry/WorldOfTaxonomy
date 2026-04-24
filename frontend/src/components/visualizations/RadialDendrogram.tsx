'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import * as d3 from 'd3'
import { getChildren } from '@/lib/api'
import { getSectorColor } from '@/lib/colors'
import type { TreeNodeData } from '@/lib/tree-data'

const STORAGE_PREFIX = 'wot:radial:'

function storageKey(systemId: string): string {
  return `${STORAGE_PREFIX}${systemId}`
}

function clearTransientFlags(node: HierarchyNode): HierarchyNode {
  return {
    ...node,
    _loading: false,
    children: (node.children ?? []).map(clearTransientFlags),
  }
}

function loadPersistedTree(systemId: string): HierarchyNode | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(storageKey(systemId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as HierarchyNode
    if (!parsed || typeof parsed.code !== 'string') return null
    return clearTransientFlags(parsed)
  } catch {
    return null
  }
}

function persistTree(systemId: string, tree: HierarchyNode): void {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(storageKey(systemId), JSON.stringify(tree))
  } catch {
    // sessionStorage disabled or quota exceeded; degrade silently
  }
}

// ── Types ────────────────────────────────────────────────────────────

interface Props {
  systemId: string
  initialNodes: TreeNodeData[]
  systemColor?: string
}

interface HierarchyNode {
  code: string
  title: string
  level: number
  parent_code: string | null
  sector_code: string | null
  is_leaf: boolean
  children_count: number
  _expanded?: boolean
  _loading?: boolean
  children?: HierarchyNode[]
}

// ── Helpers ──────────────────────────────────────────────────────────

// Max nodes to render before the browser chokes on SVG
const MAX_VISIBLE_NODES = 300

function buildTree(flat: TreeNodeData[]): HierarchyNode | null {
  if (flat.length === 0) return null

  const nodeMap = new Map<string, HierarchyNode>()
  const roots: HierarchyNode[] = []

  // Find min level in the data
  let minLevel = Infinity
  for (const n of flat) {
    if (n.level < minLevel) minLevel = n.level
  }

  // Create hierarchy nodes
  for (const n of flat) {
    nodeMap.set(n.code, {
      ...n,
      _expanded: true,
      children: [],
    })
  }

  // Link parent-child
  for (const n of flat) {
    const node = nodeMap.get(n.code)!
    if (n.parent_code && nodeMap.has(n.parent_code)) {
      nodeMap.get(n.parent_code)!.children!.push(node)
    } else {
      roots.push(node)
    }
  }

  // Auto-collapse: if too many nodes, only expand the first 1-2 levels
  // Try expanding 2 levels first, then 1 if still too many
  if (flat.length > MAX_VISIBLE_NODES) {
    const maxExpandLevel = findSafeExpandLevel(nodeMap, minLevel)
    for (const [, node] of nodeMap) {
      if (node.level >= maxExpandLevel) {
        node._expanded = false
      }
    }
  }

  // Mark leaf nodes in our subset that have children in DB as collapsed
  for (const [, node] of nodeMap) {
    if (node.children!.length === 0 && node.children_count > 0) {
      node._expanded = false
    }
  }

  // If single root, use it; otherwise create a synthetic root
  if (roots.length === 1) return roots[0]
  return {
    code: '__root__',
    title: '',
    level: 0,
    parent_code: null,
    sector_code: null,
    is_leaf: false,
    children_count: roots.length,
    _expanded: true,
    children: roots,
  }
}

function findSafeExpandLevel(
  nodeMap: Map<string, HierarchyNode>,
  minLevel: number,
): number {
  // Count nodes at each level
  const levelCounts = new Map<number, number>()
  for (const [, node] of nodeMap) {
    levelCounts.set(node.level, (levelCounts.get(node.level) ?? 0) + 1)
  }

  // Try expanding up to level N, count cumulative nodes
  const levels = [...levelCounts.keys()].sort((a, b) => a - b)
  let cumulative = 0
  for (const level of levels) {
    cumulative += levelCounts.get(level)!
    if (cumulative > MAX_VISIBLE_NODES) {
      // This level puts us over the limit - collapse from here
      return level
    }
  }
  return minLevel + 3 // expand all
}

function findNode(root: HierarchyNode, code: string): HierarchyNode | null {
  if (root.code === code) return root
  for (const child of root.children ?? []) {
    const found = findNode(child, code)
    if (found) return found
  }
  return null
}

type PointNode = d3.HierarchyPointNode<HierarchyNode>

function getRootAncestor(node: PointNode): PointNode {
  let cur = node
  while (cur.parent && cur.parent.parent) {
    cur = cur.parent
  }
  return cur
}

function countVisibleNodes(root: HierarchyNode): number {
  let count = 1
  if (root._expanded && root.children) {
    for (const child of root.children) {
      count += countVisibleNodes(child)
    }
  }
  return count
}

// ── Component ────────────────────────────────────────────────────────

export function RadialDendrogram({ systemId, initialNodes, systemColor }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { resolvedTheme } = useTheme()
  const [treeRoot, setTreeRoot] = useState<HierarchyNode | null>(() => {
    const persisted = loadPersistedTree(systemId)
    if (persisted) return persisted
    return buildTree(initialNodes)
  })

  // Persist every tree mutation so returning from a node detail page
  // via the browser Back button restores the exact expanded state.
  useEffect(() => {
    if (!treeRoot) return
    persistTree(systemId, treeRoot)
  }, [treeRoot, systemId])

  // Mutates the tree in place, then hands React a fresh top-level
  // reference so the drawing effect re-runs.
  const bumpTree = useCallback(() => {
    setTreeRoot((prev) => (prev ? { ...prev } : prev))
  }, [])

  const handleExpand = useCallback(
    async (code: string) => {
      if (!treeRoot) return
      const node = findNode(treeRoot, code)
      if (!node) return

      // Toggle collapse
      if (node._expanded && node.children && node.children.length > 0) {
        node._expanded = false
        bumpTree()
        return
      }

      // Already has children loaded, just expand
      if (node.children && node.children.length > 0) {
        node._expanded = true
        bumpTree()
        return
      }

      // Fetch from API
      node._loading = true
      bumpTree()
      try {
        const apiChildren = await getChildren(systemId, code)
        node.children = apiChildren.map((c) => ({
          code: c.code,
          title: c.title,
          level: c.level,
          parent_code: c.parent_code,
          sector_code: c.sector_code,
          is_leaf: c.is_leaf,
          children_count: 0, // unknown until fetched
          _expanded: false,
          children: [],
        }))
        node._expanded = true
      } catch {
        // silently fail
      } finally {
        node._loading = false
        bumpTree()
      }
    },
    [treeRoot, systemId, bumpTree],
  )

  const navigateToNode = useCallback(
    (code: string) => {
      if (code === '__root__') return
      router.push(`/system/${systemId}/node/${encodeURIComponent(code)}`)
    },
    [router, systemId],
  )

  useEffect(() => {
    if (!containerRef.current || !treeRoot) return

    const isDark = resolvedTheme === 'dark'
    const el = containerRef.current
    el.innerHTML = ''

    const width = el.clientWidth || 800
    const height = 600
    const cx = width / 2
    const cy = height / 2
    const radius = Math.min(cx, cy) - 80

    // ── Theme colors ──
    const bgColor = isDark ? '#0a0a0a' : '#f8fafc'
    const textColor = isDark ? '#e2e8f0' : '#1e293b'
    const mutedColor = isDark ? '#64748b' : '#94a3b8'
    const linkColor = isDark ? '#334155' : '#cbd5e1'
    const tooltipBg = isDark ? 'rgba(15,23,42,0.95)' : 'rgba(255,255,255,0.97)'
    const tooltipBorder = isDark ? '#334155' : '#e2e8f0'

    // ── Build D3 hierarchy (respecting _expanded state) ──
    function filterExpanded(node: HierarchyNode): HierarchyNode {
      if (!node._expanded || !node.children) {
        return { ...node, children: [] }
      }
      return {
        ...node,
        children: node.children.map(filterExpanded),
      }
    }

    const filtered = filterExpanded(treeRoot)

    const visibleCount = countVisibleNodes(filtered)
    const treeLayout = d3
      .tree<HierarchyNode>()
      .size([2 * Math.PI, radius])
      .separation((a, b) => {
        const base = (a.parent === b.parent ? 1 : 2) / (a.depth || 1)
        // Scale separation for larger trees
        return visibleCount > 200 ? base * 0.6 : visibleCount > 80 ? base * 0.8 : base
      })

    const root = treeLayout(d3.hierarchy(filtered))

    // ── SVG ──
    const svg = d3
      .select(el)
      .append('svg')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')
      .style('width', '100%')
      .style('height', '100%')
      .style('background', bgColor)
      .style('border-radius', '0.5rem')

    const defs = svg.append('defs')

    // Text shadow filter
    const shadowBlur = isDark ? 2 : 3
    const shadowColor = isDark ? 'rgba(0,0,0,0.95)' : 'rgba(255,255,255,0.95)'
    const textShadow = defs
      .append('filter')
      .attr('id', 'tree-text-bg')
      .attr('x', '-20%')
      .attr('y', '-20%')
      .attr('width', '140%')
      .attr('height', '140%')
    textShadow
      .append('feFlood')
      .attr('flood-color', shadowColor)
      .attr('result', 'flood')
    textShadow
      .append('feComposite')
      .attr('in', 'flood')
      .attr('in2', 'SourceGraphic')
      .attr('operator', 'in')
      .attr('result', 'shadow')
    textShadow
      .append('feGaussianBlur')
      .attr('in', 'shadow')
      .attr('stdDeviation', shadowBlur)
      .attr('result', 'blur')
    const tbMerge = textShadow.append('feMerge')
    tbMerge.append('feMergeNode').attr('in', 'blur')
    tbMerge.append('feMergeNode').attr('in', 'blur')
    tbMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    // ── Zoom ──
    const g = svg.append('g').attr('transform', `translate(${cx},${cy})`)

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 4])
      .on('zoom', (event) => {
        g.attr(
          'transform',
          `translate(${cx + event.transform.x},${cy + event.transform.y}) scale(${event.transform.k})`,
        )
      })

    svg.call(zoom)

    // Reset zoom on double-click
    svg.on('dblclick.zoom', () => {
      svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity)
    })

    // ── Links ──
    const radialLink = d3.linkRadial<d3.HierarchyPointLink<HierarchyNode>, PointNode>()
      .angle((d) => d.x)
      .radius((d) => d.y)

    g.append('g')
      .attr('fill', 'none')
      .attr('stroke', linkColor)
      .attr('stroke-width', 1.2)
      .attr('stroke-opacity', 0.6)
      .selectAll('path')
      .data(root.links())
      .join('path')
      .attr('d', (d) => radialLink(d as d3.HierarchyPointLink<HierarchyNode>) ?? '')

    // ── Nodes ──
    const nodeG = g
      .append('g')
      .selectAll<SVGGElement, PointNode>('g')
      .data(root.descendants())
      .join('g')
      .attr('transform', (d) => {
        const angle = ((d.x * 180) / Math.PI - 90)
        return `rotate(${angle}) translate(${d.y},0)`
      })

    // Node color: root-level children get sector colors, descendants inherit
    function getNodeColor(d: PointNode): string {
      if (d.depth === 0) return systemColor ?? '#6366F1'
      const ancestor = getRootAncestor(d)
      const sectorCode = ancestor.data.sector_code
      if (sectorCode) return getSectorColor(sectorCode)
      return systemColor ?? '#6366F1'
    }

    function getNodeOpacity(d: PointNode): number {
      if (d.depth <= 1) return 1
      return Math.max(0.4, 1 - (d.depth - 1) * 0.2)
    }

    // Circle for each node -- clicking the circle navigates to the node
    // detail page. Expand/collapse is driven by the +/- glyph below.
    nodeG
      .append('circle')
      .attr('r', (d) => {
        if (d.depth === 0) return 6
        const hasChildren = d.data.children_count > 0 || (d.children && d.children.length > 0)
        return hasChildren ? 4 : 2.5
      })
      .attr('fill', (d) => {
        const isLeaf = !d.children || d.children.length === 0
        if (isLeaf && d.data.children_count === 0) return getNodeColor(d)
        return isDark ? '#0a0a0a' : '#f8fafc'
      })
      .attr('stroke', (d) => getNodeColor(d))
      .attr('stroke-width', (d) => (d.depth === 0 ? 2.5 : 1.5))
      .attr('opacity', getNodeOpacity)
      .attr('cursor', (d) => (d.data.code === '__root__' ? 'default' : 'pointer'))
      .on('click', (_event, d) => {
        _event.stopPropagation()
        navigateToNode(d.data.code)
      })

    // Expand/collapse toggle glyph for parent nodes.
    // "+" when collapsed (children not rendered); "-" when expanded.
    // Leaves and the synthetic root get no glyph.
    function isExpandable(d: PointNode): boolean {
      if (d.data.code === '__root__') return false
      const hasLoaded = !!(d.children && d.children.length > 0)
      const hasUnloaded = d.data.children_count > 0
      return hasLoaded || hasUnloaded
    }

    function toggleGlyph(d: PointNode): string {
      const showingChildren = !!(d.children && d.children.length > 0)
      return showingChildren ? '-' : '+'
    }

    nodeG
      .filter(isExpandable)
      .append('text')
      .attr('dy', '0.35em')
      .attr('text-anchor', 'middle')
      .attr('fill', (d) => getNodeColor(d))
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .attr('cursor', 'pointer')
      .text(toggleGlyph)
      .on('click', (_event, d) => {
        _event.stopPropagation()
        handleExpand(d.data.code)
      })

    // Loading indicator
    nodeG
      .filter((d) => !!d.data._loading)
      .append('circle')
      .attr('r', 7)
      .attr('fill', 'none')
      .attr('stroke', (d) => getNodeColor(d))
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '4 3')
      .attr('opacity', 0.6)

    // ── Labels ──
    // Every visible non-root node gets a label. Density at the outer
    // rings is managed via truncation and smaller font sizes; overlap
    // is an acceptable signal to the user that they should collapse
    // or zoom. Losing labels on expand was more confusing than overlap.
    const truncForDepth = (depth: number): number => {
      if (depth === 1) return 28
      if (depth === 2) return 22
      if (depth === 3) return 18
      return 14
    }

    nodeG
      .filter((d) => d.depth > 0)
      .append('text')
      .attr('dy', '0.31em')
      .attr('x', (d) => (d.x < Math.PI === !d.children ? 8 : -8))
      .attr('text-anchor', (d) => (d.x < Math.PI === !d.children ? 'start' : 'end'))
      .attr('transform', (d) => (d.x >= Math.PI ? 'rotate(180)' : null))
      .attr('fill', textColor)
      .attr('font-size', (d) => {
        if (d.depth === 1) return '11px'
        if (d.depth === 2) return '10px'
        return '9px'
      })
      .attr('font-weight', (d) => (d.depth === 1 ? '600' : '400'))
      .attr('filter', 'url(#tree-text-bg)')
      .attr('cursor', 'pointer')
      .text((d) => {
        const maxLen = truncForDepth(d.depth)
        const t = d.data.title
        return t.length > maxLen ? t.slice(0, maxLen - 1) + '\u2026' : t
      })
      .on('click', (_event, d) => {
        _event.stopPropagation()
        navigateToNode(d.data.code)
      })

    // Root label
    if (root.data.code !== '__root__') {
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '-12')
        .attr('fill', textColor)
        .attr('font-size', '13px')
        .attr('font-weight', '700')
        .attr('filter', 'url(#tree-text-bg)')
        .text(root.data.title.length > 40 ? root.data.title.slice(0, 39) + '\u2026' : root.data.title)
    }

    // ── Tooltip ──
    const tooltip = svg
      .append('g')
      .attr('pointer-events', 'none')
      .attr('opacity', 0)

    const tooltipRect = tooltip
      .append('rect')
      .attr('rx', 6)
      .attr('ry', 6)
      .attr('fill', tooltipBg)
      .attr('stroke', tooltipBorder)
      .attr('stroke-width', 1)

    const tooltipCode = tooltip
      .append('text')
      .attr('font-size', '11px')
      .attr('font-weight', '700')
      .attr('fill', textColor)

    const tooltipTitle = tooltip
      .append('text')
      .attr('font-size', '10px')
      .attr('fill', mutedColor)

    const tooltipMeta = tooltip
      .append('text')
      .attr('font-size', '9px')
      .attr('fill', mutedColor)

    nodeG
      .on('mouseover', function (_event, d) {
        if (d.data.code === '__root__') return

        d3.select(this)
          .select('circle')
          .transition()
          .duration(150)
          .attr('r', (d.depth === 0 ? 8 : d.children ? 6 : 4))

        tooltipCode.text(d.data.code)
        tooltipTitle.text(
          d.data.title.length > 50
            ? d.data.title.slice(0, 49) + '\u2026'
            : d.data.title,
        )
        const meta = d.data.children_count > 0
          ? `${d.data.children_count} children`
          : 'Leaf node'
        tooltipMeta.text(meta)

        // Measure
        const codeBB = (tooltipCode.node() as SVGTextElement).getBBox()
        const titleBB = (tooltipTitle.node() as SVGTextElement).getBBox()
        const metaBB = (tooltipMeta.node() as SVGTextElement).getBBox()
        const padX = 10
        const padY = 8
        const lineH = 16
        const bw = Math.max(codeBB.width, titleBB.width, metaBB.width) + padX * 2
        const bh = lineH * 3 + padY * 2

        // Position near the node
        const angle = d.x - Math.PI / 2
        const nodeX = cx + Math.cos(angle) * d.y
        const nodeY = cy + Math.sin(angle) * d.y
        const tx = Math.min(Math.max(nodeX - bw / 2, 4), width - bw - 4)
        const ty = Math.max(nodeY - bh - 16, 4)

        tooltipRect.attr('x', tx).attr('y', ty).attr('width', bw).attr('height', bh)
        tooltipCode.attr('x', tx + padX).attr('y', ty + padY + 12)
        tooltipTitle.attr('x', tx + padX).attr('y', ty + padY + 12 + lineH)
        tooltipMeta.attr('x', tx + padX).attr('y', ty + padY + 12 + lineH * 2)

        tooltip.attr('opacity', 1)
      })
      .on('mouseout', function (_event, d) {
        d3.select(this)
          .select('circle')
          .transition()
          .duration(200)
          .attr('r', () => {
            if (d.depth === 0) return 6
            const hasChildren = d.data.children_count > 0 || (d.children && d.children.length > 0)
            return hasChildren ? 4 : 2.5
          })
        tooltip.attr('opacity', 0)
      })

    // ── Node count indicator ──
    svg
      .append('text')
      .attr('x', 12)
      .attr('y', height - 12)
      .attr('fill', mutedColor)
      .attr('font-size', '10px')
      .attr('font-family', 'var(--font-geist-mono)')
      .text(`${visibleCount} nodes visible - click label to open, +/- to expand, scroll to zoom, drag to pan`)

    return () => {
      el.innerHTML = ''
    }
  }, [resolvedTheme, treeRoot, systemId, systemColor, handleExpand, navigateToNode])

  if (!treeRoot) {
    return (
      <div className="flex items-center justify-center h-[600px] text-muted-foreground text-sm">
        No tree data available for this system.
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="w-full rounded-lg overflow-hidden border border-border/50"
      style={{ height: 600 }}
    />
  )
}

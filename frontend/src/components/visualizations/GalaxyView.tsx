'use client'

import { useRef, useEffect, useState, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import * as d3 from 'd3'
import type { ClassificationSystem, CrosswalkStat } from '@/lib/types'
import { getSystemColor } from '@/lib/colors'
import {
  SYSTEM_CATEGORIES,
  DOMAIN_SECTORS,
  LIFE_SCIENCES_SECTORS,
  getCategoryForSystem,
  groupSystemsByCategory,
  getLifeSciencesSector,
} from '@/lib/categories'
import { ChevronRight } from 'lucide-react'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Props {
  systems: ClassificationSystem[]
  stats: CrosswalkStat[]
}

type ViewMode = 'overview' | 'category' | 'sector'

interface DrillState {
  mode: ViewMode
  categoryId: string | null
  sectorId: string | null
}

interface ViewNode extends d3.SimulationNodeDatum {
  id: string
  label: string
  subLabel: string
  radius: number
  color: string
  phase: number
  breathSpeed: number
  type: 'category' | 'sector' | 'system'
}

interface ViewLink extends d3.SimulationLinkDatum<ViewNode> {
  weight: number
}

interface BreadcrumbItem {
  label: string
  state: DrillState
}

const DRILL_STORAGE_KEY = 'wot:galaxy:drill'

const DEFAULT_DRILL: DrillState = { mode: 'overview', categoryId: null, sectorId: null }

function loadDrill(): DrillState {
  if (typeof window === 'undefined') return DEFAULT_DRILL
  try {
    const raw = window.sessionStorage.getItem(DRILL_STORAGE_KEY)
    if (!raw) return DEFAULT_DRILL
    const parsed = JSON.parse(raw) as Partial<DrillState>
    if (parsed.mode === 'overview' || parsed.mode === 'category' || parsed.mode === 'sector') {
      return {
        mode: parsed.mode,
        categoryId: typeof parsed.categoryId === 'string' ? parsed.categoryId : null,
        sectorId: typeof parsed.sectorId === 'string' ? parsed.sectorId : null,
      }
    }
    return DEFAULT_DRILL
  } catch {
    return DEFAULT_DRILL
  }
}

function persistDrill(drill: DrillState): void {
  if (typeof window === 'undefined') return
  try {
    window.sessionStorage.setItem(DRILL_STORAGE_KEY, JSON.stringify(drill))
  } catch {
    // ignore
  }
}

// ── Data builder ──────────────────────────────────────────────────────────────

function buildView(
  drill: DrillState,
  systems: ClassificationSystem[],
  stats: CrosswalkStat[],
  grouped: ReturnType<typeof groupSystemsByCategory>
): { nodes: ViewNode[]; links: ViewLink[]; breadcrumb: BreadcrumbItem[] } {
  const OVERVIEW_STATE: DrillState = { mode: 'overview', categoryId: null, sectorId: null }

  // ── OVERVIEW: one bubble per category ──
  if (drill.mode === 'overview') {
    const maxCount = Math.max(...grouped.map((g) => g.systems.length), 1)
    const nodes: ViewNode[] = grouped.map(({ category, systems: catSystems }, i) => ({
      id: category.id,
      label: category.label,
      subLabel: `${catSystems.length} system${catSystems.length !== 1 ? 's' : ''}`,
      radius: Math.sqrt(catSystems.length / maxCount) * 55 + 38,
      color: category.accent,
      phase: (i / grouped.length) * Math.PI * 2,
      breathSpeed: 0.35 + Math.random() * 0.25,
      type: 'category' as const,
    }))

    // Derive category-to-category links from crosswalk stats
    const catLinkMap = new Map<string, number>()
    for (const s of stats) {
      const src = getCategoryForSystem(s.source_system).id
      const tgt = getCategoryForSystem(s.target_system).id
      if (src !== tgt) {
        const key = [src, tgt].sort().join('|')
        catLinkMap.set(key, (catLinkMap.get(key) || 0) + s.edge_count)
      }
    }
    const links: ViewLink[] = Array.from(catLinkMap.entries()).map(([key, weight]) => {
      const [source, target] = key.split('|')
      return { source, target, weight }
    })

    return { nodes, links, breadcrumb: [] }
  }

  // ── CATEGORY: systems or sector clusters ──
  if (drill.mode === 'category') {
    const catGroup = grouped.find((g) => g.category.id === drill.categoryId)
    const catSystems = catGroup?.systems ?? []
    const category = SYSTEM_CATEGORIES.find((c) => c.id === drill.categoryId)!
    const breadcrumb: BreadcrumbItem[] = [
      { label: 'All Categories', state: OVERVIEW_STATE },
      { label: category.label, state: { ...drill } },
    ]

    // Domain: show 36 sector bubbles instead of 149 systems
    if (drill.categoryId === 'domain') {
      const sectorsPresent = DOMAIN_SECTORS.filter((sector) =>
        catSystems.some((s) =>
          s.id === 'domain_adv_materials'
            ? sector.id === 'materials'
            : s.id.startsWith(sector.prefix)
        )
      )
      const maxCount = Math.max(...sectorsPresent.map((sec) => {
        return catSystems.filter((s) =>
          s.id === 'domain_adv_materials'
            ? sec.id === 'materials'
            : s.id.startsWith(sec.prefix)
        ).length
      }), 1)

      const nodes: ViewNode[] = sectorsPresent.map((sector, i) => {
        const count = catSystems.filter((s) =>
          s.id === 'domain_adv_materials'
            ? sector.id === 'materials'
            : s.id.startsWith(sector.prefix)
        ).length
        return {
          id: sector.id,
          label: sector.label,
          subLabel: `${count} system${count !== 1 ? 's' : ''}`,
          radius: Math.sqrt(count / maxCount) * 38 + 30,
          color: sector.accent,
          phase: (i / sectorsPresent.length) * Math.PI * 2,
          breathSpeed: 0.35 + Math.random() * 0.25,
          type: 'sector' as const,
        }
      })
      return { nodes, links: [], breadcrumb }
    }

    // Life Sciences: show 13 sector bubbles
    if (drill.categoryId === 'lifesciences') {
      const sectorsPresent = LIFE_SCIENCES_SECTORS.filter((sector) =>
        catSystems.some((s) => getLifeSciencesSector(s.id)?.id === sector.id)
      )
      const maxCount = Math.max(...sectorsPresent.map((sec) =>
        catSystems.filter((s) => getLifeSciencesSector(s.id)?.id === sec.id).length
      ), 1)

      const nodes: ViewNode[] = sectorsPresent.map((sector, i) => {
        const count = catSystems.filter((s) => getLifeSciencesSector(s.id)?.id === sector.id).length
        return {
          id: sector.id,
          label: sector.label,
          subLabel: `${count} system${count !== 1 ? 's' : ''}`,
          radius: Math.sqrt(count / maxCount) * 38 + 30,
          color: sector.accent,
          phase: (i / sectorsPresent.length) * Math.PI * 2,
          breathSpeed: 0.35 + Math.random() * 0.25,
          type: 'sector' as const,
        }
      })
      return { nodes, links: [], breadcrumb }
    }

    // Non-domain, non-lifesciences: show individual system bubbles
    const maxNodeCount = Math.max(...catSystems.map((s) => s.node_count), 1)
    const nodes: ViewNode[] = catSystems.map((sys, i) => ({
      id: sys.id,
      label: sys.name,
      subLabel: `${sys.node_count.toLocaleString()} codes`,
      radius: Math.sqrt(sys.node_count / maxNodeCount) * 38 + 18,
      color: sys.tint_color || category.accent,
      phase: (i / catSystems.length) * Math.PI * 2,
      breathSpeed: 0.35 + Math.random() * 0.25,
      type: 'system' as const,
    }))

    const sysIds = new Set(catSystems.map((s) => s.id))
    const linkMap = new Map<string, number>()
    for (const s of stats) {
      if (sysIds.has(s.source_system) && sysIds.has(s.target_system)) {
        const key = [s.source_system, s.target_system].sort().join('|')
        linkMap.set(key, (linkMap.get(key) || 0) + s.edge_count)
      }
    }
    const links: ViewLink[] = Array.from(linkMap.entries()).map(([key, weight]) => {
      const [source, target] = key.split('|')
      return { source, target, weight }
    })

    return { nodes, links, breadcrumb }
  }

  // ── SECTOR: systems within one sector (domain or life sciences) ──
  let sectorAccent: string
  let sectorName: string
  let sectorSystems: ClassificationSystem[]
  let parentCatId: string

  if (drill.categoryId === 'lifesciences') {
    const sector = LIFE_SCIENCES_SECTORS.find((s) => s.id === drill.sectorId)!
    sectorAccent = sector.accent
    sectorName = sector.label
    parentCatId = 'lifesciences'
    const lsGroup = grouped.find((g) => g.category.id === 'lifesciences')
    const allLS = lsGroup?.systems ?? []
    sectorSystems = allLS.filter((s) => getLifeSciencesSector(s.id)?.id === sector.id)
  } else {
    const sector = DOMAIN_SECTORS.find((s) => s.id === drill.sectorId)!
    sectorAccent = sector.accent
    sectorName = sector.label
    parentCatId = 'domain'
    const domainGroup = grouped.find((g) => g.category.id === 'domain')
    const allDomain = domainGroup?.systems ?? []
    sectorSystems = allDomain.filter((s) =>
      s.id === 'domain_adv_materials'
        ? sector.id === 'materials'
        : s.id.startsWith(sector.prefix)
    )
  }

  const parentCat = SYSTEM_CATEGORIES.find((c) => c.id === parentCatId)!
  const breadcrumb: BreadcrumbItem[] = [
    { label: 'All Categories', state: OVERVIEW_STATE },
    { label: parentCat.label, state: { mode: 'category', categoryId: parentCatId, sectorId: null } },
    { label: sectorName, state: { ...drill } },
  ]

  const maxNodeCount = Math.max(...sectorSystems.map((s) => s.node_count), 1)
  const nodes: ViewNode[] = sectorSystems.map((sys, i) => ({
    id: sys.id,
    label: sys.name,
    subLabel: `${sys.node_count.toLocaleString()} codes`,
    radius: Math.sqrt(sys.node_count / maxNodeCount) * 38 + 22,
    color: sys.tint_color || sectorAccent,
    phase: (i / sectorSystems.length) * Math.PI * 2,
    breathSpeed: 0.35 + Math.random() * 0.25,
    type: 'system' as const,
  }))

  const sysIds = new Set(sectorSystems.map((s) => s.id))
  const linkMap = new Map<string, number>()
  for (const s of stats) {
    if (sysIds.has(s.source_system) && sysIds.has(s.target_system)) {
      const key = [s.source_system, s.target_system].sort().join('|')
      linkMap.set(key, (linkMap.get(key) || 0) + s.edge_count)
    }
  }
  const links: ViewLink[] = Array.from(linkMap.entries()).map(([key, weight]) => {
    const [source, target] = key.split('|')
    return { source, target, weight }
  })

  return { nodes, links, breadcrumb }
}

// ── Component ─────────────────────────────────────────────────────────────────

export function GalaxyView({ systems, stats }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { resolvedTheme } = useTheme()

  const [drill, setDrill] = useState<DrillState>(() => loadDrill())

  useEffect(() => {
    persistDrill(drill)
  }, [drill])

  const grouped = useMemo(() => groupSystemsByCategory(systems), [systems])

  const { nodes: viewNodes, links: viewLinks, breadcrumb } = useMemo(
    () => buildView(drill, systems, stats, grouped),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [drill.mode, drill.categoryId, drill.sectorId, systems, stats, grouped]
  )

  const handleNodeClick = useCallback(
    (node: ViewNode) => {
      if (node.type === 'category') {
        setDrill({ mode: 'category', categoryId: node.id, sectorId: null })
      } else if (node.type === 'sector') {
        setDrill((prev) => ({ mode: 'sector', categoryId: prev.categoryId, sectorId: node.id }))
      } else {
        router.push(`/system/${node.id}`)
      }
    },
    [router]
  )

  const handleBack = useCallback(() => {
    setDrill((prev) => {
      if (prev.mode === 'sector') {
        return { mode: 'category', categoryId: prev.categoryId, sectorId: null }
      }
      if (prev.mode === 'category') {
        return { mode: 'overview', categoryId: null, sectorId: null }
      }
      return prev
    })
  }, [])

  useEffect(() => {
    if (!containerRef.current || viewNodes.length === 0) return

    const isDark = resolvedTheme === 'dark'
    const el = containerRef.current
    el.innerHTML = ''

    const width = el.clientWidth || 800
    const height = el.clientHeight || 680
    const isMobile = width < 600

    // ── Theme colors ──
    const bgColor = isDark ? '#0a0a0a' : '#f8fafc'
    const textColor = isDark ? '#ffffff' : '#111827'
    const textShadowColor = isDark ? 'rgba(0,0,0,0.95)' : 'rgba(255,255,255,0.95)'
    const subtextColor = isDark ? 'rgba(255,255,255,0.7)' : 'rgba(55,65,81,0.9)'
    const linkColor = isDark ? '#3B82F6' : '#6366F1'
    const linkOpacity = isDark ? 0.12 : 0.2
    const starColor = isDark ? '#ffffff' : '#94a3b8'
    const starMaxOpacity = isDark ? 0.3 : 0.15
    const orbFillOpacity = isDark ? 0.15 : 0.18
    const orbStrokeWidth = isDark ? 1.5 : 2.5

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

    // Glow filters
    const glow = defs.append('filter').attr('id', 'glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%')
    glow.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur')
    const glowMerge = glow.append('feMerge')
    glowMerge.append('feMergeNode').attr('in', 'blur')
    glowMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    const glowStrong = defs.append('filter').attr('id', 'glow-strong').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%')
    glowStrong.append('feGaussianBlur').attr('stdDeviation', '8').attr('result', 'blur')
    const gsMerge = glowStrong.append('feMerge')
    gsMerge.append('feMergeNode').attr('in', 'blur')
    gsMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    const shadowBlur = isDark ? 2 : 3
    const textShadow = defs.append('filter').attr('id', 'text-bg').attr('x', '-15%').attr('y', '-15%').attr('width', '130%').attr('height', '130%')
    textShadow.append('feFlood').attr('flood-color', textShadowColor).attr('result', 'flood')
    textShadow.append('feComposite').attr('in', 'flood').attr('in2', 'SourceGraphic').attr('operator', 'in').attr('result', 'shadow')
    textShadow.append('feGaussianBlur').attr('in', 'shadow').attr('stdDeviation', shadowBlur).attr('result', 'blur')
    const tbMerge = textShadow.append('feMerge')
    tbMerge.append('feMergeNode').attr('in', 'blur')
    tbMerge.append('feMergeNode').attr('in', 'blur')
    tbMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    // ── Background stars ──
    const starCount = isMobile ? 40 : 80
    const starsG = svg.append('g')
    for (let i = 0; i < starCount; i++) {
      starsG.append('circle')
        .attr('cx', Math.random() * width)
        .attr('cy', Math.random() * height)
        .attr('r', Math.random() * 1.2 + 0.3)
        .attr('fill', starColor)
        .attr('opacity', Math.random() * starMaxOpacity + 0.05)
    }

    // ── Click hint (overview only) ──
    if (drill.mode === 'overview') {
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', height - 14)
        .attr('text-anchor', 'middle')
        .attr('fill', isDark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')
        .attr('font-size', '11px')
        .text('Click any category to explore')
    }

    // ── Force simulation ──
    const maxRadius = Math.max(...viewNodes.map((n) => n.radius))
    const padding = maxRadius + 16
    const linkDist = isMobile ? 90 : 160
    const nCount = viewNodes.length
    const chargeStrength = nCount <= 15
      ? -(isMobile ? 900 : 1600)
      : nCount <= 40
      ? -(isMobile ? 400 : 800)
      : -(isMobile ? 200 : 420)

    // Pre-position nodes in a circle so the simulation starts settled
    const simNodes: ViewNode[] = viewNodes.map((n, i) => {
      const angle = (i / viewNodes.length) * Math.PI * 2
      const spread = Math.min(width, height) * 0.3
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * spread,
        y: height / 2 + Math.sin(angle) * spread,
      }
    })

    const simLinks: ViewLink[] = viewLinks.map((l) => ({
      ...l,
      source: typeof l.source === 'string' ? l.source : (l.source as ViewNode).id,
      target: typeof l.target === 'string' ? l.target : (l.target as ViewNode).id,
    }))

    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        'link',
        d3
          .forceLink<ViewNode, ViewLink>(simLinks)
          .id((d) => d.id)
          .distance(linkDist)
          .strength(0.35)
      )
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force(
        'collision',
        d3.forceCollide<ViewNode>().radius((d) => d.radius + (isMobile ? 14 : 20)).strength(0.9)
      )
      .force('x', d3.forceX(width / 2).strength(0.06))
      .force('y', d3.forceY(height / 2).strength(0.06))
      .velocityDecay(0.45)

    // ── Edges ──
    const linkLine = svg
      .append('g')
      .selectAll('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', linkColor)
      .attr('stroke-opacity', linkOpacity)
      .attr('stroke-width', (d) => Math.max(0.8, Math.log(d.weight + 1) * 0.5))

    // ── Particles along edges ──
    const particlesPerLink = isMobile ? 1 : 2
    const particles: Array<{
      link: ViewLink
      t: number
      speed: number
      size: number
      reverse: boolean
    }> = []
    simLinks.forEach((l) => {
      for (let p = 0; p < particlesPerLink; p++) {
        particles.push({
          link: l,
          t: Math.random(),
          speed: 0.002 + Math.random() * 0.003,
          size: 1.5 + Math.random() * 1.5,
          reverse: p % 2 === 1,
        })
      }
    })

    const particleDots = svg
      .append('g')
      .selectAll('circle.particle')
      .data(particles)
      .join('circle')
      .attr('r', (d) => d.size)
      .attr('fill', '#fff')
      .attr('opacity', 0)

    // ── Node groups ──
    const LARGE = isMobile ? 38 : 44
    const MEDIUM = isMobile ? 28 : 32

    function truncate(str: string, max: number) {
      return str.length <= max ? str : str.slice(0, max - 1) + '\u2026'
    }

    let hoveredId: string | null = null

    let wasDragged = false

    const node = svg
      .append('g')
      .selectAll<SVGGElement, ViewNode>('g')
      .data(simNodes)
      .join('g')
      .attr('cursor', 'pointer')
      .on('click', (_event, d) => {
        if (!wasDragged) handleNodeClick(d)
      })
      .call(
        d3
          .drag<SVGGElement, ViewNode>()
          .on('start', (event, d) => {
            wasDragged = false
            if (!event.active) simulation.alphaTarget(0.15).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (event, d) => {
            wasDragged = true
            d.fx = event.x
            d.fy = event.y
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          })
      )

    // Halo
    node
      .append('circle')
      .attr('class', 'halo')
      .attr('r', (d) => d.radius + 6)
      .attr('fill', 'none')
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', 0.5)
      .attr('stroke-opacity', 0)

    // Orb
    node
      .append('circle')
      .attr('class', 'orb')
      .attr('r', (d) => d.radius)
      .attr('fill', (d) => d.color)
      .attr('fill-opacity', orbFillOpacity)
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', orbStrokeWidth)
      .attr('filter', 'url(#glow)')

    // Core
    node
      .append('circle')
      .attr('class', 'core')
      .attr('r', (d) => d.radius * 0.15)
      .attr('fill', (d) => d.color)
      .attr('fill-opacity', 0.4)

    // "Drill-in" ring for non-system nodes
    node
      .filter((d) => d.type !== 'system')
      .append('circle')
      .attr('class', 'drill-ring')
      .attr('r', (d) => d.radius + 3)
      .attr('fill', 'none')
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4 3')
      .attr('stroke-opacity', 0.35)

    // Label - primary
    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => d.radius >= LARGE ? -7 : 1)
      .attr('fill', textColor)
      .attr('font-size', (d) => {
        if (d.radius >= LARGE) return isMobile ? '10px' : '12px'
        if (d.radius >= MEDIUM) return isMobile ? '9px' : '10px'
        return isMobile ? '8px' : '9px'
      })
      .attr('font-weight', '600')
      .attr('pointer-events', 'none')
      .attr('filter', 'url(#text-bg)')
      .text((d) => {
        if (d.radius >= LARGE) return d.label
        if (d.radius >= MEDIUM) return truncate(d.label, 18)
        return truncate(d.label, 12)
      })

    // Sub-label (code/system count) - only for larger orbs
    node
      .filter((d) => d.radius >= LARGE)
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 10)
      .attr('fill', subtextColor)
      .attr('font-family', 'var(--font-geist-mono)')
      .attr('font-size', isMobile ? '8px' : '10px')
      .attr('font-weight', '500')
      .attr('pointer-events', 'none')
      .attr('filter', 'url(#text-bg)')
      .text((d) => d.subLabel)

    // ── Hover tooltip for small orbs ──
    const hoverLabel = svg.append('g').attr('pointer-events', 'none').attr('opacity', 0)
    const hoverBg = hoverLabel
      .append('rect')
      .attr('rx', 4)
      .attr('ry', 4)
      .attr('fill', isDark ? 'rgba(15,23,42,0.92)' : 'rgba(255,255,255,0.95)')
      .attr('stroke', isDark ? '#334155' : '#cbd5e1')
      .attr('stroke-width', 1)
    const hoverText = hoverLabel
      .append('text')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', textColor)
      .attr('text-anchor', 'middle')

    node
      .on('mouseover', function (_event, d) {
        hoveredId = d.id
        d3.select(this).select('.orb')
          .transition().duration(200)
          .attr('fill-opacity', isDark ? 0.35 : 0.45)
          .attr('stroke-width', 2.5)
          .attr('filter', 'url(#glow-strong)')
        d3.select(this).select('.core')
          .transition().duration(200)
          .attr('r', d.radius * 0.25)
          .attr('fill-opacity', 0.7)
        d3.select(this).select('.halo')
          .transition().duration(200)
          .attr('stroke-opacity', 0.45)
          .attr('r', d.radius + 14)

        linkLine
          .transition().duration(200)
          .attr('stroke-opacity', (l) => {
            const src = (l.source as ViewNode).id
            const tgt = (l.target as ViewNode).id
            return src === d.id || tgt === d.id ? 0.55 : 0.04
          })

        if (d.radius < MEDIUM) {
          hoverText.text(`${d.label} - ${d.subLabel}`)
          const bb = (hoverText.node() as SVGTextElement).getBBox()
          const pad = 6
          const bw = bb.width + pad * 2
          const bh = bb.height + pad * 2
          const lx = Math.min(Math.max(d.x ?? 0, bw / 2 + 4), width - bw / 2 - 4)
          const ly = (d.y ?? 0) - d.radius - bh - 6
          hoverBg.attr('x', lx - bw / 2).attr('y', ly).attr('width', bw).attr('height', bh)
          hoverText.attr('x', lx).attr('y', ly + bh - pad)
          hoverLabel.attr('opacity', 1)
        }
      })
      .on('mouseout', function (_event, d) {
        hoveredId = null
        d3.select(this).select('.orb')
          .transition().duration(300)
          .attr('fill-opacity', orbFillOpacity)
          .attr('stroke-width', orbStrokeWidth)
          .attr('filter', 'url(#glow)')
        d3.select(this).select('.core')
          .transition().duration(300)
          .attr('r', d.radius * 0.15)
          .attr('fill-opacity', 0.4)
        d3.select(this).select('.halo')
          .transition().duration(300)
          .attr('stroke-opacity', 0)
          .attr('r', d.radius + 6)
        linkLine.transition().duration(300).attr('stroke-opacity', linkOpacity)
        hoverLabel.attr('opacity', 0)
      })

    // ── In-chart back button (top-left pill) ──
    if (drill.mode !== 'overview') {
      const prevLabel =
        drill.mode === 'sector'
          ? (SYSTEM_CATEGORIES.find((c) => c.id === drill.categoryId)?.label ?? 'Back')
          : 'All Categories'

      const btnW = isMobile ? 110 : 136
      const btnH = 32
      const btnX = 14
      const btnY = 14

      const backBtn = svg
        .append('g')
        .attr('class', 'back-btn')
        .attr('cursor', 'pointer')
        .on('click', (event) => {
          event.stopPropagation()
          handleBack()
        })

      // Pill background
      backBtn
        .append('rect')
        .attr('x', btnX)
        .attr('y', btnY)
        .attr('width', btnW)
        .attr('height', btnH)
        .attr('rx', btnH / 2)
        .attr('fill', isDark ? 'rgba(15,23,42,0.82)' : 'rgba(248,250,252,0.88)')
        .attr('stroke', isDark ? 'rgba(148,163,184,0.35)' : 'rgba(100,116,139,0.35)')
        .attr('stroke-width', 1.2)

      // Arrow symbol
      backBtn
        .append('text')
        .attr('x', btnX + 14)
        .attr('y', btnY + btnH / 2 + 4.5)
        .attr('fill', isDark ? '#94a3b8' : '#475569')
        .attr('font-size', isMobile ? '13px' : '14px')
        .attr('pointer-events', 'none')
        .text('\u2190')

      // Label
      backBtn
        .append('text')
        .attr('x', btnX + 28)
        .attr('y', btnY + btnH / 2 + 4.5)
        .attr('fill', isDark ? '#cbd5e1' : '#334155')
        .attr('font-size', isMobile ? '10px' : '11px')
        .attr('font-weight', '600')
        .attr('pointer-events', 'none')
        .text(prevLabel.length > 14 ? prevLabel.slice(0, 13) + '\u2026' : prevLabel)

      // Hover effect
      backBtn
        .on('mouseover', function () {
          d3.select(this)
            .select('rect')
            .transition()
            .duration(150)
            .attr('fill', isDark ? 'rgba(51,65,85,0.92)' : 'rgba(226,232,240,0.95)')
            .attr('stroke', isDark ? 'rgba(148,163,184,0.7)' : 'rgba(100,116,139,0.7)')
        })
        .on('mouseout', function () {
          d3.select(this)
            .select('rect')
            .transition()
            .duration(200)
            .attr('fill', isDark ? 'rgba(15,23,42,0.82)' : 'rgba(248,250,252,0.88)')
            .attr('stroke', isDark ? 'rgba(148,163,184,0.35)' : 'rgba(100,116,139,0.35)')
        })
    }

    // ── Simulation tick ──
    simulation.on('tick', () => {
      simNodes.forEach((d) => {
        d.x = Math.max(padding, Math.min(width - padding, d.x ?? width / 2))
        d.y = Math.max(padding, Math.min(height - padding, d.y ?? height / 2))
      })

      linkLine
        .attr('x1', (d) => (d.source as ViewNode).x ?? 0)
        .attr('y1', (d) => (d.source as ViewNode).y ?? 0)
        .attr('x2', (d) => (d.target as ViewNode).x ?? 0)
        .attr('y2', (d) => (d.target as ViewNode).y ?? 0)

      node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    // ── Animation loop ──
    const t0 = performance.now()
    let animId: number

    function animate(now: number) {
      const elapsed = (now - t0) / 1000

      node.select('.orb').each(function (d) {
        if (hoveredId === d.id) return
        const breath = 1 + Math.sin(elapsed * d.breathSpeed + d.phase) * 0.04
        d3.select(this).attr('r', d.radius * breath)
      })

      node.select('.halo').each(function (d) {
        if (hoveredId === d.id) return
        const pulse = Math.sin(elapsed * 0.8 + d.phase) * 0.5 + 0.5
        d3.select(this)
          .attr('r', d.radius + 4 + pulse * 4)
          .attr('stroke-opacity', pulse * 0.12)
      })

      node.select('.core').each(function (d) {
        if (hoveredId === d.id) return
        const shimmer = 0.3 + Math.sin(elapsed * 1.2 + d.phase + 1) * 0.15
        d3.select(this).attr('fill-opacity', shimmer)
      })

      starsG.selectAll('circle').each(function (_d, i) {
        const twinkle = 0.05 + Math.sin(elapsed * 0.5 + i * 1.7) * 0.15
        d3.select(this).attr('opacity', Math.max(0.02, twinkle))
      })

      particleDots.each(function (d) {
        d.t += d.reverse ? -d.speed : d.speed
        if (d.t > 1) d.t -= 1
        if (d.t < 0) d.t += 1
        const src = d.link.source as ViewNode
        const tgt = d.link.target as ViewNode
        if (!src.x || !tgt.x) return
        const x = src.x + (tgt.x - src.x) * d.t
        const y = (src.y ?? 0) + ((tgt.y ?? 0) - (src.y ?? 0)) * d.t
        const edgeFade = Math.sin(d.t * Math.PI)
        const isConnected = hoveredId && (src.id === hoveredId || tgt.id === hoveredId)
        d3.select(this)
          .attr('cx', x)
          .attr('cy', y)
          .attr('opacity', edgeFade * (isConnected ? 0.7 : 0.3))
          .attr('fill', src.color)
      })

      if (simulation.alpha() < 0.005) {
        simNodes.forEach((d) => {
          if (d.fx !== null && d.fx !== undefined) return
          d.vx = (d.vx ?? 0) + (Math.random() - 0.5) * 0.05
          d.vy = (d.vy ?? 0) + (Math.random() - 0.5) * 0.05
        })
        simulation.alpha(0.008).restart()
      }

      animId = requestAnimationFrame(animate)
    }

    const startTimer = setTimeout(() => {
      animId = requestAnimationFrame(animate)
    }, 1200)

    return () => {
      clearTimeout(startTimer)
      cancelAnimationFrame(animId)
      simulation.stop()
      el.innerHTML = ''
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolvedTheme, viewNodes, viewLinks, handleNodeClick, handleBack, drill.mode])

  // ── Category label for header ──
  const categoryLabel = drill.categoryId
    ? SYSTEM_CATEGORIES.find((c) => c.id === drill.categoryId)?.label ?? ''
    : ''
  const sectorLabel = drill.sectorId
    ? (DOMAIN_SECTORS.find((s) => s.id === drill.sectorId)?.label
       ?? LIFE_SCIENCES_SECTORS.find((s) => s.id === drill.sectorId)?.label
       ?? '')
    : ''

  return (
    <div className="space-y-2">
      {/* Breadcrumb nav */}
      {breadcrumb.length > 0 && (
        <div className="flex items-center gap-1 px-1 text-xs text-muted-foreground flex-wrap">
          {breadcrumb.map((item, i) => {
            const isLast = i === breadcrumb.length - 1
            return (
              <span key={i} className="flex items-center gap-1">
                {i > 0 && <ChevronRight className="h-3 w-3 opacity-40 shrink-0" />}
                {isLast ? (
                  <span className="font-semibold text-foreground">{item.label}</span>
                ) : (
                  <button
                    onClick={() => setDrill(item.state)}
                    className="hover:text-foreground transition-colors underline underline-offset-2"
                  >
                    {item.label}
                  </button>
                )}
              </span>
            )
          })}

          {/* Count badge */}
          <span className="ml-2 px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-[10px] font-mono">
            {viewNodes.length}{' '}
            {drill.mode === 'overview'
              ? 'categories'
              : drill.mode === 'category' && (drill.categoryId === 'domain' || drill.categoryId === 'lifesciences')
              ? 'sectors'
              : drill.mode === 'sector'
              ? 'systems'
              : 'systems'}
          </span>

          {/* Context hint for drillable views */}
          {drill.mode !== 'overview' && drill.mode !== 'sector' && (
            <span className="ml-1 text-[10px] opacity-50">
              {(drill.categoryId === 'domain' || drill.categoryId === 'lifesciences')
                ? '- click a sector to explore'
                : '- click a system to open it'}
            </span>
          )}
          {drill.mode === 'overview' && null}
        </div>
      )}

      {/* Visualization */}
      <div
        ref={containerRef}
        className="w-full rounded-lg overflow-hidden"
        style={{ minHeight: 620, maxHeight: 860, aspectRatio: '4/3' }}
      />

      {/* Footer hint on overview */}
      {drill.mode === 'overview' && (
        <p className="text-center text-[11px] text-muted-foreground/50">
          {categoryLabel || sectorLabel
            ? null
            : 'Click any bubble to drill into its systems'}
        </p>
      )}
    </div>
  )
}

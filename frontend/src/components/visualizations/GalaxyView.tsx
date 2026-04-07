'use client'

import { useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import * as d3 from 'd3'
import type { ClassificationSystem, CrosswalkStat } from '@/lib/types'

interface Props {
  systems: ClassificationSystem[]
  stats: CrosswalkStat[]
}

interface GalaxyNode extends d3.SimulationNodeDatum {
  id: string
  name: string
  nodeCount: number
  radius: number
  color: string
  phase: number
  breathSpeed: number
}

interface GalaxyLink extends d3.SimulationLinkDatum<GalaxyNode> {
  weight: number
}

export function GalaxyView({ systems, stats }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { resolvedTheme } = useTheme()

  useEffect(() => {
    if (!containerRef.current || systems.length === 0) return

    const isDark = resolvedTheme === 'dark'
    const el = containerRef.current
    el.innerHTML = ''

    const width = el.clientWidth
    const height = el.clientHeight || 500
    const isMobile = width < 600

    const maxRadius = isMobile ? 35 : 55
    const minRadius = isMobile ? 18 : 25
    const maxNodeCount = Math.max(...systems.map((s) => s.node_count))

    const nodes: GalaxyNode[] = systems.map((s, i) => {
      const t = Math.sqrt(s.node_count / maxNodeCount)
      return {
        id: s.id,
        name: s.name,
        nodeCount: s.node_count,
        radius: minRadius + t * (maxRadius - minRadius),
        color: s.tint_color || '#3B82F6',
        phase: (i / systems.length) * Math.PI * 2,
        breathSpeed: 0.4 + Math.random() * 0.3,
      }
    })

    const links: GalaxyLink[] = []
    const seen = new Set<string>()
    stats.forEach((s) => {
      const key = [s.source_system, s.target_system].sort().join('|')
      if (!seen.has(key)) {
        seen.add(key)
        links.push({ source: s.source_system, target: s.target_system, weight: s.edge_count })
      }
    })

    // Theme-aware colors
    const bgColor = isDark ? '#0a0a0a' : '#f8fafc'
    const textColor = isDark ? '#ffffff' : '#111827'
    const textShadowColor = isDark ? 'rgba(0, 0, 0, 0.95)' : 'rgba(255, 255, 255, 0.95)'
    const subtextColor = isDark ? 'rgba(255,255,255,0.7)' : 'rgba(55, 65, 81, 0.9)'
    const linkColor = isDark ? '#3B82F6' : '#6366F1'
    const linkOpacity = isDark ? 0.12 : 0.2
    const starColor = isDark ? '#ffffff' : '#94a3b8'
    const starMaxOpacity = isDark ? 0.3 : 0.15
    const orbFillOpacity = isDark ? 0.15 : 0.18
    const orbStrokeWidth = isDark ? 1.5 : 2.5

    // SVG
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

    // Text shadow filter for legibility — thicker halo in light mode
    const shadowBlur = isDark ? 2 : 3
    const textShadow = defs.append('filter').attr('id', 'text-bg').attr('x', '-15%').attr('y', '-15%').attr('width', '130%').attr('height', '130%')
    textShadow.append('feFlood').attr('flood-color', textShadowColor).attr('result', 'flood')
    textShadow.append('feComposite').attr('in', 'flood').attr('in2', 'SourceGraphic').attr('operator', 'in').attr('result', 'shadow')
    textShadow.append('feGaussianBlur').attr('in', 'shadow').attr('stdDeviation', shadowBlur).attr('result', 'blur')
    const tbMerge = textShadow.append('feMerge')
    tbMerge.append('feMergeNode').attr('in', 'blur')
    tbMerge.append('feMergeNode').attr('in', 'blur')  // double blur layer for stronger halo
    tbMerge.append('feMergeNode').attr('in', 'SourceGraphic')

    // Background stars
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

    // Force simulation
    const padding = maxRadius + 15
    const linkDist = isMobile ? 60 : 100
    const chargeStrength = isMobile ? -120 : -200

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink<GalaxyNode, GalaxyLink>(links).id((d) => d.id).distance(linkDist).strength(0.5))
      .force('charge', d3.forceManyBody().strength(chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide<GalaxyNode>().radius((d) => d.radius + (isMobile ? 8 : 12)))
      .force('x', d3.forceX(width / 2).strength(0.08))
      .force('y', d3.forceY(height / 2).strength(0.08))
      .velocityDecay(0.4)

    // Edges
    const linkLine = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', linkColor)
      .attr('stroke-opacity', linkOpacity)
      .attr('stroke-width', (d) => Math.max(1, Math.log(d.weight) * 0.6))

    // Data-flow particles
    const particlesPerLink = isMobile ? 1 : 2
    const particles: Array<{ link: GalaxyLink; t: number; speed: number; size: number; reverse: boolean }> = []
    links.forEach((l) => {
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

    const particleDots = svg.append('g')
      .selectAll('circle.particle')
      .data(particles)
      .join('circle')
      .attr('r', (d) => d.size)
      .attr('fill', '#fff')
      .attr('opacity', 0)

    // Nodes
    const node = svg.append('g')
      .selectAll<SVGGElement, GalaxyNode>('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .on('click', (_event, d) => {
        router.push(`/system/${d.id}`)
      })
      .call(
        d3.drag<SVGGElement, GalaxyNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x; d.fy = d.y
          })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null; d.fy = null
          })
      )

    // Halo
    node.append('circle').attr('class', 'halo')
      .attr('r', (d) => d.radius + 6)
      .attr('fill', 'none')
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', 0.5)
      .attr('stroke-opacity', 0)

    // Orb
    node.append('circle').attr('class', 'orb')
      .attr('r', (d) => d.radius)
      .attr('fill', (d) => d.color)
      .attr('fill-opacity', orbFillOpacity)
      .attr('stroke', (d) => d.color)
      .attr('stroke-width', orbStrokeWidth)
      .attr('filter', 'url(#glow)')

    // Core
    node.append('circle').attr('class', 'core')
      .attr('r', (d) => d.radius * 0.15)
      .attr('fill', (d) => d.color)
      .attr('fill-opacity', 0.4)

    // Labels — white text with shadow for legibility on both themes
    const fontSize = isMobile ? '10px' : '12px'
    const countSize = isMobile ? '8px' : '10px'
    const fontWeight = '600'

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', -5)
      .attr('fill', textColor)
      .attr('font-size', fontSize)
      .attr('font-weight', fontWeight)
      .attr('pointer-events', 'none')
      .attr('filter', 'url(#text-bg)')
      .text((d) => d.name)

    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 10)
      .attr('fill', subtextColor)
      .attr('font-family', 'var(--font-geist-mono)')
      .attr('font-size', countSize)
      .attr('font-weight', '500')
      .attr('pointer-events', 'none')
      .attr('filter', 'url(#text-bg)')
      .text((d) => `${d.nodeCount.toLocaleString()} codes`)

    // Hover
    let hoveredNode: string | null = null

    node.on('mouseover', function (_event, d) {
      hoveredNode = d.id
      d3.select(this).select('.orb')
        .transition().duration(200)
        .attr('fill-opacity', isDark ? 0.35 : 0.45).attr('stroke-width', 2.5).attr('filter', 'url(#glow-strong)')
      d3.select(this).select('.core')
        .transition().duration(200)
        .attr('r', d.radius * 0.25).attr('fill-opacity', 0.7)
      d3.select(this).select('.halo')
        .transition().duration(200)
        .attr('stroke-opacity', 0.4).attr('r', d.radius + 12)

      linkLine.transition().duration(200)
        .attr('stroke-opacity', (l) => {
          const src = (l.source as GalaxyNode).id
          const tgt = (l.target as GalaxyNode).id
          return src === d.id || tgt === d.id ? 0.5 : 0.04
        })
    }).on('mouseout', function (_event, d) {
      hoveredNode = null
      d3.select(this).select('.orb')
        .transition().duration(300)
        .attr('fill-opacity', orbFillOpacity).attr('stroke-width', orbStrokeWidth).attr('filter', 'url(#glow)')
      d3.select(this).select('.core')
        .transition().duration(300)
        .attr('r', d.radius * 0.15).attr('fill-opacity', 0.4)
      d3.select(this).select('.halo')
        .transition().duration(300)
        .attr('stroke-opacity', 0).attr('r', d.radius + 6)

      linkLine.transition().duration(300).attr('stroke-opacity', linkOpacity)
    })

    // Tick
    simulation.on('tick', () => {
      nodes.forEach((d) => {
        d.x = Math.max(padding, Math.min(width - padding, d.x!))
        d.y = Math.max(padding, Math.min(height - padding, d.y!))
      })

      linkLine
        .attr('x1', (d) => (d.source as GalaxyNode).x!)
        .attr('y1', (d) => (d.source as GalaxyNode).y!)
        .attr('x2', (d) => (d.target as GalaxyNode).x!)
        .attr('y2', (d) => (d.target as GalaxyNode).y!)

      node.attr('transform', (d) => `translate(${d.x},${d.y})`)
    })

    // Animation loop
    const t0 = performance.now()
    let animId: number

    function animate(now: number) {
      const elapsed = (now - t0) / 1000

      node.select('.orb').each(function (d) {
        if (hoveredNode === d.id) return
        const breath = 1 + Math.sin(elapsed * d.breathSpeed + d.phase) * 0.04
        d3.select(this).attr('r', d.radius * breath)
      })

      node.select('.halo').each(function (d) {
        if (hoveredNode === d.id) return
        const pulse = Math.sin(elapsed * 0.8 + d.phase) * 0.5 + 0.5
        d3.select(this).attr('r', d.radius + 4 + pulse * 4).attr('stroke-opacity', pulse * 0.12)
      })

      node.select('.core').each(function (d) {
        if (hoveredNode === d.id) return
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
        const src = d.link.source as GalaxyNode
        const tgt = d.link.target as GalaxyNode
        if (!src.x || !tgt.x) return
        const x = src.x + (tgt.x - src.x) * d.t
        const y = src.y! + (tgt.y! - src.y!) * d.t
        const edgeFade = Math.sin(d.t * Math.PI)
        const isConnected = hoveredNode && (src.id === hoveredNode || tgt.id === hoveredNode)
        d3.select(this)
          .attr('cx', x).attr('cy', y)
          .attr('opacity', edgeFade * (isConnected ? 0.7 : 0.3))
          .attr('fill', src.color)
      })

      if (simulation.alpha() < 0.01) {
        nodes.forEach((d) => {
          if (d.fx !== null && d.fx !== undefined) return
          d.vx = (d.vx || 0) + (Math.random() - 0.5) * 0.15
          d.vy = (d.vy || 0) + (Math.random() - 0.5) * 0.15
        })
        simulation.alpha(0.015).restart()
      }

      animId = requestAnimationFrame(animate)
    }

    const startTimer = setTimeout(() => {
      animId = requestAnimationFrame(animate)
    }, 1500)

    return () => {
      clearTimeout(startTimer)
      cancelAnimationFrame(animId)
      simulation.stop()
      el.innerHTML = ''
    }
  }, [systems, stats, router, resolvedTheme])

  return (
    <div
      ref={containerRef}
      className="w-full aspect-[16/10] max-h-[600px] rounded-lg overflow-hidden"
    />
  )
}

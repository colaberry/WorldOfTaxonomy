'use client'

import { useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import * as d3 from 'd3'
import { getSystemColor } from '@/lib/colors'
import type { ClassificationSystem, CrosswalkStat } from '@/lib/types'

interface Connection {
  systemId: string
  systemName: string
  edgeCount: number
  exactCount: number
}

interface Props {
  currentSystem: ClassificationSystem
  connections: Connection[]
}

export function CrosswalkNetwork({ currentSystem, connections }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { resolvedTheme } = useTheme()

  useEffect(() => {
    if (!containerRef.current || connections.length === 0) return

    const isDark = resolvedTheme !== 'light'
    const el = containerRef.current
    el.innerHTML = ''

    const width = el.clientWidth
    const height = 280
    const cx = width / 2
    const cy = height / 2
    const orbitR = Math.min(cx - 80, cy - 60, 130)

    const centerColor = currentSystem.tint_color ?? getSystemColor(currentSystem.id)
    const maxEdges = Math.max(...connections.map((c) => c.edgeCount))

    // Radial positions for connected systems
    const positioned = connections.map((c, i) => {
      const angle = (i / connections.length) * 2 * Math.PI - Math.PI / 2
      return {
        ...c,
        x: cx + orbitR * Math.cos(angle),
        y: cy + orbitR * Math.sin(angle),
        color: getSystemColor(c.systemId),
      }
    })

    const svg = d3
      .select(el)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)

    const textColor = isDark ? '#A8A69E' : '#4A4A48'
    const labelColor = isDark ? '#E8E6E1' : '#1A1A1A'

    // Edges first (behind nodes)
    positioned.forEach((c) => {
      const weight = 1 + (c.edgeCount / maxEdges) * 3 // stroke-width 1–4px

      svg
        .append('line')
        .attr('x1', cx).attr('y1', cy)
        .attr('x2', c.x).attr('y2', c.y)
        .attr('stroke', c.color)
        .attr('stroke-opacity', 0.3)
        .attr('stroke-width', weight)

      // Exact match glow on top for edges with high exact counts
      if (c.exactCount > 0) {
        svg
          .append('line')
          .attr('x1', cx).attr('y1', cy)
          .attr('x2', c.x).attr('y2', c.y)
          .attr('stroke', c.color)
          .attr('stroke-opacity', 0.15)
          .attr('stroke-width', weight + 3)
          .attr('stroke-dasharray', '4 4')
      }
    })

    // Satellite nodes
    positioned.forEach((c) => {
      const g = svg
        .append('g')
        .attr('transform', `translate(${c.x},${c.y})`)
        .attr('cursor', 'pointer')
        .on('click', () => router.push(`/system/${c.systemId}`))
        .on('mouseover', function () {
          d3.select(this).select('circle')
            .attr('fill-opacity', 0.35)
            .attr('stroke-opacity', 0.8)
        })
        .on('mouseout', function () {
          d3.select(this).select('circle')
            .attr('fill-opacity', 0.15)
            .attr('stroke-opacity', 0.4)
        })

      g.append('circle')
        .attr('r', 22)
        .attr('fill', c.color)
        .attr('fill-opacity', 0.15)
        .attr('stroke', c.color)
        .attr('stroke-opacity', 0.4)
        .attr('stroke-width', 1.5)

      // System name (abbreviated)
      const shortName = c.systemName.replace(/ \d{4}$/, '').replace('Rev ', 'R')
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('fill', c.color)
        .attr('font-family', "'Geist Mono', monospace")
        .attr('font-size', '9px')
        .attr('pointer-events', 'none')
        .text(shortName.length > 8 ? shortName.slice(0, 7) + '…' : shortName)

      // Edge count below node
      g.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '2.4em')
        .attr('fill', textColor)
        .attr('font-family', "'Geist Mono', monospace")
        .attr('font-size', '9px')
        .attr('pointer-events', 'none')
        .text(c.edgeCount.toLocaleString())
    })

    // Center node (current system)
    const center = svg
      .append('g')
      .attr('transform', `translate(${cx},${cy})`)

    center
      .append('circle')
      .attr('r', 36)
      .attr('fill', centerColor)
      .attr('fill-opacity', 0.2)
      .attr('stroke', centerColor)
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2)

    center
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.3em')
      .attr('fill', centerColor)
      .attr('font-family', "'Instrument Serif', serif")
      .attr('font-size', '12px')
      .attr('pointer-events', 'none')
      .text(currentSystem.name.replace(/ \d{4}$/, ''))

    center
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1em')
      .attr('fill', textColor)
      .attr('font-family', "'Geist Mono', monospace")
      .attr('font-size', '9px')
      .attr('pointer-events', 'none')
      .text(currentSystem.node_count.toLocaleString() + ' codes')

    return () => { el.innerHTML = '' }
  }, [currentSystem, connections, resolvedTheme, router])

  return (
    <div
      ref={containerRef}
      className="w-full"
      style={{ height: 280 }}
    />
  )
}

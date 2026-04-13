'use client'

import { useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import * as d3 from 'd3'
import { getSectorColor } from '@/lib/colors'
import type { ClassificationNode } from '@/lib/types'

interface Props {
  systemId: string
  roots: ClassificationNode[]
}

export function SectorTreemap({ systemId, roots }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { resolvedTheme } = useTheme()

  useEffect(() => {
    if (!containerRef.current || roots.length === 0) return

    const isDark = resolvedTheme !== 'light'
    const el = containerRef.current
    el.innerHTML = ''

    const width = el.clientWidth
    const height = el.clientHeight || 360

    const treemapData = {
      name: systemId,
      children: roots.map((r) => ({
        name: r.title,
        code: r.code,
        value: 1, // equal weight - visual interest comes from color, not size
        color: getSectorColor(r.code),
      })),
    }

    type LeafDatum = { name: string; code: string; value: number; color: string }

    const hierarchy = d3
      .hierarchy<{ name: string; children?: LeafDatum[] }>(treemapData)
      .sum(() => 1)
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))

    d3.treemap<{ name: string; children?: LeafDatum[] }>()
      .size([width, height])
      .paddingInner(3)
      .paddingOuter(0)
      .round(true)(hierarchy)

    const svg = d3
      .select(el)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)

    const leaves = hierarchy.leaves() as unknown as d3.HierarchyRectangularNode<LeafDatum>[]

    const cell = svg
      .selectAll<SVGGElement, d3.HierarchyRectangularNode<LeafDatum>>('g')
      .data(leaves)
      .join('g')
      .attr('transform', (d) => `translate(${d.x0},${d.y0})`)
      .attr('cursor', 'pointer')
      .on('click', (_event, d) => {
        router.push(`/system/${systemId}/node/${encodeURIComponent(d.data.code)}`)
      })

    // Background rectangles
    cell
      .append('rect')
      .attr('width', (d) => Math.max(0, d.x1 - d.x0))
      .attr('height', (d) => Math.max(0, d.y1 - d.y0))
      .attr('fill', (d) => d.data.color)
      .attr('fill-opacity', 0.15)
      .attr('stroke', (d) => d.data.color)
      .attr('stroke-opacity', 0.35)
      .attr('stroke-width', 1)
      .attr('rx', 4)
      .on('mouseover', function (_, d) {
        d3.select(this)
          .attr('fill-opacity', 0.3)
          .attr('stroke-opacity', 0.7)
      })
      .on('mouseout', function () {
        d3.select(this)
          .attr('fill-opacity', 0.15)
          .attr('stroke-opacity', 0.35)
      })

    // Code label (Geist Mono, top-left)
    cell
      .append('text')
      .attr('x', 8)
      .attr('y', 20)
      .attr('fill', isDark ? '#A8A69E' : '#4A4A48')
      .attr('font-family', "'Geist Mono', monospace")
      .attr('font-size', '11px')
      .attr('pointer-events', 'none')
      .text((d) => d.data.code)
      .attr('opacity', (d) => (d.x1 - d.x0 > 45 ? 1 : 0))

    // Title label (Instrument Serif)
    cell
      .append('text')
      .attr('x', 8)
      .attr('y', 38)
      .attr('fill', isDark ? '#E8E6E1' : '#1A1A1A')
      .attr('font-family', "'Instrument Serif', serif")
      .attr('font-size', '12px')
      .attr('pointer-events', 'none')
      .text((d) => {
        const maxChars = Math.floor((d.x1 - d.x0 - 12) / 7)
        return d.data.name.length > maxChars
          ? d.data.name.slice(0, Math.max(0, maxChars - 1)) + '…'
          : d.data.name
      })
      .attr('opacity', (d) => (d.x1 - d.x0 > 80 && d.y1 - d.y0 > 40 ? 1 : 0))

    return () => {
      el.innerHTML = ''
    }
  }, [systemId, roots, resolvedTheme, router])

  return (
    <div
      ref={containerRef}
      className="w-full rounded-xl overflow-hidden border border-border/50"
      style={{ height: 360 }}
    />
  )
}

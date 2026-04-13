'use client'

import { useRef, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import * as d3 from 'd3'
import { useQuery } from '@tanstack/react-query'
import { getCountriesStats } from '@/lib/api'
import type { CountryStat } from '@/lib/api'

// Country name -> ISO 3166-1 alpha-2 lookup
// Covers the names used by the holtzy world.geojson dataset
const NAME_TO_ALPHA2: Record<string, string> = {
  Afghanistan: 'AF', Albania: 'AL', Algeria: 'DZ', Angola: 'AO',
  Argentina: 'AR', Armenia: 'AM', Australia: 'AU', Austria: 'AT',
  Azerbaijan: 'AZ', Bahrain: 'BH', Bangladesh: 'BD', Belarus: 'BY',
  Belgium: 'BE', Benin: 'BJ', Bolivia: 'BO', 'Bosnia and Herzegovina': 'BA',
  Botswana: 'BW', Brazil: 'BR', Bulgaria: 'BG', 'Burkina Faso': 'BF',
  Burundi: 'BI', Cambodia: 'KH', Cameroon: 'CM', Canada: 'CA',
  'Central African Republic': 'CF', Chad: 'TD', Chile: 'CL', China: 'CN',
  Colombia: 'CO', Congo: 'CG', 'Costa Rica': 'CR', Croatia: 'HR',
  Cuba: 'CU', Cyprus: 'CY', 'Czech Republic': 'CZ', 'Czechia': 'CZ',
  'Democratic Republic of the Congo': 'CD', Denmark: 'DK', Djibouti: 'DJ',
  'Dominican Republic': 'DO', Ecuador: 'EC', Egypt: 'EG',
  'El Salvador': 'SV', Eritrea: 'ER', Estonia: 'EE', Ethiopia: 'ET',
  Finland: 'FI', France: 'FR', Gabon: 'GA', Georgia: 'GE', Germany: 'DE',
  Ghana: 'GH', Greece: 'GR', Guatemala: 'GT', Guinea: 'GN',
  'Guinea-Bissau': 'GW', Haiti: 'HT', Honduras: 'HN', Hungary: 'HU',
  Iceland: 'IS', India: 'IN', Indonesia: 'ID', Iran: 'IR', Iraq: 'IQ',
  Ireland: 'IE', Israel: 'IL', Italy: 'IT', Jamaica: 'JM', Japan: 'JP',
  Jordan: 'JO', Kazakhstan: 'KZ', Kenya: 'KE', Kuwait: 'KW',
  Kyrgyzstan: 'KG', Laos: 'LA', Latvia: 'LV', Lebanon: 'LB',
  Lesotho: 'LS', Liberia: 'LR', Libya: 'LY', Lithuania: 'LT',
  Luxembourg: 'LU', Madagascar: 'MG', Malawi: 'MW', Malaysia: 'MY',
  Mali: 'ML', Mauritania: 'MR', Mexico: 'MX', Moldova: 'MD',
  Mongolia: 'MN', Morocco: 'MA', Mozambique: 'MZ', Myanmar: 'MM',
  Namibia: 'NA', Nepal: 'NP', Netherlands: 'NL',
  'New Zealand': 'NZ', Nicaragua: 'NI', Niger: 'NE', Nigeria: 'NG',
  'North Korea': 'KP', 'North Macedonia': 'MK', Norway: 'NO', Oman: 'OM',
  Pakistan: 'PK', Panama: 'PA', 'Papua New Guinea': 'PG', Paraguay: 'PY',
  Peru: 'PE', Philippines: 'PH', Poland: 'PL', Portugal: 'PT',
  Qatar: 'QA', Romania: 'RO', Russia: 'RU', Rwanda: 'RW',
  'Saudi Arabia': 'SA', Senegal: 'SN', Serbia: 'RS',
  'Sierra Leone': 'SL', Slovakia: 'SK', Slovenia: 'SI', Somalia: 'SO',
  'South Africa': 'ZA', 'South Korea': 'KR', 'South Sudan': 'SS',
  Spain: 'ES', 'Sri Lanka': 'LK', Sudan: 'SD', Suriname: 'SR',
  Sweden: 'SE', Switzerland: 'CH', Syria: 'SY', Taiwan: 'TW',
  Tajikistan: 'TJ', Tanzania: 'TZ', Thailand: 'TH', Togo: 'TG',
  Tunisia: 'TN', Turkey: 'TR', Turkmenistan: 'TM', Uganda: 'UG',
  Ukraine: 'UA', 'United Arab Emirates': 'AE', 'United Kingdom': 'GB',
  'United States of America': 'US', 'United States': 'US', Uruguay: 'UY',
  Uzbekistan: 'UZ', Venezuela: 'VE', Vietnam: 'VN', Yemen: 'YE',
  Zambia: 'ZM', Zimbabwe: 'ZW', Kosovo: 'XK', Palestine: 'PS',
  'Western Sahara': 'EH', Greenland: 'GL', 'Puerto Rico': 'PR',
  'New Caledonia': 'NC', 'French Guiana': 'GF',
}

interface GeoFeature {
  type: string
  properties: { name: string }
  geometry: { type: string; coordinates: unknown[] }
}

interface WorldGeoJSON {
  type: string
  features: GeoFeature[]
}

interface TooltipState {
  x: number
  y: number
  name: string
  code: string
  stat: CountryStat | null
}

export function WorldMap() {
  const containerRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const { resolvedTheme } = useTheme()
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)

  const { data: statsArray } = useQuery({
    queryKey: ['countries-stats'],
    queryFn: getCountriesStats,
    staleTime: 5 * 60 * 1000,
    retry: 1,
    // Return empty array on error so the map still renders (all grey)
    placeholderData: [],
  })

  // Build lookup map
  const statsMap = new Map<string, CountryStat>()
  statsArray?.forEach((s) => statsMap.set(s.country_code, s))

  useEffect(() => {
    if (!containerRef.current) return

    const el = containerRef.current
    el.innerHTML = ''

    const isDark = resolvedTheme === 'dark'
    const width = el.clientWidth || 800
    const height = Math.round(width * 0.5)

    // Colors
    const bgColor = isDark ? '#0a0a0a' : '#f1f5f9'
    const oceanColor = isDark ? '#0f172a' : '#dbeafe'
    const landBase = isDark ? '#1e293b' : '#cbd5e1'
    const borderColor = isDark ? '#334155' : '#94a3b8'
    const highlightColor = isDark ? '#3b82f6' : '#2563eb'
    const officialColor = isDark ? '#22c55e' : '#16a34a'
    const textColor = isDark ? '#e2e8f0' : '#1e293b'

    const svg = d3
      .select(el)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('border-radius', '0.5rem')
      .style('background', bgColor)

    const projection = d3
      .geoNaturalEarth1()
      .scale(width / 6.28)
      .translate([width / 2, height / 2])

    const pathGen = d3.geoPath().projection(projection)

    // Ocean background
    svg
      .append('rect')
      .attr('width', width)
      .attr('height', height)
      .attr('fill', oceanColor)
      .attr('rx', 8)

    const g = svg.append('g')

    // Load GeoJSON
    fetch('/world-110m.json')
      .then((r) => r.json())
      .then((geo: WorldGeoJSON) => {
        // Draw countries
        g.selectAll('path')
          .data(geo.features)
          .enter()
          .append('path')
          .attr('d', (d) => pathGen(d as unknown as d3.GeoPermissibleObjects) || '')
          .attr('fill', (d) => {
            const alpha2 = NAME_TO_ALPHA2[d.properties.name]
            if (!alpha2) return landBase
            const stat = statsMap.get(alpha2)
            if (!stat) return landBase
            if (stat.has_official) return officialColor
            if (stat.system_count >= 2) return highlightColor
            return isDark ? '#475569' : '#94a3b8'
          })
          .attr('stroke', borderColor)
          .attr('stroke-width', 0.4)
          .style('cursor', (d) => {
            const alpha2 = NAME_TO_ALPHA2[d.properties.name]
            return alpha2 && statsMap.has(alpha2) ? 'pointer' : 'default'
          })
          .on('mouseenter', function (event: MouseEvent, d: GeoFeature) {
            const alpha2 = NAME_TO_ALPHA2[d.properties.name]
            const stat = alpha2 ? statsMap.get(alpha2) ?? null : null
            d3.select(this).attr('stroke-width', 1.2).attr('stroke', isDark ? '#94a3b8' : '#1e293b')
            const rect = el.getBoundingClientRect()
            setTooltip({
              x: event.clientX - rect.left,
              y: event.clientY - rect.top,
              name: d.properties.name,
              code: alpha2 || '',
              stat,
            })
          })
          .on('mousemove', function (event: MouseEvent) {
            const rect = el.getBoundingClientRect()
            setTooltip((prev) =>
              prev ? { ...prev, x: event.clientX - rect.left, y: event.clientY - rect.top } : null
            )
          })
          .on('mouseleave', function () {
            d3.select(this).attr('stroke-width', 0.4).attr('stroke', borderColor)
            setTooltip(null)
          })
          .on('click', function (_event: MouseEvent, d: GeoFeature) {
            const alpha2 = NAME_TO_ALPHA2[d.properties.name]
            if (alpha2 && statsMap.has(alpha2)) {
              router.push(`/country/${alpha2}`)
            }
          })
      })
      .catch(() => {
        // GeoJSON failed - show fallback message
        svg
          .append('text')
          .attr('x', width / 2)
          .attr('y', height / 2)
          .attr('text-anchor', 'middle')
          .attr('fill', textColor)
          .attr('font-size', 14)
          .text('World map unavailable')
      })

    return () => {
      el.innerHTML = ''
    }
  }, [resolvedTheme, statsMap.size, statsArray]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="w-full space-y-3">
      {/* Legend */}
      <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-green-500" />
          Has official national standard
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-blue-500" />
          Regional / UN coverage
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-slate-400" />
          UN recommended only
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-sm bg-slate-700 dark:bg-slate-700" />
          No data yet
        </span>
      </div>

      {/* Map container */}
      <div className="relative w-full rounded-lg overflow-hidden border border-border/50">
        <div ref={containerRef} className="w-full" style={{ minHeight: 320 }} />

        {/* Tooltip */}
        {tooltip && (
          <div
            className="pointer-events-none absolute z-10 rounded-md border border-border bg-popover px-3 py-2 text-xs shadow-md"
            style={{
              left: tooltip.x + 12,
              top: tooltip.y - 8,
              transform: tooltip.x > (containerRef.current?.clientWidth ?? 600) * 0.7
                ? 'translateX(-110%)'
                : undefined,
            }}
          >
            <p className="font-semibold text-foreground">
              {tooltip.name}
              {tooltip.code && (
                <span className="ml-1 font-mono text-muted-foreground">({tooltip.code})</span>
              )}
            </p>
            {tooltip.stat ? (
              <div className="mt-1 space-y-0.5 text-muted-foreground">
                <p>{tooltip.stat.system_count} classification {tooltip.stat.system_count === 1 ? 'system' : 'systems'}</p>
                {tooltip.stat.has_official && <p className="text-green-500">Has official national standard</p>}
                {tooltip.stat.sector_strength_count > 0 && (
                  <p>{tooltip.stat.sector_strength_count} sector {tooltip.stat.sector_strength_count === 1 ? 'strength' : 'strengths'}</p>
                )}
                {tooltip.code && <p className="text-primary/70 mt-1">Click to explore</p>}
              </div>
            ) : (
              <p className="mt-1 text-muted-foreground">No taxonomy data yet</p>
            )}
          </div>
        )}
      </div>

      {/* Caption */}
      {statsArray && (
        <p className="text-center text-xs text-muted-foreground">
          {statsArray.length} countries covered &middot; click any country to explore its taxonomy profile
        </p>
      )}
    </div>
  )
}

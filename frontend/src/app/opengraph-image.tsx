import { ImageResponse } from 'next/og'

export const alt = 'World Of Taxonomy - Global Classification Knowledge Graph'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '72px 80px',
          backgroundColor: '#0a0a0a',
          color: '#ffffff',
          fontFamily: 'sans-serif',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: '#a855f7',
            }}
          />
          <div style={{ fontSize: '26px', fontWeight: 700 }}>
            World Of Taxonomy
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            style={{
              fontSize: '76px',
              fontWeight: 800,
              lineHeight: 1.05,
              color: '#ffffff',
            }}
          >
            Every classification,
          </div>
          <div
            style={{
              fontSize: '76px',
              fontWeight: 800,
              lineHeight: 1.05,
              color: '#c4b5fd',
            }}
          >
            every code, mapped.
          </div>
          <div
            style={{
              fontSize: '26px',
              color: '#a1a1aa',
              marginTop: '8px',
            }}
          >
            1,000+ systems. 1.2M+ codes. 321K+ crosswalk edges.
          </div>
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '22px',
            color: '#71717a',
          }}
        >
          <div>worldoftaxonomy.com</div>
          <div>NAICS · ISIC · NACE · HS · ICD · SOC</div>
        </div>
      </div>
    ),
    { ...size },
  )
}

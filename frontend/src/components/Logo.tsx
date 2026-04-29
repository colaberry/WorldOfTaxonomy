import Image from 'next/image'

type Variant = 'mark' | 'lockup'

type LogoProps = {
  /** "mark" = WoT glyph only (square-ish). "lockup" = mark + WORLDOFTAXONOMY wordmark. */
  variant?: Variant
  /** Pixel height. Width is computed from the SVG aspect ratio. */
  height?: number
  className?: string
  /** Override aria-label. Defaults to "WorldOfTaxonomy". */
  alt?: string
  /** Force a specific theme variant; by default we render both and let CSS pick the right one. */
  forceTheme?: 'light' | 'dark'
}

// Native viewBox aspect ratios baked at export time:
//   mark   = 1086 × 545
//   lockup = 2400 × 545
const ASPECT: Record<Variant, number> = {
  mark: 1086 / 545,
  lockup: 2400 / 545,
}

/**
 * WorldOfTaxonomy logo component.
 *
 * Aleem ships two monochrome variants per shape:
 *   /logo-{variant}-mono-black.svg  (W/T strokes are #141414, cyan globe stays cyan)  → light theme
 *   /logo-{variant}-mono-white.svg  (W/T strokes are #FFFFFF, cyan globe stays cyan)  → dark theme
 *
 * We render BOTH and let Tailwind's `dark:` variant flip visibility — no JS hook,
 * no FOUC, no client-only rendering. The cyan globe is consistent across both.
 */
export function Logo({
  variant = 'mark',
  height = 24,
  className = '',
  alt = 'WorldOfTaxonomy',
  forceTheme,
}: LogoProps) {
  const width = Math.round(height * ASPECT[variant])
  const dark = `/logo-${variant}-mono-white.svg`
  const light = `/logo-${variant}-mono-black.svg`

  if (forceTheme === 'dark') {
    return (
      <Image src={dark} alt={alt} width={width} height={height} className={className} priority unoptimized />
    )
  }
  if (forceTheme === 'light') {
    return (
      <Image src={light} alt={alt} width={width} height={height} className={className} priority unoptimized />
    )
  }

  return (
    <>
      <Image
        src={light}
        alt={alt}
        width={width}
        height={height}
        className={`block dark:hidden ${className}`}
        priority
        unoptimized
      />
      <Image
        src={dark}
        alt={alt}
        width={width}
        height={height}
        className={`hidden dark:block ${className}`}
        priority
        unoptimized
      />
    </>
  )
}

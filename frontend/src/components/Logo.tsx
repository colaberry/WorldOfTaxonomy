import Image from 'next/image'

type Variant = 'mark' | 'lockup'

type LogoProps = {
  /** "mark" = WoT glyph only (square-ish). "lockup" = mark + WorldOfTaxonomy wordmark. */
  variant?: Variant
  /** Pixel height. Width is computed from the SVG aspect ratio. */
  height?: number
  /** Applied to the outer <span> wrapper (use this for responsive `hidden sm:flex` etc.). */
  className?: string
  /** Override aria-label. Defaults to "World Of Taxonomy". */
  alt?: string
  /** Force a specific theme variant; by default we render both and let CSS pick the right one. */
  forceTheme?: 'light' | 'dark'
}

// Native viewBox aspect ratios baked at export time.
//   mark   = 1086 x 545   (~1.99 : 1, square-ish glyph)
//   lockup = 790 x 105    (~7.52 : 1, mark + WorldOfTaxonomy wordmark on one row)
// Aleem v2 (2026-05-08) updated the lockup wordmark from all-caps
// "WORLDOFTAXONOMY" to mixed-case "WorldOfTaxonomy" per Ram's feedback that
// the all-caps treatment competed with the mark for visual focus. The
// viewBox went from 1038 x 95 to 790 x 105 because the new wordmark uses
// Geist Medium with 0.2em tracking and slightly taller cap height.
// Components that set `height` on a Logo with `variant="lockup"` must keep
// the height modest (~20-28 px in a typical header) - the computed width
// is height x 7.52, which can crowd the navbar at larger heights.
const ASPECT: Record<Variant, number> = {
  mark: 1086 / 545,
  lockup: 790 / 105,
}

/**
 * World Of Taxonomy logo component.
 *
 * Aleem ships two monochrome variants per shape:
 *   /logo-{variant}-mono-black.svg  (W/T strokes are #141414, cyan globe stays cyan)  → light theme
 *   /logo-{variant}-mono-white.svg  (W/T strokes are #FFFFFF, cyan globe stays cyan)  → dark theme
 *
 * We render BOTH inside an outer <span> and let Tailwind's `dark:` variant flip
 * which inner image is visible. The OUTER span owns responsive visibility (e.g.
 * `hidden sm:flex`); the INNER images own theme visibility. They live on
 * different elements so display utilities never collide. No JS hook, no FOUC,
 * no client-only rendering.
 */
export function Logo({
  variant = 'mark',
  height = 24,
  className = '',
  alt = 'World Of Taxonomy',
  forceTheme,
}: LogoProps) {
  const width = Math.round(height * ASPECT[variant])
  const dark = `/logo-${variant}-mono-white.svg`
  const light = `/logo-${variant}-mono-black.svg`

  if (forceTheme) {
    const src = forceTheme === 'dark' ? dark : light
    return (
      <Image
        src={src}
        alt={alt}
        width={width}
        height={height}
        className={className}
        priority
        unoptimized
      />
    )
  }

  // Outer wrapper carries responsive visibility from the consumer's className.
  // Inner images carry ONLY theme visibility - no class collision possible.
  // `inline-flex items-center` keeps the wrapper sized to the visible img.
  const wrapperBase = 'inline-flex items-center shrink-0'

  return (
    <span className={`${wrapperBase} ${className}`.trim()}>
      <Image
        src={light}
        alt={alt}
        width={width}
        height={height}
        className="block dark:hidden h-auto w-auto"
        style={{ height }}
        priority
        unoptimized
      />
      <Image
        src={dark}
        alt={alt}
        width={width}
        height={height}
        className="hidden dark:block h-auto w-auto"
        style={{ height }}
        priority
        unoptimized
      />
    </span>
  )
}

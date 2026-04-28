import Link from 'next/link'
import { Globe, GitFork } from 'lucide-react'

const EXPLORE_LINKS = [
  { href: '/',           label: 'Home' },
  { href: '/explore',    label: 'Search codes' },
  { href: '/explore',    label: 'Browse systems' },
  { href: '/blog',       label: 'Blog' },
  { href: '/developers', label: 'Builders' },
]

const DEVELOPER_LINKS = [
  { href: 'https://github.com/colaberry/WorldOfTaxonomy',        label: 'GitHub repository', external: true },
  { href: '/api',                                                  label: 'REST API reference', external: false },
  { href: '/mcp',                                                  label: 'MCP tools', external: false },
  { href: '/developers/signup',                                    label: 'Get an API key', external: false },
  { href: '/pricing',                                              label: 'Pricing', external: false },
  { href: '/developers#contact',                                   label: 'Contact sales', external: false },
  { href: 'https://github.com/colaberry/WorldOfTaxonomy/issues', label: 'Report an issue', external: true },
]

const LEGAL_LINKS = [
  { href: '/legal/terms',       label: 'Terms of service' },
  { href: '/legal/privacy',     label: 'Privacy policy' },
  { href: '/legal/attribution', label: 'Source attribution' },
]

export function Footer() {
  return (
    <footer className="border-t border-border/50 bg-card/40 mt-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-8">

          {/* Brand */}
          <div className="space-y-3">
            <Link href="/" className="flex items-center gap-2 text-foreground font-semibold w-fit">
              <Globe className="h-4 w-4 text-primary" />
              World Of Taxonomy
            </Link>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-xs">
              A unified knowledge graph connecting 1,000+ classification systems across
              industry, geography, health, occupations, trade, and more.
            </p>
            <Link
              href="https://github.com/colaberry/WorldOfTaxonomy"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <GitFork className="h-3.5 w-3.5" />
              Open source on GitHub
            </Link>
          </div>

          {/* Explore */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Explore</p>
            <ul className="space-y-2">
              {EXPLORE_LINKS.map(({ href, label }) => (
                <li key={label}>
                  <Link
                    href={href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Developers */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Developers</p>
            <ul className="space-y-2">
              {DEVELOPER_LINKS.map(({ href, label, external }) => (
                <li key={href}>
                  <Link
                    href={href}
                    target={external ? '_blank' : undefined}
                    rel={external ? 'noopener noreferrer' : undefined}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Legal</p>
            <ul className="space-y-2">
              {LEGAL_LINKS.map(({ href, label }) => (
                <li key={href}>
                  <Link
                    href={href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

        </div>

        {/* Bottom bar */}
        <div className="mt-8 pt-6 border-t border-border/40 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <span>World Of Taxonomy - Unified Global Classification Knowledge Graph</span>
          <span>1,000+ systems - 1.2M+ nodes - 321K+ edges</span>
        </div>

        {/* Disclaimer */}
        <div className="mt-4 pt-4 border-t border-border/30 text-center">
          <p className="text-[11px] text-muted-foreground/70 leading-relaxed max-w-2xl mx-auto">
            Data is provided for informational purposes only. We do not guarantee accuracy or completeness. Use at your own risk. For authoritative codes, consult the official source.
          </p>
        </div>
      </div>
    </footer>
  )
}

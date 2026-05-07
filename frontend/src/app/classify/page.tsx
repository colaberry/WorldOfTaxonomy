import type { Metadata } from 'next'
import { ClassifyTool } from './ClassifyTool'

export const metadata: Metadata = {
  title: 'Classify My Business - World Of Taxonomy',
  description:
    'Find NAICS, ISIC, SIC, NACE, and SOC codes for any business, product, ' +
    'or occupation. Free cross-system classification across 1,000+ taxonomy systems.',
  openGraph: {
    title: 'Classify My Business - World Of Taxonomy',
    description:
      'Find the right industry and occupation codes for your business ' +
      'across NAICS, ISIC, SIC, NACE, and SOC.',
    url: 'https://worldoftaxonomy.com/classify',
    type: 'website',
  },
  alternates: {
    canonical: 'https://worldoftaxonomy.com/classify',
  },
}

export default function ClassifyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Classify My Business
        </h1>
        <p className="text-lg text-muted-foreground">
          Describe your business, product, or occupation in plain English.
          We return the matching codes across the major industry and
          occupation classification systems.
        </p>
      </header>

      <ClassifyTool />

      <section className="pt-8 border-t border-border space-y-4">
        <h2 className="text-xl font-semibold">What you get</h2>
        <p className="text-sm text-muted-foreground">
          Three tiers, three depths of breadth. Sign-in is free; Pro unlocks
          API and MCP access plus the curated domain taxonomies.
        </p>
        <div className="grid sm:grid-cols-3 gap-3 text-sm">
          <div className="rounded-lg border border-border bg-card p-4 space-y-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Without an account
            </div>
            <div className="text-foreground font-medium">5 systems</div>
            <ul className="text-muted-foreground space-y-1 text-xs">
              <li>NAICS (US), ISIC (UN), SIC (US), NACE (EU), SOC (US occupations)</li>
              <li>Top 3 matches per system</li>
              <li>Cross-system context</li>
            </ul>
          </div>
          <div className="rounded-lg border border-primary/40 bg-card p-4 space-y-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-primary">
              Free with sign-in
            </div>
            <div className="text-foreground font-medium">10 systems</div>
            <ul className="text-muted-foreground space-y-1 text-xs">
              <li>Anon set + HS, CPC, UNSPSC (trade & products)</li>
              <li>+ ICD-11 (health), ISCO-08 (international occupations)</li>
              <li>Top 5 matches per system</li>
            </ul>
            <a href="/login" className="inline-block text-xs text-primary underline">
              Sign in free
            </a>
          </div>
          <div className="rounded-lg border border-border bg-card p-4 space-y-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Pro / Enterprise
            </div>
            <div className="text-foreground font-medium">All 1,000+ systems</div>
            <ul className="text-muted-foreground space-y-1 text-xs">
              <li>Full standards surface + 419 curated domain taxonomies</li>
              <li>Up to 20 matches per system, full crosswalk edges</li>
              <li>REST API + MCP server for AI agents</li>
            </ul>
            <a href="/pricing" className="inline-block text-xs text-primary underline">
              See pricing
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}

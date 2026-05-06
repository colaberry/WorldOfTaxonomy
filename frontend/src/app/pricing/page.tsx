import Link from 'next/link'
import type { Metadata } from 'next'
import { Zap, ArrowRight } from 'lucide-react'
import { PricingTiers } from './PricingTiers'

export const metadata: Metadata = {
  title: 'Pricing - World Of Taxonomy',
  description:
    'Free, Pro ($49/mo), and Enterprise plans for the World Of Taxonomy classification API and MCP server. /classify metered overage at $0.05/call above the 200/day Pro bucket.',
  openGraph: {
    title: 'Pricing - World Of Taxonomy',
    description:
      'Free, Pro ($49/mo), and Enterprise plans for the World Of Taxonomy classification API and MCP server.',
    url: 'https://worldoftaxonomy.com/pricing',
    type: 'website',
  },
  alternates: {
    canonical: 'https://worldoftaxonomy.com/pricing',
  },
}

export default function PricingPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-16">

      {/* Hero */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-border/60 bg-secondary/50 text-xs text-muted-foreground font-medium">
          <Zap className="h-3.5 w-3.5 text-primary" />
          Pricing
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Start free, scale as you grow
        </h1>
        <p className="text-muted-foreground text-base max-w-xl mx-auto leading-relaxed">
          The full knowledge graph is available on every plan. Pro adds higher
          limits, the /classify API, MCP HTTP-mode, bulk export, and email
          support. Cancel anytime.
        </p>
      </div>

      {/* Tier cards (interactive) */}
      <PricingTiers />

      {/* FAQ */}
      <div className="space-y-6">
        <h2 className="text-lg font-semibold tracking-tight text-center">Frequently asked questions</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {[
            {
              q: 'Is the free tier actually free?',
              a: 'Yes. Search, browse, translate, MCP stdio mode, and 20 /classify calls per day at no cost. Rate limits apply (200 req/min authenticated, 50,000 per day) to keep the service reliable.',
            },
            {
              q: 'What is /classify overage?',
              a: 'Pro includes 200 /classify calls per day. If you exceed that on a given day, additional calls succeed (no hard cap) and we add $0.05 per overage call to your next monthly invoice via Stripe metered billing.',
            },
            {
              q: 'Can I cancel anytime?',
              a: 'Yes. Cancel from the Stripe Customer Portal (linked from /developers/keys after you sign up). You keep Pro until the end of your current billing period; no future charges. No refunds for partial periods.',
            },
            {
              q: 'Can I self-host instead?',
              a: 'Absolutely. The entire project is MIT-licensed open source. Clone the repo, bring your own PostgreSQL, run the ingesters, and you have full control with no rate limits.',
            },
            {
              q: 'What MCP clients are supported?',
              a: 'Any MCP-compatible client - Claude Desktop, Claude Code, Cursor, VS Code, Windsurf, and more. Pro includes hosted MCP HTTP mode so you can connect from clients that do not run a local stdio server.',
            },
            {
              q: 'How are payments processed?',
              a: 'Stripe handles all card processing. We never see your card number. Cards are stored by Stripe; we store only a customer ID. PCI compliance is Stripe’s problem, not yours.',
            },
          ].map(({ q, a }) => (
            <div key={q} className="p-4 rounded-xl border border-border/50 bg-card space-y-2">
              <p className="text-sm font-medium">{q}</p>
              <p className="text-xs text-muted-foreground leading-relaxed">{a}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="rounded-xl border border-border/50 bg-card p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="font-semibold">Need something custom?</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Tell us about your use case and we&apos;ll put together an Enterprise plan that fits.
          </p>
        </div>
        <Link
          href="/contact?subject=enterprise"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shrink-0"
        >
          Contact us <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  )
}

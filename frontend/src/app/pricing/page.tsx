import Link from 'next/link'
import type { Metadata } from 'next'
import {
  Check, Zap, ArrowRight, Building2, Users, Rocket,
} from 'lucide-react'

export const metadata: Metadata = {
  title: 'Pricing - WorldOfTaxonomy',
  description:
    'Free, Pro, and Enterprise plans for the WorldOfTaxonomy classification API and MCP server.',
  openGraph: {
    title: 'Pricing - WorldOfTaxonomy',
    description:
      'Free, Pro, and Enterprise plans for the WorldOfTaxonomy classification API and MCP server.',
    url: 'https://worldoftaxonomy.com/pricing',
    type: 'website',
  },
  alternates: {
    canonical: 'https://worldoftaxonomy.com/pricing',
  },
}

const TIERS = [
  {
    name: 'Free',
    icon: Users,
    tagline: 'For exploration and prototyping',
    features: [
      'Full search and browse',
      'All 1,000+ systems',
      'Crosswalk translations',
      'MCP server access',
      'Community support',
    ],
    cta: 'Get a free API key',
    ctaHref: '/developers/signup',
    highlighted: false,
  },
  {
    name: 'Pro',
    icon: Rocket,
    tagline: 'For production applications',
    features: [
      'Everything in Free',
      'Higher rate limits',
      'Classify API (free-text to codes)',
      'JSONL bulk export',
      'Unlimited MCP usage',
      'Email support',
      'SLA guarantee',
    ],
    cta: 'Join the waitlist',
    ctaHref: '#waitlist',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    icon: Building2,
    tagline: 'For teams and organizations',
    features: [
      'Everything in Pro',
      'Unlimited requests',
      'Custom export formats',
      'Dedicated support',
      'Custom SLA',
      'On-premise deployment option',
      'Priority feature requests',
    ],
    cta: 'Contact us',
    ctaHref: '/developers#contact',
    highlighted: false,
  },
]

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
          The full knowledge graph is available on every plan. Paid tiers add higher
          limits, bulk export, classification API, and dedicated support.
        </p>
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-xs text-amber-700 dark:text-amber-300 font-medium">
          Public beta - all plans free while we finalize pricing.
        </div>
      </div>

      {/* Tier cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {TIERS.map((tier) => {
          const Icon = tier.icon
          return (
            <div
              key={tier.name}
              className={`rounded-xl border p-6 flex flex-col gap-5 ${
                tier.highlighted
                  ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                  : 'border-border/50 bg-card'
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Icon className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">{tier.name}</h2>
                </div>
                <p className="text-sm text-muted-foreground">{tier.tagline}</p>
              </div>

              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-muted-foreground/60">
                  Coming soon
                </span>
              </div>

              <ul className="space-y-2.5 flex-1">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm">
                    <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                    <span className="text-muted-foreground">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={tier.ctaHref}
                className={`block text-center px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  tier.highlighted
                    ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                {tier.cta}
              </Link>
            </div>
          )
        })}
      </div>

      {/* FAQ / clarifications */}
      <div className="space-y-6">
        <h2 className="text-lg font-semibold tracking-tight text-center">Frequently asked questions</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {[
            {
              q: 'Is the free tier actually free?',
              a: 'Yes. Search, browse, translate, and use the MCP server at no cost. Rate limits apply to keep the service reliable for everyone.',
            },
            {
              q: 'Can I self-host instead?',
              a: 'Absolutely. The entire project is MIT-licensed open source. Clone the repo, bring your own PostgreSQL, and you have full control with no limits.',
            },
            {
              q: 'What MCP clients are supported?',
              a: 'Any MCP-compatible client works - Claude Desktop, Claude Code, Cursor, VS Code, Windsurf, and more. The protocol is an open standard.',
            },
            {
              q: 'When will pricing be announced?',
              a: 'We are finalizing pricing based on infrastructure costs. Join the waitlist or follow us on GitHub to be notified when paid plans go live.',
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
            Tell us about your use case and we&apos;ll put together a plan that fits.
          </p>
        </div>
        <Link
          href="/developers#contact"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shrink-0"
        >
          Contact us <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  )
}

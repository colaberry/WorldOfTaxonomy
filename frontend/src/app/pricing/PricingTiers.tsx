'use client'

// Interactive pricing-tier cards. Server page (page.tsx) renders the
// hero + FAQ; this component owns the cards plus the Subscribe buttons
// that POST to /api/v1/billing/checkout.
//
// Pricing locked 2026-05-04 (project_pricing_tiers.md). Do NOT freelance
// the numbers; update the memory entry first if a price changes.

import Link from 'next/link'
import { useState } from 'react'
import { Check, Building2, Users, Rocket } from 'lucide-react'

type Plan = 'pro_monthly' | 'pro_annual'

function getCsrfToken(): string {
  const match = typeof document !== 'undefined'
    ? document.cookie.match(/(?:^|; )wot_csrf=([^;]+)/)
    : null
  return match ? decodeURIComponent(match[1]) : ''
}

export function PricingTiers() {
  const [subscribing, setSubscribing] = useState<Plan | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function startCheckout(plan: Plan) {
    setSubscribing(plan)
    setError(null)
    try {
      const res = await fetch('/api/v1/billing/checkout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCsrfToken(),
        },
        body: JSON.stringify({ plan }),
      })
      if (res.status === 401) {
        // Not signed in - send through magic-link flow, then back here
        window.location.replace('/login?next=/pricing')
        return
      }
      if (res.status === 409) {
        // Already Pro
        window.location.replace('/developers/keys?already_pro=1')
        return
      }
      if (!res.ok) {
        const detail = await res.text()
        throw new Error(detail || `HTTP ${res.status}`)
      }
      const { checkout_url } = await res.json()
      if (!checkout_url) {
        throw new Error('No checkout URL returned.')
      }
      window.location.href = checkout_url
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Subscribe failed.')
      setSubscribing(null)
    }
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {/* Free */}
        <div className="rounded-xl border border-border/50 bg-card p-6 flex flex-col gap-5">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">Free</h2>
            </div>
            <p className="text-sm text-muted-foreground">For exploration and prototyping</p>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold">$0</span>
            <span className="text-sm text-muted-foreground">/ month</span>
          </div>
          <ul className="space-y-2.5 flex-1 text-sm">
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">200 req/min authenticated</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">All read endpoints</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Crosswalk translations</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">20 /classify calls/day</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">MCP server (stdio mode)</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Community support</span></li>
          </ul>
          <Link
            href="/login"
            className="block text-center px-4 py-2.5 rounded-lg text-sm font-medium bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
          >
            Get started free
          </Link>
        </div>

        {/* Pro (highlighted) */}
        <div className="rounded-xl border border-primary bg-primary/5 ring-1 ring-primary/20 p-6 flex flex-col gap-5 relative">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-medium px-2 py-0.5 rounded-full">
            Most popular
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Rocket className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">Pro</h2>
            </div>
            <p className="text-sm text-muted-foreground">For production applications</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold">$49</span>
              <span className="text-sm text-muted-foreground">/ month</span>
            </div>
            <p className="text-xs text-muted-foreground">
              or <span className="font-medium text-foreground">$490 / year</span>
              <span className="text-primary ml-1">(save 17%)</span>
            </p>
          </div>
          <ul className="space-y-2.5 flex-1 text-sm">
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">5,000 req/min, unlimited daily</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">200 /classify calls/day included</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">$0.05/call overage (no hard cap)</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">MCP HTTP-mode (hosted)</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Bulk JSON export per system</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Webhook notifications</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Per-key analytics dashboard</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Email support, 14-day trial</span></li>
          </ul>
          <div className="space-y-2">
            <button
              type="button"
              onClick={() => startCheckout('pro_monthly')}
              disabled={subscribing !== null}
              className="block w-full text-center px-4 py-2.5 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {subscribing === 'pro_monthly'
                ? 'Redirecting to Stripe...'
                : 'Subscribe monthly - $49/mo'}
            </button>
            <button
              type="button"
              onClick={() => startCheckout('pro_annual')}
              disabled={subscribing !== null}
              className="block w-full text-center px-4 py-2.5 rounded-lg text-sm font-medium border border-primary text-primary bg-transparent hover:bg-primary/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {subscribing === 'pro_annual'
                ? 'Redirecting to Stripe...'
                : 'Subscribe annually - $490/yr'}
            </button>
          </div>
        </div>

        {/* Enterprise */}
        <div className="rounded-xl border border-border/50 bg-card p-6 flex flex-col gap-5">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">Enterprise</h2>
            </div>
            <p className="text-sm text-muted-foreground">For teams and organizations</p>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold">Contact us</span>
          </div>
          <ul className="space-y-2.5 flex-1 text-sm">
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">50,000+ req/min, custom</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Unlimited /classify</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">99.9% SLA</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Private classification systems</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Audit log export</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Dedicated support channel</span></li>
            <li className="flex items-start gap-2.5"><Check className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-muted-foreground">Annual contract, invoiced</span></li>
          </ul>
          <Link
            href="/contact?subject=enterprise"
            className="block text-center px-4 py-2.5 rounded-lg text-sm font-medium bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
          >
            Contact us
          </Link>
        </div>
      </div>
    </div>
  )
}

'use client'

// Billing panel for the API-key dashboard.
//
// Shows the current tier, classify usage today, and the right CTA based
// on tier:
//   free        -> "Upgrade to Pro" -> /pricing
//   pro         -> "Manage subscription" -> /api/v1/billing/portal -> Stripe
//   enterprise  -> "Contact us" (Enterprise has no portal flow)
//
// Pricing locked 2026-05-04 (project_pricing_tiers.md). The 200/day Pro
// classify bucket is hardcoded both here and in the daily overage cron;
// if it changes, update both plus the memory entry.

import Link from 'next/link'
import { useEffect, useState } from 'react'

const PRO_INCLUDED_DAILY_CLASSIFY = 200

type BillingState = {
  tier: 'free' | 'pro' | 'enterprise'
  tier_active_until: string | null
  classify_today: number
  has_stripe_customer: boolean
}

function getCsrfToken(): string {
  const match = typeof document !== 'undefined'
    ? document.cookie.match(/(?:^|; )wot_csrf=([^;]+)/)
    : null
  return match ? decodeURIComponent(match[1]) : ''
}

export function BillingPanel() {
  const [state, setState] = useState<BillingState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [opening, setOpening] = useState(false)

  useEffect(() => {
    let canceled = false
    async function load() {
      try {
        const res = await fetch('/api/v1/billing/state', {
          credentials: 'include',
        })
        if (res.status === 401) return
        if (!res.ok) {
          throw new Error(`Failed to load billing state (${res.status})`)
        }
        const data = await res.json()
        if (!canceled) {
          setState({
            tier: data.tier || 'free',
            tier_active_until: data.tier_active_until || null,
            classify_today: data.classify_today_count || 0,
            has_stripe_customer: Boolean(data.has_stripe_customer),
          })
        }
      } catch (e) {
        if (!canceled) {
          setError(e instanceof Error ? e.message : 'Failed to load billing.')
        }
      } finally {
        if (!canceled) setLoading(false)
      }
    }
    load()
    return () => {
      canceled = true
    }
  }, [])

  async function openPortal() {
    setOpening(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/billing/portal', {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRF-Token': getCsrfToken() },
      })
      if (!res.ok) {
        throw new Error(`Portal session failed (${res.status})`)
      }
      const { portal_url } = await res.json()
      if (!portal_url) {
        throw new Error('No portal URL returned.')
      }
      window.location.href = portal_url
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not open portal.')
      setOpening(false)
    }
  }

  if (loading) {
    return (
      <section className="border rounded p-4 space-y-2">
        <div className="font-medium">Billing</div>
        <p className="text-sm text-muted-foreground">Loading...</p>
      </section>
    )
  }

  if (!state) return null

  const overage = Math.max(0, state.classify_today - PRO_INCLUDED_DAILY_CLASSIFY)

  return (
    <section className="border rounded p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="font-medium">Billing</div>
        <span
          className={`text-xs uppercase tracking-wide px-2 py-0.5 rounded ${
            state.tier === 'pro'
              ? 'bg-primary/10 text-primary'
              : state.tier === 'enterprise'
              ? 'bg-amber-100 text-amber-800'
              : 'bg-secondary text-secondary-foreground'
          }`}
        >
          {state.tier}
        </span>
      </div>

      {error && (
        <div className="border border-red-300 bg-red-50 text-red-800 rounded p-2 text-sm">
          {error}
        </div>
      )}

      {state.tier === 'free' && (
        <>
          <p className="text-sm text-muted-foreground">
            Upgrade to Pro for 5K req/min, 200 /classify calls/day, MCP HTTP-mode,
            bulk export, and webhooks. $49/month or $490/year. 14-day free trial.
          </p>
          <Link
            href="/pricing"
            className="inline-block px-4 py-2 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Upgrade to Pro
          </Link>
        </>
      )}

      {state.tier === 'pro' && (
        <>
          <div className="text-sm text-muted-foreground space-y-1">
            <div>
              <strong className="text-foreground">/classify usage today:</strong>{' '}
              {state.classify_today} / {PRO_INCLUDED_DAILY_CLASSIFY} included
              {overage > 0 && (
                <span className="ml-1 text-amber-700">
                  (+{overage} overage @ $0.05/call)
                </span>
              )}
            </div>
            {state.tier_active_until && (
              <div>
                <strong className="text-foreground">Renews:</strong>{' '}
                {new Date(state.tier_active_until).toLocaleDateString()}
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={openPortal}
            disabled={opening}
            className="inline-block px-4 py-2 rounded-lg text-sm font-medium bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors disabled:opacity-50"
          >
            {opening ? 'Opening Stripe...' : 'Manage subscription'}
          </button>
        </>
      )}

      {state.tier === 'enterprise' && (
        <>
          <p className="text-sm text-muted-foreground">
            Your org is on an Enterprise plan. Contact your account manager
            for billing changes, SLA questions, or rate-cap adjustments.
          </p>
          <Link
            href="/contact?subject=enterprise"
            className="inline-block px-4 py-2 rounded-lg text-sm font-medium bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
          >
            Contact account manager
          </Link>
        </>
      )}
    </section>
  )
}

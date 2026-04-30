'use client'

// Sign in via magic-link. Replaces the previous OAuth-only picker
// (GitHub / Google / LinkedIn) which depended on provider client IDs
// that were never wired in any environment, so every button returned
// 503 in practice. The magic-link flow shipped in Phase 6 is the only
// real auth path; this page is now the canonical entry point for it.

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Mail, Globe, AlertCircle, CheckCircle2 } from 'lucide-react'
import Link from 'next/link'

function isSignedInClient(): boolean {
  // wot_csrf is the JS-readable companion of the httponly dev_session
  // cookie. If present, the user has an active magic-link session.
  if (typeof document === 'undefined') return false
  return document.cookie.split('; ').some((c) => c.startsWith('wot_csrf='))
}

export default function LoginPage() {
  const router = useRouter()

  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [devLink, setDevLink] = useState<string | null>(null)

  // Already signed in? Send them straight to the dashboard.
  useEffect(() => {
    if (isSignedInClient()) {
      router.replace('/developers/keys')
    }
  }, [router])

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setStatus('sending')
    setErrorMessage(null)
    setDevLink(null)
    try {
      const res = await fetch('/api/v1/developers/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setErrorMessage(
          body.detail ??
            `Sign-in request failed (${res.status}). Try again in a moment.`,
        )
        setStatus('error')
        return
      }
      const body = await res.json()
      if (body.magic_link_url) {
        // Dev mode: backend returns the link in the response body so
        // local development does not need a real inbox.
        setDevLink(body.magic_link_url)
      }
      setStatus('sent')
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Unknown error')
      setStatus('error')
    }
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-3">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary border border-border/50">
            <Globe className="h-7 w-7 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-semibold">Sign in to WorldOfTaxonomy</h1>
          <p className="text-sm text-muted-foreground">
            Enter your email. We send a one-time sign-in link to your inbox - no password.
          </p>
        </div>

        {status !== 'sent' && (
          <form onSubmit={handleSubmit} className="space-y-3">
            <label className="block">
              <span className="sr-only">Email address</span>
              <input
                type="email"
                required
                autoFocus
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-border/50 bg-card text-base placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary/60"
              />
            </label>
            <button
              type="submit"
              disabled={status === 'sending'}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-foreground text-background text-sm font-medium hover:opacity-90 disabled:opacity-60 transition-opacity"
            >
              <Mail className="h-4 w-4" />
              {status === 'sending' ? 'Sending sign-in link...' : 'Send me a sign-in link'}
            </button>
            {errorMessage && (
              <p className="text-sm text-red-600 flex items-center gap-1.5">
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                {errorMessage}
              </p>
            )}
          </form>
        )}

        {status === 'sent' && (
          <div className="space-y-3 rounded-lg border border-emerald-200 bg-emerald-50 dark:border-emerald-900/40 dark:bg-emerald-950/40 p-4">
            <p className="text-sm font-medium flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
              <CheckCircle2 className="h-4 w-4" />
              Check your inbox
            </p>
            <p className="text-sm text-muted-foreground">
              We sent a sign-in link to <strong>{email}</strong>. The link expires in 15 minutes.
            </p>
            {devLink && (
              <p className="text-xs text-muted-foreground break-all border-t border-border/40 pt-2">
                <span className="font-medium">Dev-mode link:</span>{' '}
                <a href={devLink} className="underline">
                  {devLink}
                </a>
              </p>
            )}
          </div>
        )}

        <p className="text-xs text-center text-muted-foreground">
          No password required. Free during beta.{' '}
          <Link href="/terms" className="hover:text-foreground underline">
            Terms
          </Link>{' '}
          and{' '}
          <Link href="/privacy" className="hover:text-foreground underline">
            Privacy
          </Link>
          .
        </p>
      </div>
    </div>
  )
}

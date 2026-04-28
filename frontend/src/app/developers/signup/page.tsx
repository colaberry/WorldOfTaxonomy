'use client'

// Email-only signup. POSTs to /api/v1/developers/signup, which mints
// a magic-link token, emails it (Resend), and in dev mode returns the
// link so we can drive end-to-end tests without an inbox.

import { useState } from 'react'
import Link from 'next/link'

export default function DevelopersSignupPage() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [devLink, setDevLink] = useState<string | null>(null)

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
        setErrorMessage(body.detail ?? `Signup failed (${res.status})`)
        setStatus('error')
        return
      }
      const body = await res.json()
      if (body.magic_link_url) {
        setDevLink(body.magic_link_url)
      }
      setStatus('sent')
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Unknown error')
      setStatus('error')
    }
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-16 space-y-6">
      <h1 className="text-3xl font-semibold">Get an API key</h1>
      <p className="text-muted-foreground">
        Enter your email. We send a one-time sign-in link; no password.
        Manage your keys at{' '}
        <Link href="/developers/keys" className="underline">
          /developers/keys
        </Link>
        {' '}after signing in.
      </p>

      {status !== 'sent' && (
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="email"
            required
            autoFocus
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
          <button
            type="submit"
            disabled={status === 'sending'}
            className="w-full bg-foreground text-background rounded px-3 py-2 font-medium disabled:opacity-60"
          >
            {status === 'sending' ? 'Sending...' : 'Send me a sign-in link'}
          </button>
          {errorMessage && (
            <p className="text-sm text-red-600">{errorMessage}</p>
          )}
        </form>
      )}

      {status === 'sent' && (
        <div className="space-y-3">
          <p>Check your inbox for a sign-in link from us.</p>
          {devLink && (
            <p className="text-xs text-muted-foreground">
              Dev mode link:{' '}
              <a href={devLink} className="underline break-all">
                {devLink}
              </a>
            </p>
          )}
        </div>
      )}
    </div>
  )
}

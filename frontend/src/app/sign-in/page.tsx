'use client'

// Universal sign-in for the whole site. Magic-link only: no password,
// no separate dev / non-dev path. Developers click here from
// /developers, regular users click here from the navbar; both end up
// at the same form. The `next` query param lets each origin point
// land somewhere appropriate after the magic link is consumed.

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'

function SignInForm() {
  const searchParams = useSearchParams()
  const next = searchParams.get('next') ?? '/'
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
        body: JSON.stringify({ email, next }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        setErrorMessage(body.detail ?? `Sign-in failed (${res.status})`)
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
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold">Sign in to WorldOfTaxonomy</h1>
        <p className="text-muted-foreground">
          Enter your email. We send a one-time sign-in link, no password.
          New here? The same link signs you up.
        </p>
      </div>

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

      <p className="text-xs text-muted-foreground border-t pt-4">
        Looking to manage API keys?{' '}
        <Link href="/developers/keys" className="underline">
          /developers/keys
        </Link>
        . Curious what an API key is?{' '}
        <Link href="/guide/api-keys" className="underline">
          Read the guide
        </Link>
        .
      </p>
    </div>
  )
}

export default function SignInPage() {
  return (
    <Suspense fallback={<div className="max-w-xl mx-auto px-4 py-16">Loading...</div>}>
      <SignInForm />
    </Suspense>
  )
}

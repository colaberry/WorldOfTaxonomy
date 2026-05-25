'use client'

// API key dashboard: list / create / revoke.
// Cookie-gated; on 401 we send the user to /developers/signup.

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { Check, Copy, X } from 'lucide-react'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { BillingPanel } from './BillingPanel'

type KeyMetadata = {
  id: string
  name: string
  key_prefix: string
  scopes: string[]
  created_at: string
  expires_at: string | null
  last_used_at: string | null
  revoked_at: string | null
}

type RevealedKey = {
  raw: string
  name: string
  scopes: string[]
  created_at: string
}

// Tab-scoped storage. Cleared on tab close so the raw key never leaks
// past the session it was minted in. Survives accidental refresh of
// this page, which is the actual loss path users hit.
const REVEAL_STORAGE_KEY = 'wot:keys:revealed'

const SCOPE_PRESETS: { label: string; scopes: string[] }[] = [
  { label: 'Full WoT (read, list, export, classify, admin)', scopes: ['wot:*'] },
  { label: 'WoT read-only', scopes: ['wot:read', 'wot:list'] },
  { label: 'WoT classify only', scopes: ['wot:classify'] },
]

function loadRevealed(): RevealedKey | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(REVEAL_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed.raw !== 'string') return null
    return parsed as RevealedKey
  } catch {
    return null
  }
}

function saveRevealed(key: RevealedKey | null) {
  if (typeof window === 'undefined') return
  try {
    if (key === null) {
      window.sessionStorage.removeItem(REVEAL_STORAGE_KEY)
    } else {
      window.sessionStorage.setItem(REVEAL_STORAGE_KEY, JSON.stringify(key))
    }
  } catch {
    // Storage full or disabled. The modal still shows the key on the
    // creation turn; only refresh-survival is degraded.
  }
}

function CopyButton({ value, label = 'Copy' }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  const resetRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (resetRef.current) clearTimeout(resetRef.current)
    }
  }, [])

  const handleClick = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      if (resetRef.current) clearTimeout(resetRef.current)
      resetRef.current = setTimeout(() => setCopied(false), 1800)
    } catch {
      // Clipboard API blocked (insecure context, permissions). The raw
      // key is still visible on screen; user can select it manually.
    }
  }, [value])

  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={handleClick}
      aria-label={copied ? 'Copied' : label}
    >
      {copied ? <Check aria-hidden /> : <Copy aria-hidden />}
      <span>{copied ? 'Copied' : label}</span>
    </Button>
  )
}

export default function KeysDashboardPage() {
  const [keys, setKeys] = useState<KeyMetadata[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [presetIndex, setPresetIndex] = useState(0)
  const [creating, setCreating] = useState(false)
  const [revealed, setRevealed] = useState<RevealedKey | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  // Hydrate from sessionStorage on mount. Surviving a refresh is the
  // whole point of persisting; without this the user loses the key the
  // moment they hit reload.
  useEffect(() => {
    const stored = loadRevealed()
    if (stored) setRevealed(stored)
  }, [])

  function getCsrfToken(): string {
    // Same-origin double-submit token set by /api/v1/auth/magic-callback
    // alongside the dev_session cookie. Echoed on every state-changing
    // request as X-CSRF-Token. SameSite=Lax already blocks cross-origin
    // CSRF; this catches same-origin XSS-driven attacks.
    const match = document.cookie.match(/(?:^|; )wot_csrf=([^;]+)/)
    return match ? decodeURIComponent(match[1]) : ''
  }

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/developers/keys', {
        credentials: 'include',
      })
      if (res.status === 401) {
        window.location.replace('/login')
        return
      }
      if (!res.ok) {
        throw new Error(`Failed to load keys (${res.status})`)
      }
      setKeys(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCreating(true)
    try {
      const res = await fetch('/api/v1/developers/keys', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCsrfToken(),
        },
        body: JSON.stringify({
          name: name || 'Untitled key',
          scopes: SCOPE_PRESETS[presetIndex].scopes,
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail ?? `Failed (${res.status})`)
      }
      const body = await res.json()
      const next: RevealedKey = {
        raw: body.raw_key,
        name: body.metadata?.name ?? name ?? 'Untitled key',
        scopes: body.metadata?.scopes ?? SCOPE_PRESETS[presetIndex].scopes,
        created_at: body.metadata?.created_at ?? new Date().toISOString(),
      }
      setRevealed(next)
      saveRevealed(next)
      setModalOpen(true)
      setName('')
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setCreating(false)
    }
  }

  async function handleRevoke(id: string) {
    if (!confirm('Revoke this key? This cannot be undone.')) return
    try {
      const res = await fetch(`/api/v1/developers/keys/${id}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'X-CSRF-Token': getCsrfToken() },
      })
      if (!res.ok) {
        throw new Error(`Failed (${res.status})`)
      }
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  function dismissRevealed() {
    setRevealed(null)
    saveRevealed(null)
    setModalOpen(false)
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
      {revealed && (
        <div className="sticky top-0 z-30 -mx-4 px-4 pt-2 pb-3 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
          <div className="border border-amber-500/40 bg-amber-500/10 text-foreground rounded-md p-3 space-y-2">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-medium text-sm">Your new key for &quot;{revealed.name}&quot;</div>
                <div className="text-xs text-muted-foreground">
                  Visible only in this browser tab. Copy it now - we will not show it again after you close this tab.
                </div>
              </div>
              <button
                type="button"
                onClick={dismissRevealed}
                className="text-muted-foreground hover:text-foreground"
                aria-label="Dismiss key reveal"
              >
                <X aria-hidden className="size-4" />
              </button>
            </div>
            <div className="flex items-center gap-2">
              <code className="flex-1 min-w-0 break-all bg-muted text-foreground border border-border rounded px-3 py-2 text-xs font-mono">
                {revealed.raw}
              </code>
              <CopyButton value={revealed.raw} />
            </div>
          </div>
        </div>
      )}

      <div>
        <h1 className="text-3xl font-semibold">API keys</h1>
        <p className="text-muted-foreground">
          Manage keys that gate the public API and MCP server. Read the{' '}
          <Link href="/guide/getting-started" className="underline">
            quickstart
          </Link>{' '}
          for usage.
        </p>
      </div>

      {error && (
        <div className="border border-destructive/40 bg-destructive/10 text-foreground rounded p-3 text-sm">
          {error}
        </div>
      )}

      <BillingPanel />

      <form onSubmit={handleCreate} className="border rounded p-4 space-y-3">
        <div className="font-medium">Generate a new key</div>
        <input
          type="text"
          placeholder="Name (e.g. CI runner, MCP on laptop)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full border rounded px-3 py-2 bg-background text-foreground"
        />
        <select
          value={presetIndex}
          onChange={(e) => setPresetIndex(Number(e.target.value))}
          className="w-full border rounded px-3 py-2 bg-background text-foreground"
        >
          {SCOPE_PRESETS.map((preset, i) => (
            <option key={i} value={i}>
              {preset.label}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={creating}
          className="bg-foreground text-background rounded px-3 py-2 font-medium disabled:opacity-60"
        >
          {creating ? 'Generating...' : 'Generate key'}
        </button>
      </form>

      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Your keys</h2>
        {loading ? (
          <p className="text-muted-foreground">Loading...</p>
        ) : keys.length === 0 ? (
          <p className="text-muted-foreground">No keys yet. Generate your first key above.</p>
        ) : (
          <ul className="space-y-2">
            {keys.map((k) => (
              <li key={k.id} className="border rounded p-3 flex items-start justify-between gap-3">
                <div className="space-y-1 text-sm">
                  <div className="font-medium">{k.name}</div>
                  <div className="font-mono text-xs">
                    {k.key_prefix}... &middot; {k.scopes.join(', ')}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Created {new Date(k.created_at).toLocaleDateString()}
                    {k.last_used_at && ` · Last used ${new Date(k.last_used_at).toLocaleDateString()}`}
                    {k.revoked_at && ` · Revoked ${new Date(k.revoked_at).toLocaleDateString()}`}
                  </div>
                </div>
                {!k.revoked_at && (
                  <button
                    type="button"
                    onClick={() => handleRevoke(k.id)}
                    className="text-sm text-destructive hover:underline"
                  >
                    Revoke
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <Dialog
        open={modalOpen}
        onOpenChange={(open) => setModalOpen(open)}
        disablePointerDismissal
      >
        <DialogContent className="sm:max-w-lg" showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>Save your key</DialogTitle>
            <DialogDescription>
              This is the only time the full key is shown. After you close this dialog it stays visible in a banner on this page for the rest of your browser tab session, then it is gone for good. Revoke and regenerate if you lose it.
            </DialogDescription>
          </DialogHeader>
          {revealed && (
            <div className="space-y-3">
              <div className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{revealed.name}</span>
                {' · '}
                {revealed.scopes.join(', ')}
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 min-w-0 break-all bg-muted text-foreground border border-border rounded px-3 py-2 text-xs font-mono">
                  {revealed.raw}
                </code>
                <CopyButton value={revealed.raw} />
              </div>
            </div>
          )}
          <DialogFooter>
            <DialogClose render={<Button variant="default" />}>
              I have saved this key
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

'use client'

// API key dashboard: list / create / revoke.
// Cookie-gated; on 401 we send the user to /developers/signup.

import { useEffect, useState } from 'react'
import Link from 'next/link'

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

const SCOPE_PRESETS: { label: string; scopes: string[] }[] = [
  { label: 'Full WoT (read, list, export, classify, admin)', scopes: ['wot:*'] },
  { label: 'WoT read-only', scopes: ['wot:read', 'wot:list'] },
  { label: 'WoT classify only', scopes: ['wot:classify'] },
]

export default function KeysDashboardPage() {
  const [keys, setKeys] = useState<KeyMetadata[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [presetIndex, setPresetIndex] = useState(0)
  const [creating, setCreating] = useState(false)
  const [justCreated, setJustCreated] = useState<string | null>(null)

  async function refresh() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/developers/keys', {
        credentials: 'include',
      })
      if (res.status === 401) {
        window.location.replace('/developers/signup')
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
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCreating(true)
    setJustCreated(null)
    try {
      const res = await fetch('/api/v1/developers/keys', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
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
      setJustCreated(body.raw_key)
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
      })
      if (!res.ok) {
        throw new Error(`Failed (${res.status})`)
      }
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
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
        <div className="border border-red-300 bg-red-50 text-red-800 rounded p-3 text-sm">
          {error}
        </div>
      )}

      {justCreated && (
        <div className="border border-amber-300 bg-amber-50 rounded p-4 space-y-2">
          <div className="font-medium">Copy your key now - we will not show it again</div>
          <code className="block break-all bg-white border rounded px-3 py-2 text-sm">
            {justCreated}
          </code>
        </div>
      )}

      <form onSubmit={handleCreate} className="border rounded p-4 space-y-3">
        <div className="font-medium">Generate a new key</div>
        <input
          type="text"
          placeholder="Name (e.g. CI runner, MCP on laptop)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full border rounded px-3 py-2"
        />
        <select
          value={presetIndex}
          onChange={(e) => setPresetIndex(Number(e.target.value))}
          className="w-full border rounded px-3 py-2"
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
                    {k.last_used_at && ` &middot; Last used ${new Date(k.last_used_at).toLocaleDateString()}`}
                    {k.revoked_at && ` &middot; Revoked ${new Date(k.revoked_at).toLocaleDateString()}`}
                  </div>
                </div>
                {!k.revoked_at && (
                  <button
                    type="button"
                    onClick={() => handleRevoke(k.id)}
                    className="text-sm text-red-600 hover:underline"
                  >
                    Revoke
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

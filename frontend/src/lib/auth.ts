/**
 * Auth utilities - token storage and retrieval.
 * Uses localStorage so the token survives page reloads.
 * All storage is client-side only (no cookies, no server-side sessions).
 */

const TOKEN_KEY = 'wot_token'
const USER_KEY  = 'wot_user'

export interface StoredUser {
  email: string
  name:  string
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setAuth(token: string, user: StoredUser): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as StoredUser
  } catch {
    return null
  }
}

/** Returns true if a token exists. Does NOT validate expiry client-side. */
export function isLoggedIn(): boolean {
  return !!getToken()
}

/**
 * Auth utilities for the magic-link cookie session.
 *
 * The OAuth + JWT-in-localStorage path was removed in 2026-04-30. The
 * canonical auth state is now the pair of cookies set by
 * /api/v1/auth/magic-callback:
 *
 *   - dev_session  (httponly, JS cannot read)
 *   - wot_csrf     (NOT httponly, JS-readable; double-submit token)
 *
 * Components detect "is the user signed in?" by the presence of
 * wot_csrf, since that mirrors dev_session 1:1 in lifecycle but is
 * visible to client-side JS. Reading wot_csrf is safe (it is not a
 * credential by itself - the actual auth is via dev_session).
 */

const CSRF_COOKIE = 'wot_csrf'

export interface StoredUser {
  email: string
}

/** Returns true if the magic-link cookie session is active. */
export function isLoggedIn(): boolean {
  if (typeof document === 'undefined') return false
  return document.cookie.split('; ').some((c) => c.startsWith(`${CSRF_COOKIE}=`))
}

/**
 * Returns the CSRF token value from the cookie. Used as the
 * X-CSRF-Token header on state-changing requests to /developers/keys.
 */
export function getCsrfToken(): string {
  if (typeof document === 'undefined') return ''
  const match = document.cookie.match(new RegExp(`(?:^|; )${CSRF_COOKIE}=([^;]+)`))
  return match ? decodeURIComponent(match[1]) : ''
}

/**
 * Backend logout endpoint clears both cookies on this domain. After it
 * resolves, the caller should refresh user-dependent UI state.
 */
export async function logout(): Promise<void> {
  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'include',
  }).catch(() => {
    // Even if the request fails, the next page load will see the
    // cookies expire on their own (60-min TTL) and the user will be
    // signed out at that point. Don't throw - the user has already
    // expressed the intent to sign out.
  })
}

/**
 * Frontend does not store user identity locally for the magic-link
 * flow - the backend resolves identity from the session cookie on
 * each request. This stub exists so existing imports don't break;
 * components needing the user's email should call /api/v1/me-style
 * endpoint instead.
 */
export function getStoredUser(): StoredUser | null {
  return null
}

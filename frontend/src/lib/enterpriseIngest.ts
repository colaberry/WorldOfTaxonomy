/**
 * Client-side helper that forwards lead submissions to Colaberry
 * Enterprise Accelerator's lead ingestion endpoint.
 *
 * Pattern (from Ali's Apr 18/24 prompts, already shipped for colaberry.ai
 * /request-demo):
 *
 *   POST https://enterprise.colaberry.ai/api/leads/ingest
 *        ?source=worldoftaxonomy&entry=<entry>
 *   Content-Type: application/json
 *   Body: {name?, email, company?, metadata?, page_url?, referrer?, utm_*?}
 *
 * Design notes
 *
 * - Fire-and-forget. Never throws, never blocks. Errors are logged to
 *   console at debug level; the caller's existing success / error UX is
 *   the source of truth for the user.
 *
 * - Runs IN PARALLEL with the form's primary write (Strapi / internal
 *   API). Always call the primary write first and let the user's UX be
 *   driven by that response. This webhook is secondary attribution.
 *
 * - Kill switch: set NEXT_PUBLIC_ENTERPRISE_INGEST_ENABLED to any of
 *   "false", "0", "no", or "off" to short-circuit delivery. Default is
 *   ON so the webhook is active in prod as soon as the code ships.
 *
 * - Base URL override: NEXT_PUBLIC_ENTERPRISE_INGEST_BASE_URL. Defaults
 *   to https://enterprise.colaberry.ai/api/leads/ingest. Useful for
 *   pointing at a staging ingest endpoint if Ali provisions one.
 */

export interface EnterpriseLeadData {
  /** Form-captured fields. Only `email` is required by the endpoint. */
  name?: string
  email: string
  company?: string
  /**
   * Form-specific nested fields. For /classify this holds
   * `description`; for /developers it holds `message`. Shape is free
   * per the ingestion endpoint's spec.
   */
  metadata?: Record<string, unknown>
  /**
   * Extra fields are passed through as-is. Useful for future TBI
   * forms (role, company_size, assessment_score) without having to
   * extend this interface each time.
   */
  [key: string]: unknown
}

const DEFAULT_BASE_URL = 'https://enterprise.colaberry.ai/api/leads/ingest'
const SOURCE = 'worldoftaxonomy'

function isEnabled(): boolean {
  const flag = (
    process.env.NEXT_PUBLIC_ENTERPRISE_INGEST_ENABLED || ''
  )
    .trim()
    .toLowerCase()
  // Default ON. Explicit false-y values disable.
  return !['false', '0', 'no', 'off'].includes(flag)
}

function getBaseUrl(): string {
  const override = (process.env.NEXT_PUBLIC_ENTERPRISE_INGEST_BASE_URL || '').trim()
  return override || DEFAULT_BASE_URL
}

/**
 * Pull UTM and other attribution fields from the current URL. Returns
 * only fields that actually have values so we do not spam the ingest
 * payload with empty utm_* keys.
 */
function collectAttribution(): Record<string, string> {
  if (typeof window === 'undefined') return {}
  const params = new URLSearchParams(window.location.search)
  const out: Record<string, string> = {}
  for (const key of [
    'utm_source',
    'utm_medium',
    'utm_campaign',
    'utm_term',
    'utm_content',
    'gclid',
    'fbclid',
  ]) {
    const value = params.get(key)
    if (value) out[key] = value
  }
  return out
}

/**
 * Send a lead submission to the enterprise ingestion endpoint.
 *
 * @param entry  form-specific tag (e.g. "classify_lead", "developer_contact")
 * @param data   lead payload; email is required, everything else is optional
 * @returns      true on 2xx, false otherwise. Never rejects.
 */
export async function sendEnterpriseLead(
  entry: string,
  data: EnterpriseLeadData,
): Promise<boolean> {
  if (!isEnabled()) return false
  if (typeof window === 'undefined') return false

  const base = getBaseUrl()
  const sep = base.includes('?') ? '&' : '?'
  const url = `${base}${sep}source=${encodeURIComponent(SOURCE)}&entry=${encodeURIComponent(entry)}`

  const payload: Record<string, unknown> = {
    ...data,
    page_url: window.location.href,
    referrer: document.referrer || undefined,
    ...collectAttribution(),
  }

  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      // keepalive lets the request survive a page navigation (matters for
      // /developers where the primary request is a native form POST that
      // navigates). Browsers cap the body at 64KB for keepalive requests;
      // our payloads are well under that.
      keepalive: true,
    })
    if (resp.ok) return true
    if (typeof console !== 'undefined') {
      console.debug(
        `[enterpriseIngest] ${entry} rejected`,
        resp.status,
        await resp.text().catch(() => '(no body)'),
      )
    }
    return false
  } catch (err) {
    if (typeof console !== 'undefined') {
      console.debug(`[enterpriseIngest] ${entry} failed`, err)
    }
    return false
  }
}

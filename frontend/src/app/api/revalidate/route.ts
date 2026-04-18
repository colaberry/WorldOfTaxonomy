import { timingSafeEqual } from 'node:crypto'
import { revalidatePath } from 'next/cache'
import { NextRequest, NextResponse } from 'next/server'

// Constant-time string compare so a remote attacker can not learn
// REVALIDATE_SECRET byte-by-byte via response timing. timingSafeEqual
// requires equal-length buffers, so we bail out on length mismatch.
function constantTimeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a, 'utf8')
  const bb = Buffer.from(b, 'utf8')
  if (ab.length !== bb.length) {
    return false
  }
  return timingSafeEqual(ab, bb)
}

/**
 * On-demand cache invalidation endpoint.
 *
 * Called by backend ingesters after data changes to bust the
 * Next.js server-side cache. Protected by a shared secret.
 *
 * POST /api/revalidate
 * Headers: x-revalidate-secret: <secret>
 * Body: { "systemId": "naics_2022" } or { "scope": "all" }
 */
export async function POST(request: NextRequest) {
  const secret = request.headers.get('x-revalidate-secret') ?? ''
  const expected = process.env.REVALIDATE_SECRET

  if (!expected || !constantTimeEqual(secret, expected)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await request.json()
  const { systemId, scope } = body as { systemId?: string; scope?: string }

  if (scope === 'all') {
    // Revalidate all pages by busting the layout cache
    revalidatePath('/', 'layout')
    return NextResponse.json({ revalidated: true, scope: 'all' })
  }

  if (systemId) {
    // Revalidate specific system page and related pages
    revalidatePath(`/system/${systemId}`, 'page')
    revalidatePath('/explore', 'page')
    revalidatePath('/', 'page')
    return NextResponse.json({ revalidated: true, systemId })
  }

  return NextResponse.json({ error: 'Provide systemId or scope=all' }, { status: 400 })
}

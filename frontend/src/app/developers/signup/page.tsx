// /developers/signup is preserved as a permanent redirect to the
// universal /sign-in flow. The Phase 6 design originally split sign-in
// across two surfaces (developer magic-link + legacy /login). We
// collapsed both into one passwordless flow; this stub keeps existing
// links working.

import { redirect } from 'next/navigation'

export default function DevelopersSignupRedirect() {
  redirect('/sign-in?next=/developers/keys')
}

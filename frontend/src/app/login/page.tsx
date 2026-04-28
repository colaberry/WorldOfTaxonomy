// /login redirects to /sign-in. We collapsed password + OAuth + magic
// link onto one passwordless surface; the legacy /api/v1/auth/* routes
// stay alive for backward compatibility but the UI no longer exposes
// them. This stub keeps deep-linked /login URLs working.

import { redirect } from 'next/navigation'

export default function LoginRedirect() {
  redirect('/sign-in')
}

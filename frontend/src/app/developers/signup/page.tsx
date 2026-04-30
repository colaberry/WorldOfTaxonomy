import { permanentRedirect } from 'next/navigation'

// Sign-up consolidated into /login (which now hosts the magic-link
// form). Old links and the magic-link error path may still hit
// /developers/signup; redirect them. Keep the route alive (vs.
// returning 404) so external bookmarks still work.
export default function DevelopersSignupPage() {
  permanentRedirect('/login')
}

# OAuth Production Setup Guide

Follow these steps after deploying WorldOfTaxonomy to production.
Complete them in order - the database migration must run before any
OAuth sign-ins will work.

---

## Step 1 - Run the database migration

The production database has the old schema (`password_hash NOT NULL`, no
OAuth columns). Run this SQL once against your production database before
anything else.

Open your Postgres admin console (Neon, Supabase, RDS Query Editor, `psql`,
or whatever you use), connect to the production database, and run:

```sql
-- Make password_hash optional (OAuth users have no password)
ALTER TABLE app_user
  ALTER COLUMN password_hash DROP NOT NULL;

-- Add OAuth identity columns
ALTER TABLE app_user
  ADD COLUMN IF NOT EXISTS oauth_provider    TEXT,
  ADD COLUMN IF NOT EXISTS oauth_provider_id TEXT,
  ADD COLUMN IF NOT EXISTS avatar_url        TEXT;

-- Ensure each (provider, provider_id) pair is unique
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_oauth
  ON app_user(oauth_provider, oauth_provider_id)
  WHERE oauth_provider IS NOT NULL AND oauth_provider_id IS NOT NULL;
```

Verify it worked:

```sql
SELECT column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_name = 'app_user'
ORDER BY ordinal_position;
```

You should see `password_hash` with `is_nullable = YES` and the three
new columns (`oauth_provider`, `oauth_provider_id`, `avatar_url`).

---

## Step 2 - Create OAuth applications

You need one OAuth application per provider. Each gives you a
client ID and client secret to add to your environment.

Your callback URL base is:

```
https://<your-api-domain>/api/v1/auth/oauth
```

Replace `<your-api-domain>` with your deployed FastAPI URL throughout
this section (e.g. `worldoftaxonomy-api.fly.dev`).

---

### 2a - GitHub

1. Go to https://github.com/settings/developers
2. Click **OAuth Apps** then **New OAuth App**
3. Fill in the form:
   - **Application name**: WorldOfTaxonomy
   - **Homepage URL**: `https://<your-frontend-domain>`
   - **Authorization callback URL**: `https://<your-api-domain>/api/v1/auth/oauth/github/callback`
4. Click **Register application**
5. On the next screen, copy the **Client ID**
6. Click **Generate a new client secret** and copy it immediately
   (it is only shown once)

Environment variables to set:

```
GITHUB_CLIENT_ID=<paste client id>
GITHUB_CLIENT_SECRET=<paste client secret>
```

---

### 2b - Google

1. Go to https://console.cloud.google.com
2. Create a new project (or select an existing one)
3. In the left menu go to **APIs & Services** - **OAuth consent screen**
   - User type: **External**
   - App name: WorldOfTaxonomy
   - Support email: your email
   - Authorized domains: add your frontend domain
   - Scopes: add `email` and `profile`
   - Test users: add your own email while in testing mode
   - Save and continue through all steps
4. Go to **APIs & Services** - **Credentials** - **Create Credentials** - **OAuth 2.0 Client ID**
   - Application type: **Web application**
   - Name: WorldOfTaxonomy
   - Authorized redirect URIs: `https://<your-api-domain>/api/v1/auth/oauth/google/callback`
5. Click **Create**
6. Copy the **Client ID** and **Client Secret** from the dialog

Environment variables to set:

```
GOOGLE_CLIENT_ID=<paste client id>
GOOGLE_CLIENT_SECRET=<paste client secret>
```

> Note: while your app is in "Testing" mode, only test users can sign in.
> To allow any Google account, go to the OAuth consent screen and click
> **Publish App** (this triggers a verification review for sensitive
> scopes, but `email` and `profile` are not sensitive and are usually
> approved quickly or auto-approved).

---

### 2c - LinkedIn

LinkedIn requires a Company Page before you can create an app.
If you do not have one, create a free one at linkedin.com/company/setup/new.

1. Go to https://www.linkedin.com/developers/apps and click **Create app**
2. Fill in the form:
   - **App name**: WorldOfTaxonomy
   - **LinkedIn Page**: select your company page
   - **App logo**: upload a logo (required)
3. Click **Create app**
4. Go to the **Auth** tab
   - Copy the **Client ID** and **Client Secret**
   - Under **Authorized redirect URLs** add:
     `https://<your-api-domain>/api/v1/auth/oauth/linkedin/callback`
5. Go to the **Products** tab and request access to:
   - **Sign In with LinkedIn using OpenID Connect**
   (This is usually approved instantly)

Environment variables to set:

```
LINKEDIN_CLIENT_ID=<paste client id>
LINKEDIN_CLIENT_SECRET=<paste client secret>
```

---

## Step 3 - Set environment variables on your server

Add all of the following to your backend server's environment
(Fly.io secrets, Railway variables, etc.):

```
# OAuth providers
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...

# Tell the backend where it lives and where the frontend lives
# so it can build correct callback and redirect URLs
BACKEND_URL=https://<your-api-domain>
FRONTEND_URL=https://<your-frontend-domain>

# Existing required vars (already set)
DATABASE_URL=...
JWT_SECRET=...    # must be at least 32 characters
```

After setting variables, redeploy the backend so they take effect.

---

## Step 4 - Verify each provider works

Visit `https://<your-frontend-domain>/login` and test each button.

For each provider, the expected flow is:

1. Click the button
2. Browser redirects to the provider login page
3. You approve access
4. Browser redirects back to your site
5. You are logged in and the header shows your name with a sign-out dropdown

**Quick API check** - you can also test the authorize endpoint directly:

```bash
# Should return {"auth_url": "https://github.com/login/oauth/authorize?...", "provider": "github"}
curl "https://<your-api-domain>/api/v1/auth/oauth/github/authorize"

# Same for the other two
curl "https://<your-api-domain>/api/v1/auth/oauth/google/authorize"
curl "https://<your-api-domain>/api/v1/auth/oauth/linkedin/authorize"
```

If any returns `503` the client ID env var for that provider is missing.
If any returns `400` the provider name is wrong (check the URL).

---

## Step 5 - Check the database after first sign-in

After at least one real user signs in via OAuth, verify the record looks
right in the production database:

```sql
SELECT id, email, display_name, oauth_provider, oauth_provider_id,
       avatar_url, password_hash, created_at
FROM app_user
ORDER BY created_at DESC
LIMIT 5;
```

Expected:
- `oauth_provider` is `github`, `google`, or `linkedin`
- `oauth_provider_id` is a non-empty string
- `password_hash` is `NULL` (no password stored)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `503` from `/authorize` | Env var not set | Check `GITHUB/GOOGLE/LINKEDIN_CLIENT_ID` is set and server redeployed |
| `400 redirect_uri_mismatch` from GitHub | Callback URL not registered | In GitHub app settings, confirm the callback URL matches exactly |
| `redirect_uri_mismatch` from Google | Callback URL not in authorized list | Add exact URL in Google Cloud console - Credentials - OAuth 2.0 Client |
| `invalid_client` from LinkedIn | Wrong client secret | Regenerate secret in LinkedIn developer console |
| Login works but header still shows "Sign in" | Frontend not receiving token | Open browser devtools - Network tab - check `/auth/callback` URL has `?token=` param, and check localStorage for `wot_token` |
| "This account uses social login" error on password login | User registered via OAuth, trying password | Expected behavior - direct them to the social login page |
| Google sign-in only works for test users | App still in testing mode | Publish the app in the OAuth consent screen |

---

## CORS note

If your backend and frontend are on different domains, confirm your
`BACKEND_URL` env var is set and that the `CORSMiddleware` in `app.py`
includes your production frontend origin:

```python
allow_origins=[
    "http://localhost:3000",
    "https://<your-frontend-domain>",   # add this
]
```

Redeploy the backend after updating.

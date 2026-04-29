# Releasing `worldoftaxonomy-mcp` to PyPI

How to cut a release of the MCP server PyPI package. Triggered by
tagging `vX.Y.Z` on `main`; the
[`publish-pypi.yml`](../../.github/workflows/publish-pypi.yml)
workflow handles the rest.

## One-time setup (per repo)

Configure PyPI trusted publishing so the workflow can publish without
a stored token:

1. On <https://pypi.org/manage/projects/>, create the project
   `worldoftaxonomy-mcp` (or claim it if it already exists).
2. Settings -> Publishing -> Add a new publisher.
3. Fill in:
   - Owner: `colaberry`
   - Repo: `WorldOfTaxonomy`
   - Workflow filename: `publish-pypi.yml`
   - Environment: `pypi`
4. Save. PyPI will mint short-lived OIDC tokens for that workflow.
5. In the GitHub repo settings, create an environment named `pypi`
   with the protections you want (e.g. only `main` allowed, optional
   reviewer required for prod releases).

That's the entire setup. No PyPI tokens are stored in the repo or
in GitHub secrets.

## Cutting a release

```bash
# 1. Bump the version in pyproject.toml on main.
git checkout main && git pull
sed -i '' -E 's/^version = "(.*)"$/version = "0.1.1"/' pyproject.toml
git add pyproject.toml
git commit -m "release: worldoftaxonomy-mcp 0.1.1"
git push

# 2. Tag the release. The tag MUST match pyproject.toml exactly.
git tag v0.1.1
git push origin v0.1.1

# 3. Watch the workflow at
#    https://github.com/colaberry/WorldOfTaxonomy/actions/workflows/publish-pypi.yml
```

The workflow:

1. Validates the tag matches `pyproject.toml` (fails fast if not).
2. Builds wheel + sdist with `python -m build`.
3. Smoke-tests the wheel installs in a clean venv and the
   `worldoftaxonomy-mcp` entry-point exits 2 with the
   missing-credentials message when run without env vars.
4. Uploads dist artifacts.
5. Publishes via OIDC trusted-publishing - no token needed.

End-to-end takes about 4-6 minutes.

## Pre-release flavors

Pre-releases use the `rcN` suffix:

```bash
git tag v0.2.0rc1
git push origin v0.2.0rc1
```

PyPI will list these as pre-releases; users get them with
`pip install --pre worldoftaxonomy-mcp`. Stable installs ignore them.

## Verifying after publish

```bash
# Wait ~1 min after the workflow finishes for the PyPI CDN to update.
pip install --upgrade worldoftaxonomy-mcp==0.1.1
worldoftaxonomy-mcp 2>&1 | head
# Expect: missing-creds message + exit 2.

# End-to-end with a real key:
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  | WOT_API_KEY=wot_... worldoftaxonomy-mcp \
  | jq -r '.result.serverInfo'
# Expect: {"name": "WorldOfTaxonomy", "version": "0.1.0", ...}
```

## Rollback

PyPI does not allow re-uploading the same version. To roll back:

1. Yank the bad version on PyPI: project page -> Releases -> Yank.
   This hides it from `pip install` but keeps it accessible for
   anyone who explicitly requested that version.
2. Bump to a fresh patch version with the fix and tag again.

Do NOT delete versions; PyPI's policy is yank-then-replace, not
delete-and-reuse.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `Tag v0.1.1 does not match pyproject.toml version 0.1.0` | Forgot to bump pyproject.toml before tagging | Delete the tag, bump pyproject.toml on main, retag |
| `OIDC: trust mismatch` | Trusted publisher mis-configured | Re-check the four fields in PyPI Settings -> Publishing |
| `400 File already exists` | Re-tagging the same version | Bump version, retag |
| `worldoftaxonomy-mcp` not on PATH after pip install | `pip install --user` without ~/.local/bin in PATH | Either add it, use a venv, or `uvx worldoftaxonomy-mcp` |
| Wheel ~5MB feels large | Includes the full `world_of_taxonomy` namespace | Acceptable; see the design note in pyproject.toml |

## What ships in the wheel

```
worldoftaxonomy_mcp-X.Y.Z-py3-none-any.whl
├── world_of_taxonomy/
│   ├── mcp/                 # MCP server, protocol, http_dispatcher
│   ├── api/                 # FastAPI app (used by self-hosters; HTTP-mode users do not invoke it)
│   ├── auth/                # developer-key system; included for completeness
│   ├── ingest/              # ingester modules; included for completeness
│   ├── query/               # query primitives
│   ├── classify.py          # classify engine
│   ├── schema.sql           # core schema
│   ├── schema_auth.sql      # auth schema
│   ├── schema_devkeys.sql   # dev-keys schema
│   ├── migrations/          # alembic migrations
│   └── ...
└── worldoftaxonomy_mcp-X.Y.Z.dist-info/
    └── entry_points: worldoftaxonomy-mcp, world-of-taxonomy
```

Console scripts:

- `worldoftaxonomy-mcp` runs the MCP stdio server. Used by Claude
  Desktop, Cursor, Zed, etc.
- `world-of-taxonomy` is the multi-subcommand CLI for self-hosters
  (serve, mcp, ingest, init-auth). Most end users do not need it.

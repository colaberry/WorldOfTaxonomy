# Security Policy

We take the security of WorldOfTaxonomy seriously. Thank you for helping keep the project and its users safe.

## Supported versions

Security fixes are applied only to the `main` branch and the latest released container image. Older builds are not patched; please update to the current release.

| Version       | Supported |
|---------------|-----------|
| `main` (HEAD) | Yes       |
| Older tags    | No        |

## Reporting a vulnerability

Please do **not** open a public GitHub issue for suspected vulnerabilities.

Instead, use one of the private channels below:

1. **GitHub Security Advisories** (preferred): open a private report at
   <https://github.com/ramdhanyk/WorldOfTaxonomy/security/advisories/new>.
2. **Email**: send details to the maintainer via the contact form at
   <https://worldoftaxonomy.com/contact>. Mark the subject line with
   `[SECURITY]` so it is triaged promptly.

When reporting, include as much of the following as you can:

- A clear description of the issue and its potential impact.
- Steps to reproduce (minimal PoC preferred).
- Affected versions, commit SHAs, or deployment URLs.
- Any suggested remediation, if you have one.

## Response expectations

- **Acknowledgement**: within 3 business days of receipt.
- **Triage + initial assessment**: within 7 business days.
- **Fix timeline**: depends on severity. Critical issues are prioritized and typically patched within 14 days; lower-severity issues are batched into the normal release cadence.
- **Disclosure**: coordinated with the reporter. We will credit reporters in the advisory unless they prefer to remain anonymous.

## Out of scope

The following are not considered vulnerabilities:

- Rate-limit ceilings (documented and intentional).
- Missing security headers on `/docs` or `/redoc` that do not impact users.
- Findings that require a pre-compromised host, browser, or account.
- Denial-of-service via raw volumetric traffic (handled at the ingress layer).
- Issues in third-party dependencies already tracked upstream; please report those to the respective project.

## Safe harbor

Good-faith security research conducted under this policy is welcomed. We will not pursue or support legal action against researchers who:

- Make a good-faith effort to avoid privacy violations, data destruction, and service disruption.
- Report the issue promptly via the channels above.
- Give us reasonable time to remediate before public disclosure.

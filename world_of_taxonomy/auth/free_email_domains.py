"""Static set of free-email-provider domains.

Signups from these domains get a per-email personal org instead of a
shared corporate-domain bucket; otherwise a `gmail.com` org would
have hundreds of millions of users sharing one rate-limit pool.

Refresh quarterly against a public free-email-provider list. Keep the
set small: the pricing-model loophole this closes is corporate
domains using N personal accounts to multiply the free-tier ceiling,
not exhaustive coverage of every webmail provider.
"""

FREE_EMAIL_DOMAINS = frozenset({
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "proton.me",
    "icloud.com",
    "fastmail.com",
})

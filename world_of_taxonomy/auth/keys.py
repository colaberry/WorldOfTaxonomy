"""Developer-key issuance, prefix derivation, and scope checks.

Three things this module owns:

1. Choosing a prefix from a scope set: `wot_` for full single-product
   access, `rwot_` (and `rwoo_`, `rwouc_`, `rwoa_`) when scopes are a
   strict subset, `aix_` when the key reaches across products. Mirrors
   Stripe's `sk_/rk_` and GitHub's `ghp_/ghs_` conventions so leak
   triage is fast.
2. Granting a request: `scope_granted(key.scopes, required)` answers
   "may this key call this endpoint?" with wildcard semantics
   (`['wot:*']` covers any `wot:<action>`).
3. Issuing a key: generate the random secret, derive its prefix, hash
   it with bcrypt, return the raw key once.

The `<product>:<action>` scope grammar is the contract that survives
the Phase 7 extraction to developer.aixcelerator.ai. The same scopes
work whether validation runs against a local DB or an HTTP service.
"""

from __future__ import annotations

import re
import secrets
from typing import Iterable, Mapping, Sequence

import bcrypt


# Per-product registries. Adding a sibling product (woo, wouc, woa)
# is a one-line change in WOT_FULL_ACTIONS' sibling - or just add the
# product as a key here when its scopes get defined.

WOT_FULL_ACTIONS = frozenset({"read", "list", "export", "classify", "admin"})

PRODUCT_FULL_ACTIONS: dict[str, frozenset[str]] = {
    "wot": WOT_FULL_ACTIONS,
    # Sibling products fill these in when they ship; until then,
    # any subset of woo:* is treated as restricted.
    "woo": frozenset(),
    "wouc": frozenset(),
    "woa": frozenset(),
}

_SCOPE_RE = re.compile(r"^([a-z][a-z0-9]*):(\*|[a-z][a-z0-9_]*)$")


def _split_scope(scope: str) -> tuple[str, str]:
    """Return (product, action) for a scope; raise ValueError on malformed input."""
    match = _SCOPE_RE.match(scope)
    if not match:
        raise ValueError(f"invalid scope: {scope!r}")
    return match.group(1), match.group(2)


def _products_in(scopes: Sequence[str]) -> set[str]:
    return {_split_scope(s)[0] for s in scopes}


def _is_full_product(scopes: Sequence[str], product: str) -> bool:
    """True when the scope set covers every action on `product`.

    A wildcard `wot:*` always counts as full. A complete enumeration
    of every action in PRODUCT_FULL_ACTIONS[product] also counts so
    that callers can request explicit scope lists without losing the
    `wot_` prefix.
    """
    actions: set[str] = set()
    for scope in scopes:
        prod, action = _split_scope(scope)
        if prod != product:
            continue
        if action == "*":
            return True
        actions.add(action)

    full = PRODUCT_FULL_ACTIONS.get(product, frozenset())
    return bool(full) and actions >= full


def prefix_for_scopes(scopes: Sequence[str]) -> str:
    """Return the bare prefix (e.g. 'wot_', 'rwot_', 'aix_') for a scope set.

    Empty scopes is a programmer error - callers must declare what
    the key is allowed to do.
    """
    if not scopes:
        raise ValueError("scopes must be non-empty")

    products = _products_in(scopes)
    if len(products) > 1:
        return "aix_"

    (product,) = products
    if _is_full_product(scopes, product):
        return f"{product}_"
    return f"r{product}_"


def scope_granted(granted_scopes: Iterable[str], required: str) -> bool:
    """True when any granted scope covers `required`.

    Wildcard `<product>:*` matches any `<product>:<action>`. Exact
    equality also matches. Mismatched products always deny - we never
    let a `wot:*` key reach a `woo:read` endpoint.
    """
    req_product, req_action = _split_scope(required)
    for granted in granted_scopes:
        try:
            prod, action = _split_scope(granted)
        except ValueError:
            continue
        if prod != req_product:
            continue
        if action == "*" or action == req_action:
            return True
    return False


# Issuance


def _generate_raw_key(prefix: str) -> str:
    """Return `<prefix><32 hex chars>` using `secrets.token_hex`."""
    return prefix + secrets.token_hex(16)


def _key_prefix_index(raw_key: str) -> str:
    """Return the 8-char prefix-index slice used for fast lookup.

    For the legacy `wot_xxxxxxxxxxxx...` shape we kept the first 8
    hex chars after the underscore. The new prefixes (`rwot_`,
    `aix_`, etc.) are variable length, so we slice the 8 hex chars
    immediately after the trailing underscore in the visible prefix.
    """
    underscore = raw_key.index("_")
    return raw_key[underscore + 1 : underscore + 9]


def issue_key(scopes: Sequence[str]) -> Mapping[str, str]:
    """Generate a new key for the given scope set.

    Returns a mapping with:
      - raw_key:    show this to the user once and never again.
      - prefix:     visible prefix (e.g. 'wot_', 'rwot_', 'aix_').
      - key_prefix: 8-char index slice for hot-path lookup.
      - key_hash:   bcrypt hash to store in the database.

    Callers persist everything except `raw_key` and immediately drop
    `raw_key` from memory after returning it to the user.
    """
    prefix = prefix_for_scopes(scopes)
    raw_key = _generate_raw_key(prefix)
    key_hash = bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return {
        "raw_key": raw_key,
        "prefix": prefix,
        "key_prefix": _key_prefix_index(raw_key),
        "key_hash": key_hash,
    }


# Validation against the database


async def validate_key(conn, raw_key: str, *, required_scope: str) -> Mapping:
    """Look up `raw_key` in api_key, check scope, mark last_used_at.

    Returns a mapping with `allow: bool`. On allow=True the result
    also carries `user_id`, `org_id`, `key_id`, `scopes`. On
    allow=False, `reason` is one of:
      not_found       - prefix matches nothing live, or hash mismatch
      revoked         - key has revoked_at set
      expired         - expires_at <= now
      scope_missing   - the key's scopes do not cover required_scope

    The hot path is a single SELECT keyed by `key_prefix` (8-char
    slice), then bcrypt-checking each match's hash. Keys with
    `revoked_at IS NULL` are surfaced via the partial index added in
    migration 003.
    """
    if "_" not in raw_key:
        return {"allow": False, "reason": "not_found"}
    try:
        key_prefix = _key_prefix_index(raw_key)
    except ValueError:
        return {"allow": False, "reason": "not_found"}

    rows = await conn.fetch(
        """SELECT k.id AS key_id, k.user_id, k.key_hash, k.scopes,
                  k.revoked_at, k.expires_at,
                  u.org_id
           FROM api_key k
           JOIN app_user u ON k.user_id = u.id
           WHERE k.key_prefix = $1""",
        key_prefix,
    )

    raw_bytes = raw_key.encode("utf-8")
    for row in rows:
        if not bcrypt.checkpw(raw_bytes, row["key_hash"].encode("utf-8")):
            continue

        # Match found. Check lifecycle before scope so a revoked key
        # never reports a misleading "scope_missing".
        if row["revoked_at"] is not None:
            return {"allow": False, "reason": "revoked"}

        from datetime import datetime, timezone
        if row["expires_at"] is not None and row["expires_at"] <= datetime.now(timezone.utc):
            return {"allow": False, "reason": "expired"}

        if not scope_granted(row["scopes"], required_scope):
            return {"allow": False, "reason": "scope_missing"}

        await conn.execute(
            "UPDATE api_key SET last_used_at = NOW() WHERE id = $1",
            row["key_id"],
        )
        return {
            "allow": True,
            "user_id": row["user_id"],
            "org_id": row["org_id"],
            "key_id": row["key_id"],
            "scopes": list(row["scopes"]),
        }

    return {"allow": False, "reason": "not_found"}


__all__ = [
    "PRODUCT_FULL_ACTIONS",
    "issue_key",
    "prefix_for_scopes",
    "scope_granted",
    "validate_key",
]

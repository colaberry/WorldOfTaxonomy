-- Migration 004: email_send_log + idempotent backfill helper.
--
-- Purpose: rate-limit + budget-cap signup-driven email sends so a bot
-- cannot drain the Resend budget. Every magic-link email writes a row
-- here BEFORE the signup endpoint returns 202; the budget guard reads
-- this table to count sends in the last hour and refuses new signups
-- when over a configurable cap (default 200/hour).
--
-- email_hash is sha256(lower(email)) so the table can support abuse
-- pattern queries (e.g. "is this email getting hammered?") without
-- storing raw addresses on hot paths.
--
-- Row size: ~120 bytes. At the default 200/hour cap and a 7-day
-- retention, max table size is ~4 MB. Cleanup is a cron job documented
-- in the runbook, not enforced by this migration.

CREATE TABLE IF NOT EXISTS email_send_log (
    id          BIGSERIAL PRIMARY KEY,
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    email_hash  TEXT,
    ip_address  TEXT,
    purpose     TEXT NOT NULL DEFAULT 'magic_link'
                CHECK (purpose IN ('magic_link', 'key_issued', 'key_revoked', 'other'))
);

-- Hot-path queries are "count rows since some recent timestamp".
-- A regular btree on sent_at lets us answer that with an index range
-- scan without touching every row.
CREATE INDEX IF NOT EXISTS idx_email_send_log_sent_at
    ON email_send_log(sent_at);

-- Optional secondary index for abuse triage. Cheap; ~24 bytes per row.
CREATE INDEX IF NOT EXISTS idx_email_send_log_email_hash
    ON email_send_log(email_hash) WHERE email_hash IS NOT NULL;

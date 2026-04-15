-- Migration 002: Add source_file_hash for audit trail
-- SHA-256 hash of the downloaded data file used to populate each system.
-- Allows auditors to re-download the source and verify data integrity.

ALTER TABLE classification_system
  ADD COLUMN IF NOT EXISTS source_file_hash TEXT;

-- WorldOfTaxanomy PostgreSQL Schema
-- Federation model: multiple classification systems as equal peers

-- ============================================================
-- Classification Systems (NAICS, ISIC, NACE, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS classification_system (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    full_name   TEXT,
    region      TEXT,
    version     TEXT,
    authority   TEXT,
    url         TEXT,
    tint_color  TEXT,
    node_count  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Classification Nodes (every code in every system)
-- ============================================================
CREATE TABLE IF NOT EXISTS classification_node (
    id           SERIAL PRIMARY KEY,
    system_id    TEXT NOT NULL REFERENCES classification_system(id) ON DELETE CASCADE,
    code         TEXT NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT,
    level        INTEGER NOT NULL DEFAULT 0,
    parent_code  TEXT,
    sector_code  TEXT,
    is_leaf      BOOLEAN DEFAULT FALSE,
    seq_order    INTEGER DEFAULT 0,
    search_vector TSVECTOR,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(system_id, code)
);

-- Indexes for hierarchy navigation
CREATE INDEX IF NOT EXISTS idx_node_system ON classification_node(system_id);
CREATE INDEX IF NOT EXISTS idx_node_parent ON classification_node(system_id, parent_code);
CREATE INDEX IF NOT EXISTS idx_node_level ON classification_node(system_id, level);
CREATE INDEX IF NOT EXISTS idx_node_sector ON classification_node(system_id, sector_code);
CREATE INDEX IF NOT EXISTS idx_node_code ON classification_node(code);

-- GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_node_search ON classification_node USING GIN(search_vector);

-- Auto-update search_vector on INSERT or UPDATE
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.code, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_node_search_vector ON classification_node;
CREATE TRIGGER trg_node_search_vector
    BEFORE INSERT OR UPDATE ON classification_node
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- ============================================================
-- Equivalence Edges (cross-system mappings)
-- ============================================================
CREATE TABLE IF NOT EXISTS equivalence (
    id              SERIAL PRIMARY KEY,
    source_system   TEXT NOT NULL,
    source_code     TEXT NOT NULL,
    target_system   TEXT NOT NULL,
    target_code     TEXT NOT NULL,
    match_type      TEXT NOT NULL DEFAULT 'partial'
                    CHECK (match_type IN ('exact', 'partial', 'broad', 'narrow')),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_system, source_code, target_system, target_code)
);

-- Indexes for bidirectional lookup
CREATE INDEX IF NOT EXISTS idx_equiv_source ON equivalence(source_system, source_code);
CREATE INDEX IF NOT EXISTS idx_equiv_target ON equivalence(target_system, target_code);

-- ============================================================
-- Domain Taxonomies (ICD, ATC, HS codes - future)
-- ============================================================
CREATE TABLE IF NOT EXISTS domain_taxonomy (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    full_name   TEXT,
    authority   TEXT,
    url         TEXT,
    code_count  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Link table: which domain taxonomies attach to which industry nodes
CREATE TABLE IF NOT EXISTS node_taxonomy_link (
    id              SERIAL PRIMARY KEY,
    system_id       TEXT NOT NULL,
    node_code       TEXT NOT NULL,
    taxonomy_id     TEXT NOT NULL REFERENCES domain_taxonomy(id) ON DELETE CASCADE,
    relevance       TEXT DEFAULT 'primary'
                    CHECK (relevance IN ('primary', 'secondary', 'related')),
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(system_id, node_code, taxonomy_id)
);

CREATE INDEX IF NOT EXISTS idx_ntl_node ON node_taxonomy_link(system_id, node_code);
CREATE INDEX IF NOT EXISTS idx_ntl_taxonomy ON node_taxonomy_link(taxonomy_id);

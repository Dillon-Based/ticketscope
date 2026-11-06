-- 0001: extensions, read-only default grants, the issue table and corpus_meta.
-- Applied once by the migrate Job as the app owner (AD-7).

-- Neither extension is `trusted`, so the Cluster's postInitApplicationSQL creates
-- both as superuser. These are no-ops then, and keep the schema self-describing.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_textsearch;

-- Before any table: everything the app owner creates from here on is readable
-- by ticketscope_ro without a per-table grant (AD-7).
GRANT USAGE ON SCHEMA public TO ticketscope_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ticketscope_ro;

CREATE TABLE issue (
    number          integer     PRIMARY KEY,
    title           text        NOT NULL,
    body            text,
    url             text        NOT NULL,
    state           text        NOT NULL CHECK (state IN ('open', 'closed')),
    state_reason    text,
    created_at      timestamptz NOT NULL,
    closed_at       timestamptz,
    kind            text        NOT NULL CHECK (kind IN ('short', 'log_heavy')),
    outcome_status  text        NOT NULL DEFAULT 'unknown'
        CHECK (outcome_status IN
            ('fixed', 'duplicate', 'not_planned', 'stale', 'answered', 'unknown')),
    outcome_summary text,
    outcome_source  text
        CHECK (outcome_source IN ('label', 'linked_pr', 'closing_comment')),
    outcome_ref     text,
    -- Title and body, written by load; ranked by pg_textsearch BM25 (AD-9).
    search_text     text        NOT NULL
);

CREATE INDEX issue_search_bm25_idx ON issue USING bm25 (search_text)
    WITH (text_config = 'english');

-- Exactly one row, written by load (AD-21).
CREATE TABLE corpus_meta (
    singleton             boolean     PRIMARY KEY DEFAULT true CHECK (singleton),
    snapshot_version      text        NOT NULL,
    embedding_model_id    text,
    preprocessing_version text,
    loaded_at             timestamptz NOT NULL DEFAULT now()
);

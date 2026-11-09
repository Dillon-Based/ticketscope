-- 0002: embeddings per (issue, model), written only by load (AD-21, AD-7).
-- The vector column is unsized so a second model of another dimension can sit beside the
-- first; dense search is an exact scan filtered by model_id, so there is no vector index.
-- ticketscope_ro reads it through the default privileges set in 0001.
CREATE TABLE issue_embedding (
    issue_number integer NOT NULL REFERENCES issue (number) ON DELETE CASCADE,
    model_id     text    NOT NULL,
    embedding    vector  NOT NULL,
    PRIMARY KEY (issue_number, model_id)
);

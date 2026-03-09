-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ──────────────────────────────────────
-- Sources: origin of collected content
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS sources (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    source_type     VARCHAR(50) NOT NULL,          -- twitter, youtube, rss, arxiv, github
    url             TEXT,
    reliability     FLOAT DEFAULT 0.5,
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────
-- Content: every collected item
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS content (
    id              SERIAL PRIMARY KEY,
    source_id       INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    external_id     VARCHAR(255),
    title           TEXT,
    body            TEXT NOT NULL,
    url             TEXT,
    author          VARCHAR(255),
    published_at    TIMESTAMPTZ,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    content_type    VARCHAR(50) NOT NULL,           -- tweet, video, article, paper, repo
    language        VARCHAR(10) DEFAULT 'en',
    engagement      JSONB DEFAULT '{}',             -- {likes, shares, views, stars...}
    metadata        JSONB DEFAULT '{}',
    is_spam         BOOLEAN DEFAULT FALSE,
    UNIQUE(source_id, external_id)
);

-- ──────────────────────────────────────
-- Embeddings: vector representations
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS embeddings (
    id              SERIAL PRIMARY KEY,
    content_id      INTEGER REFERENCES content(id) ON DELETE CASCADE UNIQUE,
    embedding       vector(1536) NOT NULL,
    model           VARCHAR(100) DEFAULT 'text-embedding-3-small',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────
-- Topics: detected topic clusters
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS topics (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    keywords        JSONB DEFAULT '[]',
    content_count   INTEGER DEFAULT 0,
    trend_score     FLOAT DEFAULT 0.0,
    first_seen      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW(),
    cluster_id      INTEGER
);

-- ──────────────────────────────────────
-- Topic ↔ Content: many-to-many
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS topic_content (
    topic_id        INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    content_id      INTEGER REFERENCES content(id) ON DELETE CASCADE,
    relevance       FLOAT DEFAULT 1.0,
    PRIMARY KEY (topic_id, content_id)
);

-- ──────────────────────────────────────
-- Trends: time-series trend snapshots
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS trends (
    id              SERIAL PRIMARY KEY,
    topic_id        INTEGER REFERENCES topics(id) ON DELETE CASCADE,
    trend_score     FLOAT NOT NULL,
    content_velocity FLOAT DEFAULT 0.0,
    engagement_weight FLOAT DEFAULT 0.0,
    source_authority FLOAT DEFAULT 0.0,
    snapshot_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ──────────────────────────────────────
-- Reports: generated intelligence reports
-- ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS reports (
    id              SERIAL PRIMARY KEY,
    report_date     DATE NOT NULL UNIQUE,
    title           VARCHAR(500),
    summary         TEXT,
    sections        JSONB NOT NULL DEFAULT '{}',    -- {announcements, breakthroughs, tools, discussions, insights}
    source_refs     JSONB DEFAULT '[]',             -- [{content_id, title, url}]
    generated_at    TIMESTAMPTZ DEFAULT NOW(),
    model_used      VARCHAR(100)
);

-- ──────────────────────────────────────
-- Indexes
-- ──────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_content_published    ON content (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_type         ON content (content_type);
CREATE INDEX IF NOT EXISTS idx_content_source       ON content (source_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_vec       ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_trends_snapshot      ON trends (snapshot_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_date         ON reports (report_date DESC);

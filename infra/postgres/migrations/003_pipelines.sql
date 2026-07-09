-- Pipeline persistence table

CREATE TABLE IF NOT EXISTS pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id TEXT NOT NULL UNIQUE,
    channel_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'topic',
    stages JSONB NOT NULL DEFAULT '{}',
    data JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pipelines_pipeline_id ON pipelines(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_pipelines_status ON pipelines(status);

-- Procrastinate schema — generated from procrastinate.schema module
-- This creates all tables needed by Procrastinate for job queue management

CREATE SCHEMA IF NOT EXISTS procrastinate;

CREATE TABLE IF NOT EXISTS procrastinate_jobs (
    id bigserial PRIMARY KEY,
    queue text NOT NULL,
    task_name text NOT NULL,
    priority integer NOT NULL DEFAULT 0,
    lock text,
    args jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'todo',
    attempts integer NOT NULL DEFAULT 0,
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    attempts_info jsonb NOT NULL DEFAULT '[]'::jsonb,
    lock_cycle_id integer,
    lock_id integer
);

CREATE INDEX IF NOT EXISTS idx_procrastinate_jobs_on_task_status_scheduled
    ON procrastinate_jobs (task_name, status, priority, id)
    WHERE status IN ('todo', 'doing');

CREATE INDEX IF NOT EXISTS idx_procrastinate_jobs_on_queue
    ON procrastinate_jobs (queue, priority, id)
    WHERE status = 'todo';

CREATE INDEX IF NOT EXISTS idx_procrastinate_jobs_on_lock
    ON procrastinate_jobs (lock, lock_cycle_id)
    WHERE status IN ('todo', 'doing');

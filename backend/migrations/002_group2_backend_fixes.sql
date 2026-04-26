-- Group 2 backend fixes: missing columns + bulk score update RPC

ALTER TABLE resumes
ADD COLUMN IF NOT EXISTS resume_embedding JSONB;

ALTER TABLE preferences
ADD COLUMN IF NOT EXISTS preferred_domains TEXT[] DEFAULT '{}';

ALTER TABLE preferences
ADD COLUMN IF NOT EXISTS stipend_min INTEGER DEFAULT 0;

ALTER TABLE cold_emails
ADD COLUMN IF NOT EXISTS tone TEXT;

ALTER TABLE cold_emails
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

CREATE OR REPLACE FUNCTION bulk_update_job_scores(
    p_job_ids UUID[],
    p_scores DOUBLE PRECISION[]
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    IF p_job_ids IS NULL OR p_scores IS NULL THEN
        RETURN 0;
    END IF;

    IF array_length(p_job_ids, 1) IS DISTINCT FROM array_length(p_scores, 1) THEN
        RAISE EXCEPTION 'p_job_ids and p_scores must have the same length';
    END IF;

    UPDATE jobs AS j
    SET score = payload.score
    FROM (
        SELECT UNNEST(p_job_ids) AS job_id, UNNEST(p_scores) AS score
    ) AS payload
    WHERE j.id = payload.job_id;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$;

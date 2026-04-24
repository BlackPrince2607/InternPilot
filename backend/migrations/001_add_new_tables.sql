-- Companies table (may already exist, use CREATE TABLE IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    domain TEXT,
    careers_url TEXT,
    contact_emails TEXT[] DEFAULT '{}',
    quality_score INTEGER DEFAULT 50,
    email_crawled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table (may already exist)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    external_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    location TEXT,
    remote_type TEXT,
    description TEXT,
    apply_url TEXT,
    source_name TEXT,
    skills_required JSONB,
    experience_level TEXT,
    posted_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    score FLOAT,
    company_score FLOAT,
    recency_score FLOAT,
    source_url TEXT,
    raw_data JSONB,
    job_domain TEXT,
    job_embedding JSONB,
    stipend TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cold emails sent or generated
CREATE TABLE IF NOT EXISTS cold_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    recipient_email TEXT,
    subject TEXT,
    body TEXT NOT NULL,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Application tracker (counters only)
CREATE TABLE IF NOT EXISTS user_activity (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    jobs_applied_count INTEGER DEFAULT 0,
    emails_sent_count INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User interaction tracking for adaptive ranking
CREATE TABLE IF NOT EXISTS user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    action TEXT NOT NULL CHECK (action IN ('view', 'apply', 'skip')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast job lookups
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source_name);
CREATE INDEX IF NOT EXISTS idx_cold_emails_user ON cold_emails(user_id);
CREATE INDEX IF NOT EXISTS idx_cold_emails_sent_at ON cold_emails(sent_at);
CREATE INDEX IF NOT EXISTS idx_user_interactions_user ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_interactions_job ON user_interactions(job_id);

ALTER TABLE companies ADD COLUMN IF NOT EXISTS domain TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS location TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS remote_type TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_url TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_name TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS skills_required JSONB;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS experience_level TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS posted_at TIMESTAMPTZ;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS score FLOAT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_score FLOAT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS recency_score FLOAT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS raw_data JSONB;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_domain TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_embedding JSONB;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS stipend TEXT;

ALTER TABLE cold_emails ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE cold_emails ADD COLUMN IF NOT EXISTS job_id UUID REFERENCES jobs(id) ON DELETE SET NULL;
ALTER TABLE cold_emails ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE SET NULL;
ALTER TABLE cold_emails ADD COLUMN IF NOT EXISTS recipient_email TEXT;
ALTER TABLE cold_emails ADD COLUMN IF NOT EXISTS subject TEXT;
ALTER TABLE cold_emails ADD COLUMN IF NOT EXISTS body TEXT;
ALTER TABLE cold_emails ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ;
ALTER TABLE cold_emails ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE user_activity ADD COLUMN IF NOT EXISTS jobs_applied_count INTEGER DEFAULT 0;
ALTER TABLE user_activity ADD COLUMN IF NOT EXISTS emails_sent_count INTEGER DEFAULT 0;
ALTER TABLE user_activity ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE user_interactions ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE user_interactions ADD COLUMN IF NOT EXISTS job_id UUID REFERENCES jobs(id) ON DELETE CASCADE;
ALTER TABLE user_interactions ADD COLUMN IF NOT EXISTS action TEXT;
ALTER TABLE user_interactions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_external_id_unique ON jobs(external_id);

CREATE OR REPLACE FUNCTION increment_jobs_applied(target_user_id UUID)
RETURNS TABLE (jobs_applied_count INTEGER, emails_sent_count INTEGER)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO user_activity (user_id, jobs_applied_count, emails_sent_count, updated_at)
    VALUES (target_user_id, 1, 0, NOW())
    ON CONFLICT (user_id)
    DO UPDATE SET
        jobs_applied_count = user_activity.jobs_applied_count + 1,
        updated_at = NOW();

    RETURN QUERY
    SELECT ua.jobs_applied_count, ua.emails_sent_count
    FROM user_activity ua
    WHERE ua.user_id = target_user_id;
END;
$$;

CREATE OR REPLACE FUNCTION increment_emails_sent(target_user_id UUID)
RETURNS TABLE (jobs_applied_count INTEGER, emails_sent_count INTEGER)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO user_activity (user_id, jobs_applied_count, emails_sent_count, updated_at)
    VALUES (target_user_id, 0, 1, NOW())
    ON CONFLICT (user_id)
    DO UPDATE SET
        emails_sent_count = user_activity.emails_sent_count + 1,
        updated_at = NOW();

    RETURN QUERY
    SELECT ua.jobs_applied_count, ua.emails_sent_count
    FROM user_activity ua
    WHERE ua.user_id = target_user_id;
END;
$$;

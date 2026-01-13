-- ContextBridge Complete Schema Migration
-- Includes: RAG, Conversations, Analytics, Michael D1 Swimming
-- Execute in Supabase SQL Editor

-- ============================================================================
-- STEP 1: Enable Extensions
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- STEP 2: Context Embeddings (RAG System)
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_embeddings (
    id BIGSERIAL PRIMARY KEY,
    product TEXT NOT NULL,  -- biddeed, zonewise, lifeos, spd, michael
    filepath TEXT NOT NULL,  -- /CONTEXT/ARCHITECTURE.md
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS context_embeddings_product_idx 
    ON context_embeddings(product);

CREATE INDEX IF NOT EXISTS context_embeddings_filepath_idx 
    ON context_embeddings(filepath);

CREATE INDEX IF NOT EXISTS context_embeddings_embedding_idx 
    ON context_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================================
-- STEP 3: Vector Search Functions
-- ============================================================================

CREATE OR REPLACE FUNCTION match_context_embeddings(
    query_embedding vector(1536),
    match_product text,
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id bigint,
    product text,
    filepath text,
    chunk_index integer,
    content text,
    char_count integer,
    similarity float,
    metadata jsonb
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ce.id,
        ce.product,
        ce.filepath,
        ce.chunk_index,
        ce.content,
        ce.char_count,
        1 - (ce.embedding <=> query_embedding) AS similarity,
        ce.metadata
    FROM context_embeddings ce
    WHERE ce.product = match_product
        AND 1 - (ce.embedding <=> query_embedding) > match_threshold
    ORDER BY ce.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION execute_readonly_sql(query text)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result json;
BEGIN
    IF UPPER(TRIM(query)) NOT LIKE 'SELECT%' THEN
        RAISE EXCEPTION 'Only SELECT queries are allowed';
    END IF;
    
    EXECUTE 'SELECT json_agg(row_to_json(t)) FROM (' || query || ') t'
        INTO result;
    
    RETURN COALESCE(result, '[]'::json);
END;
$$;

-- ============================================================================
-- STEP 4: Conversation Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS contextbridge_conversations (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL UNIQUE,
    product TEXT NOT NULL,
    user_id TEXT NOT NULL,
    messages JSONB DEFAULT '[]'::jsonb,
    state JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS contextbridge_conversations_user_idx 
    ON contextbridge_conversations(user_id);

CREATE INDEX IF NOT EXISTS contextbridge_conversations_product_idx 
    ON contextbridge_conversations(product);

CREATE INDEX IF NOT EXISTS contextbridge_conversations_updated_at_idx 
    ON contextbridge_conversations(updated_at DESC);

-- ============================================================================
-- STEP 5: Analytics & Monitoring
-- ============================================================================

CREATE TABLE IF NOT EXISTS contextbridge_analytics (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    product TEXT NOT NULL,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    intent TEXT,
    agents_used TEXT[],
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd NUMERIC(10, 6),
    model_used TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS contextbridge_analytics_product_idx 
    ON contextbridge_analytics(product);

CREATE INDEX IF NOT EXISTS contextbridge_analytics_created_at_idx 
    ON contextbridge_analytics(created_at DESC);

CREATE INDEX IF NOT EXISTS contextbridge_analytics_user_idx 
    ON contextbridge_analytics(user_id);

-- ============================================================================
-- STEP 6: Michael D1 Swimming Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS swim_times (
    id BIGSERIAL PRIMARY KEY,
    swimmer_id TEXT DEFAULT 'michael_shapira',
    event TEXT NOT NULL,
    time_scy TEXT NOT NULL,
    time_lcy TEXT,
    meet_name TEXT,
    meet_date DATE,
    is_personal_best BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS swim_times_swimmer_idx ON swim_times(swimmer_id);
CREATE INDEX IF NOT EXISTS swim_times_event_idx ON swim_times(event);
CREATE INDEX IF NOT EXISTS swim_times_meet_date_idx ON swim_times(meet_date DESC);

CREATE TABLE IF NOT EXISTS target_schools (
    id BIGSERIAL PRIMARY KEY,
    swimmer_id TEXT DEFAULT 'michael_shapira',
    school_name TEXT NOT NULL,
    conference TEXT,
    fit_score INTEGER,
    priority INTEGER,
    coach_name TEXT,
    recruiting_times JSONB,
    visit_date DATE,
    visit_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS target_schools_swimmer_idx ON target_schools(swimmer_id);
CREATE INDEX IF NOT EXISTS target_schools_priority_idx ON target_schools(priority);

CREATE TABLE IF NOT EXISTS recruiting_outreach (
    id BIGSERIAL PRIMARY KEY,
    swimmer_id TEXT DEFAULT 'michael_shapira',
    school_name TEXT NOT NULL,
    coach_name TEXT NOT NULL,
    email_sent_date DATE,
    email_subject TEXT,
    email_body TEXT,
    response_received BOOLEAN DEFAULT FALSE,
    response_date DATE,
    response_summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS recruiting_outreach_swimmer_idx ON recruiting_outreach(swimmer_id);
CREATE INDEX IF NOT EXISTS recruiting_outreach_school_idx ON recruiting_outreach(school_name);

CREATE TABLE IF NOT EXISTS meet_schedule (
    id BIGSERIAL PRIMARY KEY,
    swimmer_id TEXT DEFAULT 'michael_shapira',
    meet_name TEXT NOT NULL,
    meet_date DATE NOT NULL,
    location TEXT,
    events_entered TEXT[],
    is_championship BOOLEAN DEFAULT FALSE,
    is_shabbat_conflict BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS meet_schedule_swimmer_idx ON meet_schedule(swimmer_id);
CREATE INDEX IF NOT EXISTS meet_schedule_date_idx ON meet_schedule(meet_date);

-- ============================================================================
-- STEP 7: Row Level Security
-- ============================================================================

ALTER TABLE context_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE contextbridge_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE contextbridge_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE swim_times ENABLE ROW LEVEL SECURITY;
ALTER TABLE target_schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE recruiting_outreach ENABLE ROW LEVEL SECURITY;
ALTER TABLE meet_schedule ENABLE ROW LEVEL SECURITY;

-- Service role policies (full access)
CREATE POLICY "Enable all for service role" ON context_embeddings
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON contextbridge_conversations
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON contextbridge_analytics
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON swim_times
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON target_schools
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON recruiting_outreach
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON meet_schedule
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ============================================================================
-- STEP 8: Seed Data - Michael D1 Target Schools (27 schools)
-- ============================================================================

INSERT INTO target_schools (school_name, conference, priority, coach_name, recruiting_times) VALUES
('University of Florida', 'SEC', 1, 'Anthony Nesty', '{"50_free_walkOn":"21.5","100_free_walkOn":"46.5"}'::jsonb),
('University of Texas', 'Big 12', 2, 'Bob Bowman', '{"50_free_walkOn":"21.0","100_free_walkOn":"45.5"}'::jsonb),
('NC State', 'ACC', 3, 'Braden Holloway', '{"50_free_walkOn":"21.2","100_free_walkOn":"46.0"}'::jsonb),
('University of Virginia', 'ACC', 4, 'Todd DeSorbo', '{"50_free_walkOn":"20.8","100_free_walkOn":"45.0"}'::jsonb),
('University of Michigan', 'Big Ten', 5, 'Mike Bottom', '{"50_free_walkOn":"21.3","100_free_walkOn":"46.2"}'::jsonb),
('Georgia Tech', 'ACC', 6, 'Courtney Shealy Hart', '{"50_free_walkOn":"21.8","100_free_walkOn":"47.0"}'::jsonb),
('Texas A&M', 'SEC', 7, 'Jay Benefiel', '{"50_free_walkOn":"21.5","100_free_walkOn":"46.5"}'::jsonb),
('Stanford', 'Pac-12', 8, 'Dan Schemmel', '{"50_free_walkOn":"20.5","100_free_walkOn":"44.8"}'::jsonb),
('USC', 'Big Ten', 9, 'Lea Maurer', '{"50_free_walkOn":"21.0","100_free_walkOn":"45.5"}'::jsonb),
('California', 'ACC', 10, 'Dave Durden', '{"50_free_walkOn":"20.8","100_free_walkOn":"45.2"}'::jsonb),
('Arizona State', 'Big 12', 11, 'Herbie Behm', '{"50_free_walkOn":"21.5","100_free_walkOn":"46.5"}'::jsonb),
('Louisville', 'ACC', 12, 'Arthur Albiero', '{"50_free_walkOn":"21.8","100_free_walkOn":"47.2"}'::jsonb),
('Tennessee', 'SEC', 13, 'Matt Kredich', '{"50_free_walkOn":"21.5","100_free_walkOn":"46.8"}'::jsonb),
('Auburn', 'SEC', 14, 'Ryan Wochomurka', '{"50_free_walkOn":"21.6","100_free_walkOn":"47.0"}'::jsonb),
('Alabama', 'SEC', 15, 'Coley Stickels', '{"50_free_walkOn":"21.7","100_free_walkOn":"47.2"}'::jsonb),
('Florida State', 'ACC', 16, 'Neal Studd', '{"50_free_walkOn":"22.0","100_free_walkOn":"47.5"}'::jsonb),
('Ohio State', 'Big Ten', 17, 'Bill Dorenkott', '{"50_free_walkOn":"21.5","100_free_walkOn":"46.5"}'::jsonb),
('Indiana', 'Big Ten', 18, 'Ray Looze', '{"50_free_walkOn":"21.3","100_free_walkOn":"46.3"}'::jsonb),
('Northwestern', 'Big Ten', 19, 'Katie Robinson', '{"50_free_walkOn":"21.8","100_free_walkOn":"47.5"}'::jsonb),
('Wisconsin', 'Big Ten', 20, 'Chris Clark', '{"50_free_walkOn":"21.6","100_free_walkOn":"47.0"}'::jsonb),
('Miami', 'ACC', 21, 'Andy Kershaw', '{"50_free_walkOn":"22.2","100_free_walkOn":"48.0"}'::jsonb),
('Duke', 'ACC', 22, 'Travis Michelson', '{"50_free_walkOn":"21.5","100_free_walkOn":"46.8"}'::jsonb),
('Notre Dame', 'ACC', 23, 'Mike Litzinger', '{"50_free_walkOn":"21.8","100_free_walkOn":"47.5"}'::jsonb),
('Pittsburgh', 'ACC', 24, 'John Hargis', '{"50_free_walkOn":"22.0","100_free_walkOn":"48.0"}'::jsonb),
('Virginia Tech', 'ACC', 25, 'Sergio Lopez Miro', '{"50_free_walkOn":"22.2","100_free_walkOn":"48.5"}'::jsonb),
('South Carolina', 'SEC', 26, 'Jeff Poppell', '{"50_free_walkOn":"22.0","100_free_walkOn":"48.0"}'::jsonb),
('Missouri', 'SEC', 27, 'Andrew Grevers', '{"50_free_walkOn":"21.8","100_free_walkOn":"47.5"}'::jsonb)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- STEP 9: Analytics Views
-- ============================================================================

CREATE OR REPLACE VIEW context_stats AS
SELECT
    product,
    filepath,
    COUNT(*) as chunk_count,
    SUM(char_count) as total_chars,
    MIN(created_at) as first_indexed,
    MAX(updated_at) as last_updated
FROM context_embeddings
GROUP BY product, filepath
ORDER BY product, filepath;

CREATE OR REPLACE VIEW daily_query_stats AS
SELECT
    DATE(created_at) as date,
    product,
    COUNT(*) as query_count,
    AVG(processing_time_ms) as avg_time_ms,
    SUM(cost_usd) as total_cost,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) FILTER (WHERE success = TRUE) as successful_queries,
    COUNT(*) FILTER (WHERE success = FALSE) as failed_queries
FROM contextbridge_analytics
GROUP BY DATE(created_at), product
ORDER BY date DESC, product;

CREATE OR REPLACE VIEW michael_progress AS
SELECT
    (SELECT COUNT(*) FROM swim_times WHERE swimmer_id = 'michael_shapira') as total_times,
    (SELECT COUNT(*) FROM swim_times WHERE swimmer_id = 'michael_shapira' AND is_personal_best = TRUE) as personal_bests,
    (SELECT COUNT(*) FROM recruiting_outreach WHERE swimmer_id = 'michael_shapira') as emails_sent,
    (SELECT COUNT(*) FROM recruiting_outreach WHERE swimmer_id = 'michael_shapira' AND response_received = TRUE) as responses_received,
    (SELECT COUNT(*) FROM target_schools WHERE swimmer_id = 'michael_shapira' AND visit_date IS NOT NULL) as visits_completed,
    (SELECT COUNT(*) FROM meet_schedule WHERE swimmer_id = 'michael_shapira' AND meet_date >= CURRENT_DATE) as upcoming_meets;

-- ============================================================================
-- STEP 10: Grant Permissions
-- ============================================================================

GRANT ALL ON context_embeddings TO service_role;
GRANT ALL ON contextbridge_conversations TO service_role;
GRANT ALL ON contextbridge_analytics TO service_role;
GRANT ALL ON swim_times TO service_role;
GRANT ALL ON target_schools TO service_role;
GRANT ALL ON recruiting_outreach TO service_role;
GRANT ALL ON meet_schedule TO service_role;

GRANT EXECUTE ON FUNCTION match_context_embeddings TO service_role;
GRANT EXECUTE ON FUNCTION execute_readonly_sql TO service_role;

-- ============================================================================
-- SUCCESS
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ ContextBridge schema created successfully!';
    RAISE NOTICE '   Tables: 7 (embeddings, conversations, analytics, swim_times, target_schools, recruiting_outreach, meet_schedule)';
    RAISE NOTICE '   Functions: 2 (match_context_embeddings, execute_readonly_sql)';
    RAISE NOTICE '   Views: 3 (context_stats, daily_query_stats, michael_progress)';
    RAISE NOTICE '   Seed data: 27 target schools for Michael Shapira';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 Next steps:';
    RAISE NOTICE '   1. Index documents: python src/rag_system.py index <product> /CONTEXT/';
    RAISE NOTICE '   2. Test SQL agent: python src/sql_agent.py michael "What are my target schools?"';
    RAISE NOTICE '   3. Test full query: python src/contextbridge_orchestrator.py michael "What is my gap to UF?"';
END $$;

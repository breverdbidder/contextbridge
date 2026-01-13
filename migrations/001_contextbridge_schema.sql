-- ContextBridge RAG System - Supabase Schema
-- Migration: Add pgvector support for semantic search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create context embeddings table
CREATE TABLE IF NOT EXISTS context_embeddings (
    id BIGSERIAL PRIMARY KEY,
    product TEXT NOT NULL,  -- biddeed, zonewise, lifeos, spd
    filepath TEXT NOT NULL,  -- /CONTEXT/ARCHITECTURE.md
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    embedding vector(1536) NOT NULL,  -- OpenAI text-embedding-3-small
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for fast retrieval
CREATE INDEX IF NOT EXISTS context_embeddings_product_idx 
    ON context_embeddings(product);

CREATE INDEX IF NOT EXISTS context_embeddings_filepath_idx 
    ON context_embeddings(filepath);

CREATE INDEX IF NOT EXISTS context_embeddings_created_at_idx 
    ON context_embeddings(created_at DESC);

-- Create vector similarity index (HNSW for fast approximate search)
-- This enables sub-millisecond similarity search over millions of vectors
CREATE INDEX IF NOT EXISTS context_embeddings_embedding_idx 
    ON context_embeddings 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Create function for vector similarity search
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

-- Create function for hybrid search (semantic + keyword)
CREATE OR REPLACE FUNCTION hybrid_search_context(
    query_embedding vector(1536),
    query_text text,
    match_product text,
    match_count int DEFAULT 5,
    semantic_weight float DEFAULT 0.7,
    keyword_weight float DEFAULT 0.3
)
RETURNS TABLE (
    id bigint,
    product text,
    filepath text,
    chunk_index integer,
    content text,
    combined_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT
            ce.id,
            ce.product,
            ce.filepath,
            ce.chunk_index,
            ce.content,
            1 - (ce.embedding <=> query_embedding) AS similarity
        FROM context_embeddings ce
        WHERE ce.product = match_product
    ),
    keyword_results AS (
        SELECT
            ce.id,
            ce.product,
            ce.filepath,
            ce.chunk_index,
            ce.content,
            ts_rank(to_tsvector('english', ce.content), plainto_tsquery('english', query_text)) AS keyword_score
        FROM context_embeddings ce
        WHERE ce.product = match_product
            AND to_tsvector('english', ce.content) @@ plainto_tsquery('english', query_text)
    )
    SELECT
        COALESCE(s.id, k.id) as id,
        COALESCE(s.product, k.product) as product,
        COALESCE(s.filepath, k.filepath) as filepath,
        COALESCE(s.chunk_index, k.chunk_index) as chunk_index,
        COALESCE(s.content, k.content) as content,
        (COALESCE(s.similarity, 0) * semantic_weight + COALESCE(k.keyword_score, 0) * keyword_weight) as combined_score
    FROM semantic_results s
    FULL OUTER JOIN keyword_results k ON s.id = k.id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;

-- Create conversation memory table for ContextBridge
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

-- Create analytics table for query tracking
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

-- Create competitive intelligence checkpoints table (if not exists)
CREATE TABLE IF NOT EXISTS competitive_intel_checkpoints (
    id BIGSERIAL PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    competitor_name TEXT NOT NULL,
    current_stage INTEGER NOT NULL,
    state JSONB NOT NULL,
    workflow_status TEXT DEFAULT 'running',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS competitive_intel_checkpoints_analysis_id_idx 
    ON competitive_intel_checkpoints(analysis_id);

CREATE INDEX IF NOT EXISTS competitive_intel_checkpoints_competitor_idx 
    ON competitive_intel_checkpoints(competitor_name);

-- Enable Row Level Security (RLS)
ALTER TABLE context_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE contextbridge_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE contextbridge_analytics ENABLE ROW LEVEL SECURITY;

-- Create policies (allow service role full access)
CREATE POLICY "Enable all for service role" ON context_embeddings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON contextbridge_conversations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON contextbridge_analytics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Grant permissions
GRANT ALL ON context_embeddings TO service_role;
GRANT ALL ON contextbridge_conversations TO service_role;
GRANT ALL ON contextbridge_analytics TO service_role;
GRANT ALL ON competitive_intel_checkpoints TO service_role;

-- Create helpful views
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
    COUNT(DISTINCT user_id) as unique_users
FROM contextbridge_analytics
GROUP BY DATE(created_at), product
ORDER BY date DESC, product;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'ContextBridge schema created successfully!';
    RAISE NOTICE 'Tables: context_embeddings, contextbridge_conversations, contextbridge_analytics';
    RAISE NOTICE 'Functions: match_context_embeddings(), hybrid_search_context()';
    RAISE NOTICE 'Views: context_stats, daily_query_stats';
END $$;

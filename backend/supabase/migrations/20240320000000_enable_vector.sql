-- Enable the vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the vector operator class (wrapped in DO block to handle if exists)
DO $$
BEGIN
    -- Check if operator class already exists
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_opclass 
        WHERE opcname = 'vector_cosine_ops'
    ) THEN
        -- Create the operator class if it doesn't exist
        CREATE OPERATOR CLASS vector_cosine_ops
            DEFAULT FOR TYPE vector USING hnsw AS
            OPERATOR 1 <=> (vector, vector);
    END IF;
END
$$;

CREATE OR REPLACE FUNCTION public.search_account_embeddings(
    query_embedding vector,
    user_id TEXT,
    embedding_column TEXT DEFAULT 'embedding',
    similarity_threshold FLOAT DEFAULT 0.7,
    match_count INTEGER DEFAULT 5
) RETURNS TABLE (
    chunk_id BIGINT,
    chunk_content TEXT,
    chunk_title TEXT,
    similarity FLOAT,
    account_id TEXT,
    account_name TEXT,
    account_code TEXT,
    account_type TEXT,
    account_description TEXT
) LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
BEGIN
    -- Input validation
    IF embedding_column NOT IN ('embedding', 'jina_embedding', 'voyage_embeddings') THEN
        RAISE EXCEPTION 'Invalid embedding_column. Must be one of: embedding, jina_embedding, voyage_embeddings';
    END IF;
    
    IF similarity_threshold < 0 OR similarity_threshold > 1 THEN
        RAISE EXCEPTION 'similarity_threshold must be between 0 and 1';
    END IF;
    
    IF match_count < 1 THEN
        RAISE EXCEPTION 'match_count must be greater than 0';
    END IF;

    -- Dynamic SQL for flexible embedding column selection
    RETURN QUERY EXECUTE format(
        'SELECT 
            c.id AS chunk_id,
            c.content AS chunk_content,
            c.title AS chunk_title,
            (1 - (c.%I <=> $1)) as similarity,
            coa.account_id,
            coa.name AS account_name,
            coa.code AS account_code,
            coa.account_type,
            coa.description AS account_description
        FROM public.chunks c
        JOIN public.chart_of_accounts coa ON c.parent_id = coa.id
        WHERE 
            c.user_id = $2 
            AND c.%I IS NOT NULL
            AND (1 - (c.%I <=> $1)) >= $3
        ORDER BY similarity DESC
        LIMIT $4',
        embedding_column,
        embedding_column,
        embedding_column
    )
    USING query_embedding, user_id, similarity_threshold, match_count;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.search_account_embeddings TO authenticated;

-- Add comment explaining the function
COMMENT ON FUNCTION public.search_account_embeddings IS 
'Performs similarity search on account embeddings using cosine similarity.
Parameters:
- query_embedding: The embedding vector to search with
- user_id: The ID of the user performing the search
- embedding_column: Which embedding column to use (embedding, jina_embedding, or voyage_embeddings)
- similarity_threshold: Minimum similarity score (0-1) for results
- match_count: Maximum number of results to return';
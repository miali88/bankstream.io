-- Add vector column for embeddings to chart_of_accounts
ALTER TABLE public.chart_of_accounts
ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- Create an index for vector similarity search
CREATE INDEX IF NOT EXISTS chart_of_accounts_embedding_idx
ON public.chart_of_accounts
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Add this function for similarity search
CREATE OR REPLACE FUNCTION search_account_embeddings(
    query_embedding vector(1024),
    similarity_threshold float,
    match_count int,
    user_id text
)
RETURNS TABLE (
    id uuid,
    name text,
    description text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.name,
        a.description,
        1 - (a.embedding <=> query_embedding) AS similarity
    FROM 
        chart_of_accounts a
    WHERE
        a.user_id = user_id
        AND (1 - (a.embedding <=> query_embedding)) > similarity_threshold
    ORDER BY 
        similarity DESC
    LIMIT 
        match_count;
END;
$$; 
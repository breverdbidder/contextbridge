"""
ContextBridge RAG System with pgvector
Semantic search over /CONTEXT/ folders for all products

Features:
- OpenAI ada-002 embeddings
- Supabase pgvector storage
- Product-specific context namespacing
- Hybrid search (semantic + keyword)
- Reranking by relevance
"""

import os
from typing import List, Dict, Optional
import openai
from supabase import create_client, Client
import numpy as np


class ContextBridgeRAG:
    """
    RAG system for ContextBridge with pgvector semantic search
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        # Initialize OpenAI
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.openai_api_key
        
        # Initialize Supabase
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Embedding model
        self.embedding_model = "text-embedding-3-small"  # Cheaper than ada-002
        self.embedding_dimensions = 1536
        
        print("✅ ContextBridge RAG initialized")
        print(f"   Embedding model: {self.embedding_model}")
        print(f"   Vector dimensions: {self.embedding_dimensions}")
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create embedding vector for text using OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (1536 dimensions)
        """
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            embedding = response.data[0].embedding
            return embedding
            
        except Exception as e:
            print(f"❌ Embedding failed: {e}")
            raise
    
    def chunk_document(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Dict]:
        """
        Split document into overlapping chunks
        
        Args:
            text: Full document text
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            # If adding this paragraph exceeds chunk_size, save current chunk
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'chunk_index': chunk_index,
                    'char_count': len(current_chunk)
                })
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + para
                chunk_index += 1
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_index': chunk_index,
                'char_count': len(current_chunk)
            })
        
        return chunks
    
    def index_document(
        self,
        filepath: str,
        content: str,
        product: str,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Index a document into pgvector
        
        Args:
            filepath: Path to document (e.g., "/CONTEXT/ARCHITECTURE.md")
            content: Full document content
            product: Product namespace ("biddeed", "zonewise", "lifeos", "spd")
            metadata: Optional metadata
            
        Returns:
            Number of chunks indexed
        """
        print(f"\n📚 Indexing: {filepath}")
        print(f"   Product: {product}")
        print(f"   Length: {len(content):,} characters")
        
        # Chunk document
        chunks = self.chunk_document(content)
        print(f"   Chunks: {len(chunks)}")
        
        indexed_count = 0
        
        for chunk in chunks:
            try:
                # Create embedding
                embedding = self.create_embedding(chunk['text'])
                
                # Prepare record
                record = {
                    'product': product,
                    'filepath': filepath,
                    'chunk_index': chunk['chunk_index'],
                    'content': chunk['text'],
                    'char_count': chunk['char_count'],
                    'embedding': embedding,
                    'metadata': metadata or {}
                }
                
                # Insert into Supabase
                result = self.supabase.table('context_embeddings').insert(record).execute()
                
                if result.data:
                    indexed_count += 1
                
            except Exception as e:
                print(f"⚠️ Failed to index chunk {chunk['chunk_index']}: {e}")
        
        print(f"✅ Indexed {indexed_count}/{len(chunks)} chunks")
        return indexed_count
    
    def search(
        self,
        query: str,
        product: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Semantic search over indexed documents
        
        Args:
            query: Search query
            product: Product namespace
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of relevant chunks with similarity scores
        """
        print(f"\n🔍 RAG Search")
        print(f"   Query: {query}")
        print(f"   Product: {product}")
        print(f"   Top K: {top_k}")
        
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            
            # Perform vector similarity search using Supabase RPC
            # This calls a PostgreSQL function that uses pgvector
            result = self.supabase.rpc(
                'match_context_embeddings',
                {
                    'query_embedding': query_embedding,
                    'match_product': product,
                    'match_threshold': similarity_threshold,
                    'match_count': top_k
                }
            ).execute()
            
            results = result.data if result.data else []
            
            print(f"✅ Found {len(results)} results")
            
            # Format results
            formatted_results = []
            for i, row in enumerate(results):
                formatted_results.append({
                    'rank': i + 1,
                    'filepath': row['filepath'],
                    'chunk_index': row['chunk_index'],
                    'content': row['content'],
                    'similarity': row['similarity'],
                    'char_count': row['char_count']
                })
                
                print(f"   {i+1}. {row['filepath']} (similarity: {row['similarity']:.3f})")
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        product: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict]:
        """
        Hybrid search combining semantic and keyword matching
        
        Args:
            query: Search query
            product: Product namespace
            top_k: Number of results
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            
        Returns:
            Ranked results combining both methods
        """
        # Semantic search
        semantic_results = self.search(query, product, top_k=top_k*2)
        
        # Keyword search (simple text matching)
        keyword_results = self._keyword_search(query, product, top_k=top_k*2)
        
        # Combine and rerank
        combined_scores = {}
        
        for result in semantic_results:
            key = f"{result['filepath']}_{result['chunk_index']}"
            combined_scores[key] = {
                'result': result,
                'score': result['similarity'] * semantic_weight
            }
        
        for result in keyword_results:
            key = f"{result['filepath']}_{result['chunk_index']}"
            if key in combined_scores:
                combined_scores[key]['score'] += result['keyword_score'] * keyword_weight
            else:
                combined_scores[key] = {
                    'result': result,
                    'score': result['keyword_score'] * keyword_weight
                }
        
        # Sort by combined score
        ranked = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return [item['result'] for item in ranked[:top_k]]
    
    def _keyword_search(
        self,
        query: str,
        product: str,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Simple keyword-based search
        """
        try:
            # Use Supabase text search
            keywords = query.lower().split()
            
            results = []
            
            for keyword in keywords[:3]:  # Top 3 keywords
                result = self.supabase.table('context_embeddings')\
                    .select('*')\
                    .eq('product', product)\
                    .ilike('content', f'%{keyword}%')\
                    .limit(top_k)\
                    .execute()
                
                if result.data:
                    for row in result.data:
                        # Calculate simple keyword score
                        keyword_count = row['content'].lower().count(keyword)
                        keyword_score = min(keyword_count / 10, 1.0)
                        
                        results.append({
                            'filepath': row['filepath'],
                            'chunk_index': row['chunk_index'],
                            'content': row['content'],
                            'keyword_score': keyword_score
                        })
            
            return results[:top_k]
            
        except Exception as e:
            print(f"⚠️ Keyword search failed: {e}")
            return []
    
    def reindex_product(self, product: str, context_dir: str):
        """
        Reindex all documents for a product
        
        Args:
            product: Product namespace
            context_dir: Path to /CONTEXT/ directory
        """
        print(f"\n🔄 Reindexing {product}...")
        
        # Delete existing embeddings
        self.supabase.table('context_embeddings')\
            .delete()\
            .eq('product', product)\
            .execute()
        
        # Index all markdown files
        import os
        
        total_indexed = 0
        
        for filename in os.listdir(context_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(context_dir, filename)
                
                with open(filepath, 'r') as f:
                    content = f.read()
                
                indexed = self.index_document(
                    filepath=f"/CONTEXT/{filename}",
                    content=content,
                    product=product
                )
                
                total_indexed += indexed
        
        print(f"\n✅ Reindexing complete: {total_indexed} chunks indexed")


# ============================================================================
# SUPABASE SCHEMA SETUP
# ============================================================================

PGVECTOR_SCHEMA_SQL = """
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
    embedding vector(1536) NOT NULL,  -- OpenAI embedding dimensions
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for fast retrieval
CREATE INDEX IF NOT EXISTS context_embeddings_product_idx 
    ON context_embeddings(product);

CREATE INDEX IF NOT EXISTS context_embeddings_filepath_idx 
    ON context_embeddings(filepath);

-- Create vector similarity index (HNSW for fast approximate search)
CREATE INDEX IF NOT EXISTS context_embeddings_embedding_idx 
    ON context_embeddings 
    USING hnsw (embedding vector_cosine_ops);

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
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        context_embeddings.id,
        context_embeddings.product,
        context_embeddings.filepath,
        context_embeddings.chunk_index,
        context_embeddings.content,
        context_embeddings.char_count,
        1 - (context_embeddings.embedding <=> query_embedding) AS similarity
    FROM context_embeddings
    WHERE context_embeddings.product = match_product
        AND 1 - (context_embeddings.embedding <=> query_embedding) > match_threshold
    ORDER BY context_embeddings.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Initialize RAG
    rag = ContextBridgeRAG()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python rag_system.py index <product> <context_dir>")
        print("  python rag_system.py search <product> <query>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "index":
        if len(sys.argv) < 4:
            print("Usage: python rag_system.py index <product> <context_dir>")
            sys.exit(1)
        
        product = sys.argv[2]
        context_dir = sys.argv[3]
        
        rag.reindex_product(product, context_dir)
    
    elif command == "search":
        if len(sys.argv) < 4:
            print("Usage: python rag_system.py search <product> <query>")
            sys.exit(1)
        
        product = sys.argv[2]
        query = ' '.join(sys.argv[3:])
        
        results = rag.search(query, product, top_k=5)
        
        print(f"\n{'='*70}")
        print("SEARCH RESULTS")
        print(f"{'='*70}")
        
        for result in results:
            print(f"\n[{result['rank']}] {result['filepath']}")
            print(f"Similarity: {result['similarity']:.3f}")
            print(f"\n{result['content'][:500]}...")
            print(f"\n{'-'*70}")

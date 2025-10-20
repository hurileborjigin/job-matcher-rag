"""Retrieve relevant jobs from vector store."""
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.vectorstore.chroma_manager import ChromaManager
from src.embeddings.job_embedder import JobEmbedder


class JobRetriever:
    """Retrieve relevant jobs based on queries."""
    
    def __init__(self):
        """Initialize retriever with embedder and vector store."""
        self.embedder = JobEmbedder()
        self.chroma = ChromaManager()
        self.chroma.create_collection()
        
        print("✅ Job Retriever initialized")
    
    def search_jobs(
        self,
        query: str,
        n_results: int = 10,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for jobs matching the query.
        
        Args:
            query: Search query (e.g., "Python developer in Berlin")
            n_results: Number of results to return
            location: Filter by location (optional)
            job_type: Filter by job type (optional)
            category: Filter by category (optional)
        
        Returns:
            List of matching jobs with metadata and relevance scores
        """
        # Create query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Build filters
        filter_dict = {}
        if location:
            filter_dict['location'] = location
        if job_type:
            filter_dict['job_type'] = job_type
        if category:
            filter_dict['category'] = category
        
        # Search vector store
        results = self.chroma.search(
            query_embedding=query_embedding.tolist(),
            n_results=n_results,
            filter_dict=filter_dict if filter_dict else None
        )
        
        # Format results
        jobs = []
        if results['ids'] and len(results['ids']) > 0:
            for i, job_id in enumerate(results['ids'][0]):
                # ChromaDB returns cosine distance, convert to similarity score
                # Cosine distance range: [0, 2], where 0 = identical
                # Convert to similarity: 1 - (distance / 2) gives range [0, 1]
                distance = results['distances'][0][i]
                similarity_score = max(0, 1 - (distance / 2))  # Ensure non-negative
                
                job = {
                    'id': job_id,
                    'title': results['metadatas'][0][i].get('title', 'N/A'),
                    'company': results['metadatas'][0][i].get('company', 'N/A'),
                    'location': results['metadatas'][0][i].get('location', 'N/A'),
                    'job_type': results['metadatas'][0][i].get('job_type', 'N/A'),
                    'category': results['metadatas'][0][i].get('category', 'N/A'),
                    'url': results['metadatas'][0][i].get('url', ''),
                    'relevance_score': similarity_score,
                    'distance': distance,  # Keep original distance for debugging
                }
                jobs.append(job)
        
        return jobs

    def get_job_context(self, jobs: List[Dict]) -> str:
        """
        Format jobs into context string for LLM.
        
        Args:
            jobs: List of job dictionaries
        
        Returns:
            Formatted context string
        """
        if not jobs:
            return "No matching jobs found."
        
        context_parts = []
        for i, job in enumerate(jobs, 1):
            job_text = f"""
Job {i}:
- Title: {job['title']}
- Company: {job['company']}
- Location: {job['location']}
- Type: {job['job_type']}
- Category: {job['category']}
- URL: {job['url']}
- Relevance Score: {job['relevance_score']:.2%}
"""
            context_parts.append(job_text.strip())
        
        return "\n\n".join(context_parts)
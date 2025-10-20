"""
Job Retriever - Semantic search over job postings using ChromaDB
"""
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


class JobRetriever:
    """Retrieve relevant jobs using semantic search."""
    
    def __init__(
        self,
        collection_name: str = "jobs",
        persist_directory: str = "./data/chroma_db"
    ):
        """
        Initialize the job retriever.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory where ChromaDB data is stored
        """
        # Initialize Azure OpenAI for embeddings
        self.embedding_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        self.embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        
        print(f"✅ Using Azure OpenAI embeddings: {self.embedding_model}")
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Try to get collection, if it doesn't exist, show helpful error
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"✅ Collection ready: {collection_name}")
            print(f"✅ Job Retriever initialized")
        except Exception as e:
            print(f"❌ Collection '{collection_name}' not found!")
            print(f"💡 Please run: python scripts/build_vectorstore.py")
            raise ValueError(
                f"ChromaDB collection '{collection_name}' does not exist. "
                f"Please build the vector store first by running: "
                f"python scripts/build_vectorstore.py"
            )
    

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text using Azure OpenAI.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        response = self.embedding_client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return response.data[0].embedding
    
    def retrieve_jobs(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Retrieve relevant jobs based on a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of job dictionaries with relevance scores
        """
        # Generate query embedding
        query_embedding = self._get_embedding(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict,
            include=["metadatas", "documents", "distances"]
        )
        
        # Format results
        jobs = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            # Get all distances to normalize them
            distances = results['distances'][0]
            
            # Normalize distances to 0-100% relevance score
            # ChromaDB uses cosine distance (0 = identical, 2 = opposite)
            # Convert to similarity: similarity = 1 - (distance / 2)
            # Then convert to percentage
            
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                distance = distances[i]
                
                # Convert cosine distance to similarity score (0-100%)
                # Cosine distance ranges from 0 (identical) to 2 (opposite)
                # Similarity = (1 - distance/2) * 100
                similarity = max(0, min(100, (1 - distance / 2) * 100))
                
                job = {
                    'id': metadata.get('job_id'),
                    'title': metadata.get('title'),
                    'company': metadata.get('company', 'Unknown'),
                    'location': metadata.get('location', 'Unknown'),
                    'job_type': metadata.get('job_type'),
                    'category': metadata.get('category'),
                    'url': metadata.get('url'),
                    'description': metadata.get('description'),
                    'requirements': metadata.get('requirements'),
                    'posted_date': metadata.get('posted_date'),
                    'relevance_score': similarity,
                    'distance': distance
                }
                
                jobs.append(job)
        
        return jobs

    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the job collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            return {
                'total_jobs': count,
                'vectors_count': count,
                'collection_name': self.collection.name
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {
                'total_jobs': 0,
                'vectors_count': 0,
                'collection_name': self.collection.name
            }
    
    def search_by_filters(
        self,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        category: Optional[str] = None,
        company: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search jobs by metadata filters.
        
        Args:
            location: Filter by location
            job_type: Filter by job type (e.g., "Vollzeit", "Teilzeit")
            category: Filter by category
            company: Filter by company name
            top_k: Maximum number of results
            
        Returns:
            List of matching jobs
        """
        # Build filter dictionary
        where_filter = {}
        
        if location:
            where_filter['location'] = {'$contains': location}
        
        if job_type:
            where_filter['job_type'] = job_type
        
        if category:
            where_filter['category'] = category
        
        if company:
            where_filter['company'] = {'$contains': company}
        
        # If no filters, return empty
        if not where_filter:
            return []
        
        # Query with filters only (no semantic search)
        results = self.collection.get(
            where=where_filter,
            limit=top_k,
            include=["metadatas"]
        )
        
        # Format results
        jobs = []
        
        if results['ids']:
            for i, metadata in enumerate(results['metadatas']):
                job = {
                    'id': metadata.get('job_id'),
                    'title': metadata.get('title'),
                    'company': metadata.get('company'),
                    'location': metadata.get('location'),
                    'job_type': metadata.get('job_type'),
                    'category': metadata.get('category'),
                    'url': metadata.get('url'),
                    'description': metadata.get('description'),
                    'requirements': metadata.get('requirements'),
                    'posted_date': metadata.get('posted_date'),
                    'relevance_score': 100.0  # No semantic search, so all equally relevant
                }
                
                jobs.append(job)
        
        return jobs
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """
        Retrieve a specific job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job dictionary or None
        """
        results = self.collection.get(
            where={'job_id': job_id},
            include=["metadatas"]
        )
        
        if results['ids'] and len(results['ids']) > 0:
            metadata = results['metadatas'][0]
            
            return {
                'id': metadata.get('job_id'),
                'title': metadata.get('title'),
                'company': metadata.get('company'),
                'location': metadata.get('location'),
                'job_type': metadata.get('job_type'),
                'category': metadata.get('category'),
                'url': metadata.get('url'),
                'description': metadata.get('description'),
                'requirements': metadata.get('requirements'),
                'posted_date': metadata.get('posted_date')
            }
        
        return None
    
    def get_all_categories(self) -> List[str]:
        """Get all unique job categories."""
        # This is a workaround since ChromaDB doesn't have a direct way to get unique values
        # We'll query all jobs and extract unique categories
        results = self.collection.get(
            include=["metadatas"],
            limit=10000  # Adjust based on your dataset size
        )
        
        categories = set()
        for metadata in results['metadatas']:
            if metadata.get('category'):
                categories.add(metadata['category'])
        
        return sorted(list(categories))
    
    def get_all_locations(self) -> List[str]:
        """Get all unique job locations."""
        results = self.collection.get(
            include=["metadatas"],
            limit=10000
        )
        
        locations = set()
        for metadata in results['metadatas']:
            if metadata.get('location'):
                locations.add(metadata['location'])
        
        return sorted(list(locations))
    
    def get_all_companies(self) -> List[str]:
        """Get all unique companies."""
        results = self.collection.get(
            include=["metadatas"],
            limit=10000
        )
        
        companies = set()
        for metadata in results['metadatas']:
            if metadata.get('company'):
                companies.add(metadata['company'])
        
        return sorted(list(companies))
    
    def get_job_context(self, jobs: List[Dict]) -> str:
        """
        Format jobs into a context string for the generator.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Formatted context string
        """
        if not jobs:
            return "No jobs found."
        
        context_parts = []
        
        for i, job in enumerate(jobs, 1):
            context = f"""
    Job {i}:
    - Title: {job['title']}
    - Company: {job['company']}
    - Location: {job['location']}
    - Type: {job.get('job_type', 'N/A')}
    - Category: {job.get('category', 'N/A')}
    - Relevance: {job.get('relevance_score', 0):.1f}%
    - Description: {job.get('description', 'N/A')[:200]}...
    - Requirements: {job.get('requirements', 'N/A')[:200]}...
    - URL: {job['url']}
    """
            context_parts.append(context.strip())
        
        return "\n\n".join(context_parts)
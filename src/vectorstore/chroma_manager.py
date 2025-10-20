"""Manage ChromaDB vector store for jobs."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
from pathlib import Path


class ChromaManager:
    """Manage job embeddings in ChromaDB."""
    
    def __init__(self, persist_directory: str = "data/vector_store"):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Directory to store vector database
        """
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection_name = "jobs"
        self.collection = None
    
    def create_collection(self, reset: bool = False):
        """
        Create or get collection.
        
        Args:
            reset: If True, delete existing collection
        """
        if reset:
            try:
                self.client.delete_collection(self.collection_name)
                print(f"🗑️  Deleted existing collection: {self.collection_name}")
            except:
                pass
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "IT/CS job listings from it-cs.io"}
        )
        print(f"✅ Collection ready: {self.collection_name}")
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean metadata by removing None values and converting to valid types.
        
        Args:
            metadata: Raw metadata dictionary
        
        Returns:
            Cleaned metadata dictionary
        """
        cleaned = {}
        for key, value in metadata.items():
            if value is None:
                cleaned[key] = ""  # Replace None with empty string
            elif isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            else:
                cleaned[key] = str(value)  # Convert other types to string
        return cleaned
    
    def add_jobs(self, jobs: List[Dict], embeddings: List[List[float]]):
        """
        Add jobs to vector store.
        
        Args:
            jobs: List of job dictionaries
            embeddings: List of embedding vectors
        """
        if not self.collection:
            self.create_collection()
        
        # Prepare data
        ids = [str(job['id']) for job in jobs]
        documents = [job.get('title', 'No title') or 'No title' for job in jobs]
        
        # Clean metadata - remove None values
        metadatas = []
        for job in jobs:
            metadata = {
                'title': job.get('title') or 'N/A',
                'company': job.get('company') or 'N/A',
                'location': job.get('location') or 'N/A',
                'job_type': job.get('job_type') or 'N/A',
                'url': job.get('url') or '',
                'category': job.get('category') or 'N/A',
            }
            # Additional cleaning
            cleaned_metadata = self._clean_metadata(metadata)
            metadatas.append(cleaned_metadata)
        
        # Add to collection in batches (ChromaDB has limits)
        batch_size = 100
        for i in range(0, len(jobs), batch_size):
            end_idx = min(i + batch_size, len(jobs))
            
            self.collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
            
            print(f"  Added batch {i//batch_size + 1}/{(len(jobs)-1)//batch_size + 1}")
        
        print(f"✅ Added {len(jobs)} jobs to vector store")
    
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        filter_dict: Optional[Dict] = None
    ) -> Dict:
        """
        Search for similar jobs.
        
        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            filter_dict: Metadata filters (e.g., {'location': 'Berlin'})
        
        Returns:
            Search results with jobs and distances
        """
        if not self.collection:
            self.create_collection()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict
        )
        
        return results
    
    def get_stats(self) -> Dict:
        """Get collection statistics."""
        if not self.collection:
            return {"count": 0}
        
        return {
            "count": self.collection.count(),
            "name": self.collection_name
        }
"""ChromaDB Manager for storing and retrieving job embeddings."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import numpy as np


class ChromaManager:
    """Manage ChromaDB operations for job vectors."""
    
    def __init__(
        self,
        collection_name: str = "jobs",
        persist_directory: str = "./data/chroma_db"
    ):
        """
        Initialize ChromaDB manager.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection = None
        print(f"✅ ChromaDB initialized at: {persist_directory}")
    
    def create_collection(self, reset: bool = False):
        """
        Create or get collection.
        
        Args:
            reset: If True, delete existing collection and create new one
        """
        if reset:
            try:
                self.client.delete_collection(name=self.collection_name)
                print(f"🗑️  Deleted existing collection: {self.collection_name}")
            except Exception as e:
                print(f"ℹ️  No existing collection to delete: {e}")
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Job postings with embeddings"}
        )
        print(f"✅ Collection ready: {self.collection_name}")
    
    def add_jobs(self, jobs: List[Dict], embeddings: List[List[float]]):
        """
        Add jobs with embeddings to collection.
        
        Args:
            jobs: List of job dictionaries
            embeddings: List of embedding vectors
        """
        if self.collection is None:
            raise ValueError("Collection not initialized. Call create_collection() first.")
        
        if len(jobs) != len(embeddings):
            raise ValueError(f"Jobs ({len(jobs)}) and embeddings ({len(embeddings)}) count mismatch")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embedding_list = []
        
        for i, job in enumerate(jobs):
            # Create unique ID
            job_id = str(job.get('id', i))
            ids.append(f"job_{job_id}")
            
            # Create document text (for reference)
            doc_text = f"{job.get('title', '')} {job.get('company', '')} {job.get('description', '')}"
            documents.append(doc_text[:1000])  # Limit length
            
            # Create metadata
            metadata = {
                'job_id': int(job.get('id', i)),
                'title': str(job.get('title', 'Unknown'))[:500],
                'company': str(job.get('company', 'Unknown'))[:200],
                'location': str(job.get('location', 'Unknown'))[:200],
                'job_type': str(job.get('job_type', 'Unknown'))[:100],
                'category': str(job.get('category', 'Unknown'))[:200],
                'url': str(job.get('url', ''))[:500],
                'description': str(job.get('description', ''))[:1000],
                'requirements': str(job.get('requirements', ''))[:1000],
                'posted_date': str(job.get('posted_date', 'Unknown'))[:50]
            }
            metadatas.append(metadata)
            
            # Add embedding
            embedding_list.append(embeddings[i])
        
        # Add to collection in batches
        batch_size = 100
        total_batches = (len(ids) + batch_size - 1) // batch_size
        
        for i in range(0, len(ids), batch_size):
            batch_num = i // batch_size + 1
            end_idx = min(i + batch_size, len(ids))
            
            print(f"📦 Adding batch {batch_num}/{total_batches} ({end_idx - i} jobs)...")
            
            self.collection.add(
                ids=ids[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
                embeddings=embedding_list[i:end_idx]
            )
        
        print(f"✅ Added {len(ids)} jobs to collection")
    
    def get_stats(self) -> Dict:
        """
        Get collection statistics.
        
        Returns:
            Dictionary with stats
        """
        if self.collection is None:
            return {'count': 0, 'name': self.collection_name}
        
        count = self.collection.count()
        
        return {
            'count': count,
            'name': self.collection_name,
            'persist_directory': self.persist_directory
        }
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the collection.
        
        Args:
            query_embeddings: Query embedding vectors
            n_results: Number of results to return
            where: Optional metadata filters
        
        Returns:
            Query results
        """
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            include=["metadatas", "documents", "distances"]
        )
"""Job Embedder - Create embeddings for job postings."""
from typing import List, Dict
import numpy as np
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


class JobEmbedder:
    """Create embeddings for job postings using Azure OpenAI."""
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        self.embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        print(f"✅ JobEmbedder initialized with model: {self.embedding_model}")
    
    def create_job_text(self, job: Dict) -> str:
        """
        Create a text representation of a job for embedding.
        
        Args:
            job: Job dictionary
        
        Returns:
            Formatted text string
        """
        parts = []
        
        # Title
        if job.get('title'):
            parts.append(f"Job Title: {job['title']}")
        
        # Company
        if job.get('company'):
            parts.append(f"Company: {job['company']}")
        
        # Location
        if job.get('location'):
            parts.append(f"Location: {job['location']}")
        
        # Job Type
        if job.get('job_type'):
            parts.append(f"Type: {job['job_type']}")
        
        # Category
        if job.get('category'):
            parts.append(f"Category: {job['category']}")
        
        # Description
        if job.get('description'):
            desc = job['description'][:500]  # Limit length
            parts.append(f"Description: {desc}")
        
        # Requirements
        if job.get('requirements'):
            req = job['requirements'][:500]  # Limit length
            parts.append(f"Requirements: {req}")
        
        return " | ".join(parts)
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return response.data[0].embedding
    
    def embed_jobs(self, jobs: List[Dict], batch_size: int = 100) -> np.ndarray:
        """
        Create embeddings for multiple jobs.
        
        Args:
            jobs: List of job dictionaries
            batch_size: Number of jobs to process at once
        
        Returns:
            NumPy array of embeddings
        """
        all_embeddings = []
        total_batches = (len(jobs) + batch_size - 1) // batch_size
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} jobs)...")
            
            # Create texts for batch
            texts = [self.create_job_text(job) for job in batch]
            
            # Get embeddings for batch
            response = self.client.embeddings.create(
                input=texts,
                model=self.embedding_model
            )
            
            # Extract embeddings
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        print(f"✅ Created embeddings for {len(all_embeddings)} jobs")
        return np.array(all_embeddings)
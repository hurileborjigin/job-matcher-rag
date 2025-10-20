"""Create embeddings for job listings using Azure OpenAI."""
from typing import List, Dict
import numpy as np
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


class JobEmbedder:
    """Create embeddings for job listings using Azure OpenAI."""
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        # Load Azure OpenAI credentials
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        
        if not all([api_key, endpoint, deployment]):
            raise ValueError(
                "Missing Azure OpenAI configuration. Please check .env file.\n"
                "Required: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
            )
        
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        self.deployment = deployment
        print(f"✅ Using Azure OpenAI embeddings: {deployment}")
    
    def create_job_text(self, job: Dict) -> str:
        """
        Create searchable text from job data.
        
        Args:
            job: Job dictionary with title, location, description, etc.
        
        Returns:
            Combined text for embedding
        """
        parts = []
        
        # Title (most important)
        if job.get('title'):
            parts.append(f"Title: {job['title']}")
        
        # Company
        if job.get('company'):
            parts.append(f"Company: {job['company']}")
        
        # Location
        if job.get('location'):
            parts.append(f"Location: {job['location']}")
        
        # Job type
        if job.get('job_type'):
            parts.append(f"Type: {job['job_type']}")
        
        # Category
        if job.get('category'):
            parts.append(f"Category: {job['category']}")
        
        # Description (if available)
        if job.get('description'):
            parts.append(f"Description: {job['description'][:500]}")
        
        # Requirements (if available)
        if job.get('requirements'):
            parts.append(f"Requirements: {job['requirements'][:500]}")
        
        return " | ".join(parts)
    
    def embed_jobs(self, jobs: List[Dict]) -> np.ndarray:
        """
        Create embeddings for multiple jobs.
        
        Args:
            jobs: List of job dictionaries
        
        Returns:
            Numpy array of embeddings
        """
        texts = [self.create_job_text(job) for job in jobs]
        
        print(f"Creating embeddings for {len(texts)} jobs using Azure OpenAI...")
        
        # Azure OpenAI has a limit on batch size, process in chunks
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"  Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}...")
            
            response = self.client.embeddings.create(
                input=batch,
                model=self.deployment
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        print(f"✅ Created {len(all_embeddings)} embeddings")
        return np.array(all_embeddings)
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Create embedding for search query.
        
        Args:
            query: Search query text
        
        Returns:
            Query embedding as numpy array
        """
        response = self.client.embeddings.create(
            input=[query],
            model=self.deployment
        )
        return np.array(response.data[0].embedding)
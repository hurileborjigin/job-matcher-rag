"""Generate responses using Azure OpenAI with retrieved job context."""
from typing import List, Dict, Optional
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


class JobResponseGenerator:
    """Generate natural language responses about jobs using Azure OpenAI."""
    
    def __init__(self):
        """Initialize Azure OpenAI client for chat completion."""
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        
        if not all([api_key, endpoint]):
            raise ValueError(
                "Missing Azure OpenAI configuration. Please check .env file."
            )
        
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        self.deployment = deployment
        print(f"✅ Using Azure OpenAI chat: {deployment}")
    
    def generate_response(
        self,
        query: str,
        jobs: List[Dict],
        job_context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a response based on the query and retrieved jobs.
        
        Args:
            query: User's question/query
            jobs: List of retrieved jobs
            job_context: Formatted context string with job details
            conversation_history: Previous conversation messages (optional)
        
        Returns:
            Generated response text
        """
        # System prompt
        system_prompt = """You are a helpful job search assistant. Your role is to help users find relevant IT/CS jobs from the it-cs.io platform.

When answering:
1. Be concise and helpful
2. Highlight the most relevant jobs based on the user's query
3. Mention key details like company, location, and job type
4. Provide direct links to job postings
5. If no jobs match well, suggest broadening the search criteria

Always base your answers on the provided job listings. Don't make up information."""

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current query with context
        user_message = f"""User Query: {query}

Retrieved Jobs:
{job_context}

Please provide a helpful response based on these job listings."""
        
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content
    
    def generate_job_summary(self, jobs: List[Dict]) -> str:
        """
        Generate a summary of the retrieved jobs.
        
        Args:
            jobs: List of job dictionaries
        
        Returns:
            Summary text
        """
        if not jobs:
            return "No jobs found matching your criteria."
        
        job_context = "\n\n".join([
            f"- {job['title']} at {job['company']} ({job['location']}) - {job['url']}"
            for job in jobs[:5]  # Top 5 jobs
        ])
        
        messages = [
            {
                "role": "system",
                "content": "You are a job search assistant. Summarize the following jobs concisely."
            },
            {
                "role": "user",
                "content": f"Summarize these job opportunities:\n\n{job_context}"
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=0.5,
            max_tokens=300
        )
        
        return response.choices[0].message.content
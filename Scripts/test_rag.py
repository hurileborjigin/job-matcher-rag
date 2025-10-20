"""Test the RAG system with sample queries."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.retriever import JobRetriever
from src.rag.generator import JobResponseGenerator


def test_rag_system():
    """Test the complete RAG pipeline."""
    print("=" * 70)
    print("Testing Job Matcher RAG System")
    print("=" * 70)
    
    # Initialize components
    print("\n🔧 Initializing RAG components...")
    retriever = JobRetriever()
    generator = JobResponseGenerator()
    
    # Test queries
    test_queries = [
        "Python developer jobs in Berlin",
        "Remote frontend developer positions",
        "Machine learning engineer roles",
        "Full-stack developer with React experience",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test Query {i}: {query}")
        print('='*70)
        
        # Retrieve relevant jobs
        print("\n🔍 Retrieving relevant jobs...")
        jobs = retriever.search_jobs(query, n_results=5)
        
        print(f"✅ Found {len(jobs)} relevant jobs")
        
        # Display top jobs
        print("\n📋 Top matching jobs:")
        for j, job in enumerate(jobs[:3], 1):
            print(f"\n{j}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Relevance: {job['relevance_score']:.2%}")
            print(f"   URL: {job['url']}")
        
        # Generate response
        print("\n🤖 Generating AI response...")
        job_context = retriever.get_job_context(jobs)
        response = generator.generate_response(query, jobs, job_context)
        
        print("\n💬 AI Response:")
        print("-" * 70)
        print(response)
        print("-" * 70)
    
    print("\n" + "=" * 70)
    print("✅ RAG System Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_rag_system()
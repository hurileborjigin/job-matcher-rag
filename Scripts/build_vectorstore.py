"""Build vector store from jobs database."""
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.embeddings.job_embedder import JobEmbedder
from src.vectorstore.chroma_manager import ChromaManager


def load_jobs_from_db(db_path: str):
    """Load all jobs from SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM jobs")
    jobs = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jobs


def main():
    """Build vector store from jobs."""
    print("=" * 70)
    print("Building Vector Store for Job Matching")
    print("=" * 70)
    
    # Load jobs
    print("\n📂 Loading jobs from database...")
    db_path = Path(__file__).parent.parent / "data" / "jobs.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("💡 Please make sure jobs.db exists in the data/ folder")
        return
    
    jobs = load_jobs_from_db(str(db_path))
    print(f"✅ Loaded {len(jobs)} jobs")
    
    if len(jobs) == 0:
        print("❌ No jobs found in database!")
        return
    
    # Create embeddings
    print("\n🤖 Creating embeddings...")
    embedder = JobEmbedder()
    embeddings = embedder.embed_jobs(jobs)
    print(f"✅ Created {len(embeddings)} embeddings")
    
    # Store in ChromaDB
    print("\n💾 Storing in vector database...")
    chroma = ChromaManager()
    chroma.create_collection(reset=True)
    chroma.add_jobs(jobs, embeddings.tolist())
    
    # Show stats
    stats = chroma.get_stats()
    print(f"\n✅ Vector store built successfully!")
    print(f"   Total jobs indexed: {stats['count']}")
    print(f"   Collection name: {stats.get('name', 'jobs')}")
    print("=" * 70)
    
    # Verify the collection
    print("\n🔍 Verifying collection...")
    from src.rag.retriever import JobRetriever
    try:
        retriever = JobRetriever()
        verify_stats = retriever.get_collection_stats()
        print(f"✅ Verification successful!")
        print(f"   Jobs in collection: {verify_stats['total_jobs']}")
        print(f"   Vectors count: {verify_stats['vectors_count']}")
    except Exception as e:
        print(f"⚠️  Warning during verification: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 You can now run: streamlit run app.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
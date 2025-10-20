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
    jobs = load_jobs_from_db("data/jobs.db")
    print(f"✅ Loaded {len(jobs)} jobs")
    
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
    print("=" * 70)


if __name__ == "__main__":
    main()
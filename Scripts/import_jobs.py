"""Import jobs from itcs-job-matcher database."""
import sys
import sqlite3
from pathlib import Path
import shutil

def import_jobs(source_db: str, dest_db: str):
    """Copy jobs database from itcs-job-matcher."""
    source_path = Path(source_db)
    dest_path = Path(dest_db)
    
    if not source_path.exists():
        print(f"❌ Source database not found: {source_db}")
        print(f"Please run the scraper first in itcs-job-matcher project")
        sys.exit(1)
    
    # Create data directory
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy database
    shutil.copy2(source_path, dest_path)
    
    # Verify
    conn = sqlite3.connect(dest_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"✅ Imported {count} jobs to {dest_db}")

if __name__ == "__main__":
    source = "../itcs-job-matcher/data/jobs.db"
    dest = "data/jobs.db"
    import_jobs(source, dest)
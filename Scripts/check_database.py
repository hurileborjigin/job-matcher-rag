"""Check database content and quality."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check_database():
    """Check database for data quality issues."""
    db_path = "data/jobs.db"
    
    print("=" * 70)
    print("Database Quality Check")
    print("=" * 70)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total jobs
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total jobs: {total}")
    
    # Check for NULL/empty companies
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE company IS NULL OR company = ''")
    null_companies = cursor.fetchone()[0]
    print(f"⚠️  Jobs with missing company: {null_companies} ({null_companies/total*100:.1f}%)")
    
    # Check for NULL/empty locations
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE location IS NULL OR location = ''")
    null_locations = cursor.fetchone()[0]
    print(f"⚠️  Jobs with missing location: {null_locations} ({null_locations/total*100:.1f}%)")
    
    # Sample jobs with missing data
    print("\n📋 Sample jobs with missing company:")
    cursor.execute("""
        SELECT id, title, company, location, url 
        FROM jobs 
        WHERE company IS NULL OR company = ''
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"\nID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  Company: {row[2] or 'MISSING'}")
        print(f"  Location: {row[3] or 'MISSING'}")
        print(f"  URL: {row[4]}")
    
    # Check data distribution
    print("\n📊 Job Type Distribution:")
    cursor.execute("SELECT job_type, COUNT(*) FROM jobs GROUP BY job_type ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        print(f"  {row[0] or 'Unknown'}: {row[1]}")
    
    print("\n📊 Category Distribution:")
    cursor.execute("SELECT category, COUNT(*) FROM jobs GROUP BY category ORDER BY COUNT(*) DESC LIMIT 10")
    for row in cursor.fetchall():
        print(f"  {row[0] or 'Unknown'}: {row[1]}")
    
    conn.close()
    print("\n" + "=" * 70)


if __name__ == "__main__":
    check_database()
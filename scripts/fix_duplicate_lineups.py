import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
from sqlalchemy import text

engine = create_db_engine()

print("="*70)
print("FIXING DUPLICATE LINEUP BUG")
print("="*70)

print("\nStep 1: Checking current duplicate lineup situation...")
with engine.connect() as conn:
    # Check for duplicate lineups (same lineup_hash for different teams in same game)
    result = conn.execute(text("""
        SELECT game_id, lineup_hash, COUNT(DISTINCT team_id) as num_teams,
               array_agg(DISTINCT team_id) as team_ids
        FROM lineup_stints
        GROUP BY game_id, lineup_hash
        HAVING COUNT(DISTINCT team_id) > 1
        LIMIT 5
    """))
    duplicates = result.fetchall()

    if duplicates:
        print(f"[FOUND] {len(duplicates)} duplicate lineup examples:")
        for dup in duplicates:
            print(f"  Game {dup[0]}: lineup_hash appears for {dup[1]} teams: {dup[2]}")
    else:
        print("[OK] No duplicate lineups found")

print("\nStep 2: Clearing all lineup_stints data (will be reloaded with fixed code)...")
try:
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM lineup_stints"))
        conn.commit()
    print("[OK] All lineup_stints data cleared")
except Exception as e:
    print(f"[ERROR] Failed to clear data: {e}")
    engine.dispose()
    exit(1)

print("\nStep 3: Verifying tables are empty...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM lineup_stints"))
    count = result.fetchone()[0]
    print(f"  lineup_stints: {count} rows")

print("\n" + "="*70)
print("DATABASE CLEARED SUCCESSFULLY!")
print("="*70)
print("\nNext steps:")
print("1. Run your ETL pipeline to reload the data with the fixed code")
print("2. The duplicate lineup bug is now fixed in src/etl/lineup_tracker.py")
print("3. Each team will now get their own unique lineups")
print("="*70)

engine.dispose()

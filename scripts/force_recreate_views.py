import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
from sqlalchemy import text

engine = create_db_engine()

print("Step 1: Dropping all existing views...")
drop_statements = [
    "DROP VIEW IF EXISTS game_lineup_summary CASCADE",
    "DROP VIEW IF EXISTS player_impact_stats CASCADE",
    "DROP VIEW IF EXISTS lineup_aggregated_stats CASCADE",
    "DROP VIEW IF EXISTS lineup_stint_stats CASCADE"
]

try:
    with engine.connect() as conn:
        for stmt in drop_statements:
            print(f"  Executing: {stmt}")
            conn.execute(text(stmt))
        conn.commit()
    print("[OK] All views dropped successfully")
except Exception as e:
    print(f"[ERROR] Failed to drop views: {e}")
    engine.dispose()
    exit(1)

print("\nStep 2: Reading updated SQL file...")
try:
    with open('sql/views/lineup_performance.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    print(f"[OK] Read {len(sql_content)} characters from SQL file")
except Exception as e:
    print(f"[ERROR] Failed to read SQL file: {e}")
    engine.dispose()
    exit(1)

print("\nStep 3: Creating new views with fixed definitions...")
try:
    with engine.connect() as conn:
        conn.execute(text(sql_content))
        conn.commit()
    print("[OK] All views created successfully")
except Exception as e:
    print(f"[ERROR] Failed to create views: {e}")
    import traceback
    traceback.print_exc()
    engine.dispose()
    exit(1)

print("\nStep 4: Verifying the fix...")
try:
    result = conn.execute(text("SELECT pg_get_viewdef('lineup_stint_stats', true)"))
    view_def = result.fetchone()[0]

    if 'pbp.action_id >=' in view_def:
        print("[OK] View now uses action_id (FIX SUCCESSFUL!)")
    else:
        print("[WARNING] Could not verify fix")
except Exception as e:
    print(f"[ERROR] Verification failed: {e}")

engine.dispose()

print("\n" + "="*60)
print("DONE! Now run: python scripts/check_views.py")
print("You should see possessions of 10-30 per stint")
print("="*60)

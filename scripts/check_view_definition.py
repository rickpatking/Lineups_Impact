import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
import pandas as pd

engine = create_db_engine()

print("Checking if view was updated correctly...")
result = pd.read_sql("SELECT pg_get_viewdef('lineup_stint_stats', true)", engine)
view_def = result.iloc[0,0]

print("\nSearching for join condition in view definition:")
if 'pbp.action_id >=' in view_def and 'pbp.action_id <=' in view_def:
    print("[OK] View uses action_id for joins (CORRECT - view was updated!)")
elif 'pbp.seconds_into_game >=' in view_def:
    print("[ERROR] View still uses seconds_into_game (OLD - view NOT updated)")
    print("\nThe SQL file execution didn't update the view.")
    print("Try manually dropping and recreating the view.")
else:
    print("[UNKNOWN] Could not determine join condition")

print("\nView definition snippet:")
print(view_def[:600])
print("...")

engine.dispose()

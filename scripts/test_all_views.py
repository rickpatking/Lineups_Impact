import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
import pandas as pd

engine = create_db_engine()

print("Checking which views exist in database...")
views = pd.read_sql("SELECT table_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name", engine)
print("\nViews found:")
print(views)

print("\nTesting each view:")
for view_name in views['table_name']:
    try:
        count = pd.read_sql(f'SELECT COUNT(*) FROM {view_name}', engine)
        print(f"  {view_name}: OK ({count.iloc[0,0]} rows)")
    except Exception as e:
        print(f"  {view_name}: ERROR - {str(e)[:100]}")

engine.dispose()

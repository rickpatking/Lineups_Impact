import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
import pandas as pd

engine = create_db_engine()

print("=== Checking lineup_stint_stats view ===")
try:
    check = pd.read_sql('''
        SELECT stint_id, duration_secs, points_scored, points_allowed,
               possessions, offensive_rating, defensive_rating, net_rating
        FROM lineup_stint_stats
        WHERE possessions > 0
        LIMIT 10
    ''', engine)
    print(check)
    print(f"\nRows with NULL ratings: {check['offensive_rating'].isna().sum()}")
    print(f"Rows with valid ratings: {check['offensive_rating'].notna().sum()}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Checking lineup_aggregated_stats view ===")
try:
    agg = pd.read_sql('''
        SELECT lineup_hash, total_minutes, total_plus_minus,
               avg_offensive_rating, avg_defensive_rating, avg_net_rating
        FROM lineup_aggregated_stats
        WHERE total_minutes > 5
        ORDER BY total_minutes DESC
        LIMIT 10
    ''', engine)
    print(agg)
except Exception as e:
    print(f"Error: {e}")

engine.dispose()

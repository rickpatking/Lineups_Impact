import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
import pandas as pd

engine = create_db_engine()

print("Checking lineup names in database...\n")

result = pd.read_sql("""
SELECT
    las.lineup_hash,
    p1.player_name as player1,
    p2.player_name as player2,
    p3.player_name as player3,
    p4.player_name as player4,
    p5.player_name as player5
FROM lineup_aggregated_stats las
LEFT JOIN players p1 ON las.player1_id = p1.player_id
LEFT JOIN players p2 ON las.player2_id = p2.player_id
LEFT JOIN players p3 ON las.player3_id = p3.player_id
LEFT JOIN players p4 ON las.player4_id = p4.player_id
LEFT JOIN players p5 ON las.player5_id = p5.player_id
ORDER BY las.total_minutes DESC
LIMIT 15
""", engine)

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 30)

print("Top 15 lineups by minutes played:")
result.to_csv('logs/lineup_names_check.csv', index=False, encoding='utf-8')
print("Saved to logs/lineup_names_check.csv")
print(f"\nShowing first 5 rows:")
for idx, row in result.head(5).iterrows():
    print(f"{idx+1}. {row['lineup_hash'][:30]}...")

print("\n\nChecking for NULL player names...")
nulls = pd.read_sql("""
SELECT COUNT(*) as count
FROM lineup_aggregated_stats las
WHERE NOT EXISTS (SELECT 1 FROM players WHERE player_id = las.player1_id)
   OR NOT EXISTS (SELECT 1 FROM players WHERE player_id = las.player2_id)
   OR NOT EXISTS (SELECT 1 FROM players WHERE player_id = las.player3_id)
   OR NOT EXISTS (SELECT 1 FROM players WHERE player_id = las.player4_id)
   OR NOT EXISTS (SELECT 1 FROM players WHERE player_id = las.player5_id)
""", engine)

print(f"Lineups with missing player data: {nulls.iloc[0,0]}")

engine.dispose()

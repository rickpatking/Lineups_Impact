import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db_connection import create_db_engine
from nba_api.stats.endpoints import commonplayerinfo
import pandas as pd
import time

engine = create_db_engine()

print("="*70)
print("FINDING AND FIXING MISSING PLAYERS")
print("="*70)

# Find player IDs that are in lineups but not in players table
missing_query = """
SELECT DISTINCT player_id FROM (
    SELECT player1_id AS player_id FROM lineup_stints
    UNION SELECT player2_id FROM lineup_stints
    UNION SELECT player3_id FROM lineup_stints
    UNION SELECT player4_id FROM lineup_stints
    UNION SELECT player5_id FROM lineup_stints
) all_players
WHERE player_id NOT IN (SELECT player_id FROM players)
ORDER BY player_id
"""

missing_players = pd.read_sql(missing_query, engine)

if len(missing_players) == 0:
    print("\n[OK] No missing players found!")
    engine.dispose()
    exit(0)

print(f"\nFound {len(missing_players)} missing player IDs:")
print(missing_players)

print("\nFetching player info from NBA API...")

player_data = []
for player_id in missing_players['player_id']:
    try:
        print(f"  Fetching player {player_id}...", end=" ")
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        df = info.get_data_frames()[0]

        # Match the schema: player_id, player_name, position, height, weight
        player_info = {
            'player_id': player_id,
            'player_name': df['DISPLAY_FIRST_LAST'].iloc[0],
            'position': df['POSITION'].iloc[0] if 'POSITION' in df.columns and pd.notna(df['POSITION'].iloc[0]) else None,
            'height': df['HEIGHT'].iloc[0] if 'HEIGHT' in df.columns and pd.notna(df['HEIGHT'].iloc[0]) else None,
            'weight': int(df['WEIGHT'].iloc[0]) if 'WEIGHT' in df.columns and pd.notna(df['WEIGHT'].iloc[0]) else None
        }
        player_data.append(player_info)
        print(f"OK - {player_info['player_name']}")
        time.sleep(0.6)  # Rate limiting

    except Exception as e:
        print(f"ERROR - {e}")
        continue

if len(player_data) > 0:
    print(f"\nLoading {len(player_data)} players into database...")
    players_df = pd.DataFrame(player_data)
    players_df.to_sql('players', engine, if_exists='append', index=False)
    print("[OK] Players loaded successfully")

    print("\nLoaded players:")
    for p in player_data:
        print(f"  {p['player_id']}: {p['player_name']}")
else:
    print("\n[ERROR] Could not fetch any player data")

print("\n" + "="*70)
print("Now refresh your Power BI dashboard!")
print("The Lineup Display measure should show player names correctly.")
print("="*70)

engine.dispose()

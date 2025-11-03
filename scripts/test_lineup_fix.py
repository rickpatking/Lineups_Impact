import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.etl.lineup_tracker import get_lineups, get_stints, clean_data
from nba_api.stats.endpoints import playbyplayv3
import pandas as pd

# Test with the problematic game from earlier
game_id = '0042400407'
team1_id = 1610612754  # Indiana Pacers
team2_id = 1610612760  # Oklahoma City Thunder

print("="*70)
print("TESTING LINEUP TRACKER FIX")
print(f"Game: {game_id}")
print(f"Team 1: {team1_id} (Pacers)")
print(f"Team 2: {team2_id} (Thunder)")
print("="*70)

print("\nStep 1: Getting play-by-play data...")
pbp = playbyplayv3.PlayByPlayV3(game_id)
pbp_df = pbp.get_data_frames()[0]
clean_pbp = clean_data(pbp_df)
print(f"[OK] Got {len(clean_pbp)} play-by-play events")

print("\nStep 2: Getting lineups for Team 1 (Pacers)...")
team1_lineups = get_lineups(game_id, team1_id)
print(f"[OK] Found {len(team1_lineups)} lineups for Team 1")
print(f"  First lineup: {team1_lineups[0]['PLAYERS']}")

print("\nStep 3: Getting lineups for Team 2 (Thunder)...")
team2_lineups = get_lineups(game_id, team2_id)
print(f"[OK] Found {len(team2_lineups)} lineups for Team 2")
print(f"  First lineup: {team2_lineups[0]['PLAYERS']}")

print("\nStep 4: Checking for duplicates...")
team1_hashes = set('-'.join(str(p) for p in lineup['PLAYERS']) for lineup in team1_lineups)
team2_hashes = set('-'.join(str(p) for p in lineup['PLAYERS']) for lineup in team2_lineups)
duplicates = team1_hashes.intersection(team2_hashes)

if duplicates:
    print(f"[ERROR] Found {len(duplicates)} duplicate lineups between teams!")
    for dup in list(duplicates)[:3]:
        print(f"  {dup}")
else:
    print("[OK] No duplicate lineups found - FIX IS WORKING!")

print("\nStep 5: Generating stints for both teams...")
team1_stints = get_stints(clean_pbp, team1_lineups, team1_id)
team2_stints = get_stints(clean_pbp, team2_lineups, team2_id)
print(f"[OK] Team 1: {len(team1_stints)} stints")
print(f"[OK] Team 2: {len(team2_stints)} stints")

print("\nStep 6: Verifying stint data integrity...")
combined = pd.concat([team1_stints, team2_stints])
print(f"  Total stints: {len(combined)}")
print(f"  Unique team_ids: {combined['team_id'].unique()}")
print(f"  Unique lineup_hashes: {combined['lineup_hash'].nunique()}")

# Check if same lineup_hash appears for both teams
duplicates_in_stints = combined.groupby('lineup_hash')['team_id'].nunique()
duplicates_in_stints = duplicates_in_stints[duplicates_in_stints > 1]

if len(duplicates_in_stints) > 0:
    print(f"\n[ERROR] {len(duplicates_in_stints)} lineup_hashes appear for multiple teams!")
    print("  Examples:")
    for hash_val in duplicates_in_stints.index[:3]:
        teams = combined[combined['lineup_hash'] == hash_val]['team_id'].unique()
        print(f"    {hash_val}: teams {teams}")
else:
    print("\n[SUCCESS] Each lineup_hash belongs to exactly one team!")

print("\n" + "="*70)
if len(duplicates_in_stints) == 0:
    print("FIX VERIFIED - Ready to reload all data!")
else:
    print("FIX NOT WORKING - Further investigation needed")
print("="*70)

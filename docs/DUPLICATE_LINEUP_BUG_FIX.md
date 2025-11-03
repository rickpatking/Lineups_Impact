# Duplicate Lineup Bug - Root Cause and Fix

## Problem Summary

The `lineup_aggregated_stats` view showed that lineups had a maximum of 2 games played together, despite having ~872 games (half of the 2024-25 season) loaded into the database.

Investigation revealed that **the same lineup_hash was appearing for BOTH opposing teams** in the same game, with identical player IDs but different team_ids. This is physically impossible - the same 5 players cannot play for both teams simultaneously.

### Example of the Bug

```sql
-- Game 0042400407 had the same lineup for both teams:
Team 1610612754 (Pacers): lineup_hash '1631097-1630167-1641767-1628418-1642277'
Team 1610612760 (Thunder): lineup_hash '1631097-1630167-1641767-1628418-1642277'

-- Same players for different teams = DATA CORRUPTION
```

## Root Cause

The bug was in `src/etl/lineup_tracker.py` in the `get_lineups()` function (line 74-76):

```python
def get_lineups(game_id, team_id):
    rotation = gamerotation.GameRotation(game_id)
    rotation = rotation.get_data_frames()[0]  # ❌ ALWAYS GETS FIRST TEAM
```

**The Issue:**
1. The NBA API's `gamerotation.GameRotation(game_id)` returns **2 dataframes** - one for each team
2. The code was using `get_data_frames()[0]` which ALWAYS got the first team's rotation data
3. The `team_id` parameter was passed to the function but **never used**
4. When the pipeline looped through both teams, it processed the SAME rotation data twice:
   - First iteration: `team_id = 1610612754` → used `rotation_dfs[0]` (Pacers data) ✓
   - Second iteration: `team_id = 1610612760` → used `rotation_dfs[0]` (Pacers data again) ❌

5. Result: Both teams got the same lineups (Pacers players), but `get_stints()` assigned whatever team_id was passed in, creating duplicate entries with different team_ids but identical player lists

## The Fix

Changed `get_lineups()` to properly iterate through both rotation dataframes and select the correct one for the requested team:

```python
def get_lineups(game_id, team_id):
    rotation = gamerotation.GameRotation(game_id)
    rotation_dfs = rotation.get_data_frames()  # ✓ Get both dataframes

    # gamerotation returns 2 dataframes (one per team)
    # Find the dataframe for the requested team
    rotation = None
    for df in rotation_dfs:
        if team_id in df['TEAM_ID'].values:
            rotation = df.copy()
            break

    if rotation is None or len(rotation) == 0:
        raise ValueError(f"No rotation data found for team {team_id} in game {game_id}")

    # ... rest of function continues as before
```

## Verification

After the fix, testing on game 0042400407 shows:

```
Team 1 (Pacers 1610612754): 44 lineups
  First lineup: [1631097, 1630167, 1641767, 1628418, 1642277]

Team 2 (Thunder 1610612760): 43 lineups
  First lineup: [1631096, 1629026, 1631172, 1641794, 1642349]

✓ No duplicate lineups between teams!
✓ Each lineup_hash belongs to exactly one team
```

## Steps to Reload Data

Since the database has corrupted lineup_stints data, follow these steps:

### 1. Clear Corrupted Data
```bash
python scripts/fix_duplicate_lineups.py
```
This script:
- Shows examples of duplicate lineups
- Clears all data from lineup_stints table
- Keeps play_by_play, games, players, and teams intact

### 2. Reload Lineup Stints with Fixed Code
```bash
python scripts/reload_lineup_stints_only.py
```
This script:
- Gets all game_ids from the play_by_play table
- Regenerates lineup stints using the FIXED get_lineups() function
- Loads corrected data back into lineup_stints table
- Takes ~1-2 hours for 872 games due to NBA API rate limiting

### 3. Verify the Fix
```bash
python scripts/check_views.py
```
Check that:
- Lineup stints have reasonable statistics
- Lineups now show more than 2 games played together
- No duplicate lineup_hashes for different teams

### 4. Test Power BI
Open Power BI Desktop and refresh your data sources. You should now see:
- Correct lineup statistics
- Lineups with more than 2 games played together
- Proper team differentiation

## Impact

**Before Fix:**
- Same lineups duplicated for both teams
- `games_played` in `lineup_aggregated_stats` capped at 2
- Impossible to analyze real lineup performance
- Data corruption affected all 872 loaded games

**After Fix:**
- Each team has unique, correct lineups
- Lineups will show accurate games_played counts (5, 10, 20+ games for common lineups)
- Proper lineup performance analysis possible
- Foundation for loading remaining ~1300 games of the season

## Files Modified

1. `src/etl/lineup_tracker.py` - Fixed `get_lineups()` function to use correct team dataframe
2. `scripts/fix_duplicate_lineups.py` - NEW: Clears corrupted data
3. `scripts/reload_lineup_stints_only.py` - NEW: Reloads all lineup stints with fixed code
4. `scripts/test_lineup_fix.py` - NEW: Verification script

## Lessons Learned

1. Always verify NBA API return structure - `get_data_frames()` can return multiple dataframes
2. Function parameters should always be used (team_id was passed but ignored)
3. Data integrity checks are critical - duplicates went unnoticed until aggregation revealed the issue
4. Testing with multiple games helps catch systematic bugs

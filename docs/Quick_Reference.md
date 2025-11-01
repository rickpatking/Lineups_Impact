# Quick Reference: NBA Lineup Analysis Setup

## 📋 What We Built

### 1. Database Views (SQL)

Located in: `sql/views/lineup_performance.sql`

| View Name | Purpose | Key Metrics |
|-----------|---------|-------------|
| **lineup_stint_stats** | Individual stint performance | Points scored/allowed, plus/minus, offensive/defensive/net rating per stint |
| **lineup_aggregated_stats** | Overall lineup statistics | Total minutes, games played, average ratings across all games |
| **player_impact_stats** | Player on/off court impact | Individual player value, plus/minus per 48 min |
| **game_lineup_summary** | Game-specific lineup performance | Win/loss context, lineup performance by game |

### 2. Key Basketball Metrics Explained

**Net Rating**: The most important metric
- Formula: Offensive Rating - Defensive Rating
- Meaning: Point differential per 100 possessions
- Good value: +5.0 or higher
- Example: Net Rating of +10 = Team scores 10 more points than opponent per 100 possessions

**Offensive Rating**: Points scored per 100 possessions
- NBA average: ~110-115
- Elite: 120+

**Defensive Rating**: Points allowed per 100 possessions
- NBA average: ~110-115
- Elite: <105

**Plus/Minus**: Simple point differential while lineup is on court
- +15 = Team outscored opponent by 15 points with this lineup

**Plus/Minus per 48**: Impact standardized to full game
- Allows fair comparison between players with different minutes

---

## 🔌 Connecting Power BI

### Quick Steps:
1. Get Data → PostgreSQL database
2. Server: `localhost:5432`
3. Database: `nba_analysis`
4. Enter credentials from your `.env` file
5. Select: `teams`, `players`, `games`, and all 4 views
6. Load (don't transform)

### Essential DAX Measures:

```dax
Total Minutes = SUM(lineup_aggregated_stats[total_minutes])
Avg Net Rating = AVERAGE(lineup_aggregated_stats[avg_net_rating])
Total Plus Minus = SUM(lineup_aggregated_stats[total_plus_minus])
Win Percentage = DIVIDE(
    CALCULATE(COUNT(game_lineup_summary[game_id]),
              game_lineup_summary[game_result] = "W"),
    COUNT(game_lineup_summary[game_id]), 0) * 100
```

---

## 📊 Dashboard Ideas

### Dashboard 1: "Best Lineups"
**Question**: Which 5-man units are most effective?
- Table: Top lineups by net rating (min 10 minutes)
- Scatter: Offensive vs Defensive rating
- Bar chart: Plus/minus by lineup

### Dashboard 2: "Player Impact"
**Question**: Which players make the team better?
- Rankings table: Players by plus/minus per 48
- Bar chart: Top players by net rating
- Slicer: Filter by team/position

### Dashboard 3: "Winning Lineups"
**Question**: Which lineups are used in wins vs losses?
- Win/loss split comparison
- Lineups in close games
- Clutch performance

---

## 🗂️ Project Structure

```
Lineups_Impact/
├── sql/
│   ├── schema/
│   │   └── 01_create_tables.sql          # Database structure
│   └── views/
│       └── lineup_performance.sql         # Analysis views ⭐
├── src/
│   └── etl/
│       ├── pipeline.py                    # Main ETL script
│       ├── nba_data_extractor.py         # NBA API calls
│       ├── lineup_tracker.py             # Lineup tracking logic
│       └── database_loader.py            # Load data to DB
├── scripts/
│   ├── run_etl.py                        # Run the pipeline
│   └── create_views.py                   # Create SQL views
├── docs/
│   ├── PowerBI_Setup_Guide.md            # Full Power BI guide ⭐
│   └── Quick_Reference.md                # This file ⭐
└── .env                                   # Database credentials
```

---

## 🚀 Common Workflows

### Loading More Games
```bash
cd Lineups_Impact
python scripts/run_etl.py --season 2024-25
```
- Automatically skips already-loaded games
- Retries failed games
- Updates all views automatically

### Refreshing Power BI
1. Open your .pbix file
2. Click "Refresh" in Home ribbon
3. All visuals update with new games

### Querying Data Directly (PostgreSQL)
```sql
-- Best lineups (min 20 minutes)
SELECT
    lineup_hash,
    total_minutes,
    total_plus_minus,
    avg_net_rating
FROM lineup_aggregated_stats
WHERE total_minutes >= 20
ORDER BY avg_net_rating DESC
LIMIT 10;

-- Top players by impact
SELECT
    player_name,
    position,
    total_minutes,
    on_court_plus_minus,
    plus_minus_per_48min
FROM player_impact_stats
WHERE total_minutes >= 30
ORDER BY plus_minus_per_48min DESC;
```

---

## 📈 Current Data Status

Run this to check your data:
```python
from src.utils.db_connection import create_db_engine
import pandas as pd

engine = create_db_engine()
games = pd.read_sql('SELECT COUNT(*) FROM games', engine)
print(f"Games loaded: {games.iloc[0,0]}")

stints = pd.read_sql('SELECT COUNT(*) FROM lineup_stint_stats', engine)
print(f"Lineup stints: {stints.iloc[0,0]}")
```

As of now: **118 games loaded** out of 2196 total (2024-25 season)

---

## 🐛 Troubleshooting

### Views not showing data?
```sql
-- Test each view
SELECT COUNT(*) FROM lineup_stint_stats;
SELECT COUNT(*) FROM lineup_aggregated_stats;
SELECT COUNT(*) FROM player_impact_stats;
SELECT COUNT(*) FROM game_lineup_summary;
```

### Power BI connection failed?
1. Check PostgreSQL is running
2. Verify credentials in `.env`
3. Test connection: `python -c "from src.utils.db_connection import test_connection; test_connection()"`

### ETL pipeline errors?
- Check logs in `logs/etl_pipeline.log`
- Common: API timeouts (just retry)
- Common: Player IDs not found (expected, skips automatically)

---

## 💡 Pro Tips

1. **Filter for significance**: Always filter lineups by minimum minutes (10-20 min) to avoid small sample noise

2. **Context matters**: A lineup with +15 in 5 minutes is less meaningful than +15 in 30 minutes

3. **Normalize stats**: Use per-100-possession or per-48-minute metrics to compare fairly

4. **Win context**: Lineups look better in blowout wins. Filter for close games for true performance

5. **Sample size**: Wait until you have 50+ games loaded for more reliable insights

---

## 📚 Key Files to Know

| File | What It Does |
|------|--------------|
| `sql/views/lineup_performance.sql` | Creates all 4 analysis views |
| `docs/PowerBI_Setup_Guide.md` | Step-by-step Power BI tutorial |
| `scripts/run_etl.py` | Load games from NBA API |
| `.env` | Database connection settings |
| `logs/etl_pipeline.log` | ETL execution logs |

---

## 🎯 Next Steps

- [ ] Load remaining ~2000 games (run ETL multiple times)
- [ ] Connect Power BI and create first dashboard
- [ ] Experiment with different visualizations
- [ ] Add date/time dimensions for temporal analysis
- [ ] Calculate advanced metrics (True Shooting %, Usage Rate, etc.)
- [ ] Compare lineups across teams
- [ ] Build predictive models (which lineups win?)

---

**Need help?** Check the full PowerBI_Setup_Guide.md for detailed walkthroughs!

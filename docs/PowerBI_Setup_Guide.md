# Power BI Setup Guide for NBA Lineup Analysis

This guide walks you through connecting Power BI to your PostgreSQL database and creating impactful visualizations for lineup performance analysis.

---

## Part 1: Installing Power BI Desktop

1. **Download Power BI Desktop** (Free)
   - Go to: https://powerbi.microsoft.com/desktop/
   - Click "Download Free"
   - Install the application

2. **Install PostgreSQL Connector** (if not included)
   - Power BI Desktop usually includes PostgreSQL connector by default
   - If prompted, allow it to install the Npgsql data provider

---

## Part 2: Connecting to Your PostgreSQL Database

### Step 1: Open Power BI and Get Data

1. Open Power BI Desktop
2. Click **"Get Data"** on the Home ribbon
3. Search for "PostgreSQL" in the search box
4. Select **"PostgreSQL database"** and click **Connect**

### Step 2: Enter Connection Details

In the PostgreSQL database connection dialog:

```
Server: localhost:5432
Database: nba_analysis
```

Click **OK**

### Step 3: Authentication

1. Select **"Database"** authentication (left sidebar)
2. Enter your credentials:
   - **User name**: (your DB_USER from .env file)
   - **Password**: (your DB_PASSWORD from .env file)
3. Click **Connect**

### Step 4: Select Tables and Views

In the Navigator window, you'll see all your tables and views. **Select these items**:

**Core Tables** (check these):
- ✅ `teams`
- ✅ `players`
- ✅ `games`

**Analysis Views** (check these - these are the important ones!):
- ✅ `lineup_stint_stats` - Individual stint performance
- ✅ `lineup_aggregated_stats` - Overall lineup metrics
- ✅ `player_impact_stats` - Player on/off court impact
- ✅ `game_lineup_summary` - Lineup performance by game

**Optional** (only if you need raw data):
- `play_by_play` - Raw play-by-play events (large table, only load if needed)
- `lineup_stints` - Raw stint data (already aggregated in views)

After selecting, click **Load** (not Transform)

---

## Part 3: Understanding Your Data Model

### What Each View Contains

#### 1. **lineup_stint_stats**
Every row = one stint (continuous period with same 5 players on court)

**Key columns**:
- `lineup_hash` - Unique identifier for this 5-player combination
- `game_id` - Which game
- `team_id` - Which team
- `player1_id` through `player5_id` - The 5 players
- `duration_secs` - How long this stint lasted
- `points_scored` - Points this lineup scored
- `points_allowed` - Points opponent scored
- `plus_minus` - Point differential (+/-)
- `offensive_rating` - Points per 100 possessions (offense)
- `defensive_rating` - Points allowed per 100 possessions (defense)
- `net_rating` - Offensive rating - Defensive rating (MOST IMPORTANT METRIC)

**Use for**: Game-by-game lineup analysis, identifying when lineups work best

#### 2. **lineup_aggregated_stats**
Every row = one unique lineup across ALL games

**Key columns**:
- `lineup_hash` - Unique 5-player combination
- `games_played` - How many games this lineup played
- `total_minutes` - Total minutes together
- `total_plus_minus` - Cumulative point differential
- `avg_net_rating` - Average efficiency rating
- `avg_offensive_rating` - Average offensive efficiency
- `avg_defensive_rating` - Average defensive efficiency

**Use for**: "Best lineups" analysis, identifying which 5-man units work together

#### 3. **player_impact_stats**
Every row = one player's overall impact

**Key columns**:
- `player_name` - Player name
- `position` - Position
- `team_id` - Current team
- `total_minutes` - Minutes played
- `on_court_plus_minus` - Team performance with player ON court
- `avg_net_rating` - Average net rating when player is on court
- `plus_minus_per_48min` - Impact standardized to 48 minutes

**Use for**: Individual player value, MVP candidates, player comparisons

#### 4. **game_lineup_summary**
Every row = one lineup's performance in one specific game

**Key columns**:
- `game_id` - The game
- `lineup_hash` - The lineup
- `game_result` - 'W' or 'L'
- `minutes_played_in_game` - Minutes this lineup played
- `plus_minus_in_game` - Performance in this game

**Use for**: Win/loss analysis, which lineups perform in wins vs losses

---

## Part 4: Creating Relationships

After loading data, Power BI should auto-detect relationships. Verify these exist:

### In the Model View (left sidebar, third icon):

1. **teams** to **lineup_aggregated_stats**
   - `teams[team_id]` → `lineup_aggregated_stats[team_id]`

2. **teams** to **player_impact_stats**
   - `teams[team_id]` → `player_impact_stats[team_id]`

3. **players** to **lineup_stint_stats** (create 5 relationships):
   - `players[player_id]` → `lineup_stint_stats[player1_id]`
   - `players[player_id]` → `lineup_stint_stats[player2_id]`
   - ... etc for player3, player4, player5

   **Note**: Mark these relationships as "inactive" except for player1_id. You'll use DAX to activate them when needed.

4. **players** to **player_impact_stats**
   - `players[player_id]` → `player_impact_stats[player_id]`

5. **games** to **game_lineup_summary**
   - `games[game_id]` → `game_lineup_summary[game_id]`

---

## Part 5: Creating DAX Measures

Click on **"New Measure"** in the Home ribbon and create these calculated measures:

### Basic Measures

```dax
// Total Minutes Played
Total Minutes = SUM(lineup_aggregated_stats[total_minutes])

// Average Net Rating
Avg Net Rating = AVERAGE(lineup_aggregated_stats[avg_net_rating])

// Total Plus Minus
Total Plus Minus = SUM(lineup_aggregated_stats[total_plus_minus])

// Games Played
Games Played = SUM(lineup_aggregated_stats[games_played])
```

### Advanced Measures

```dax
// Net Rating (Color-coded: Green if positive, Red if negative)
Net Rating Color =
VAR NetRating = AVERAGE(lineup_aggregated_stats[avg_net_rating])
RETURN
    IF(NetRating > 0, "Positive", "Negative")

// Win Percentage
Win Percentage =
DIVIDE(
    CALCULATE(COUNT(game_lineup_summary[game_id]), game_lineup_summary[game_result] = "W"),
    COUNT(game_lineup_summary[game_id]),
    0
) * 100

// Offensive Efficiency Rating
Offensive Rating = AVERAGE(lineup_aggregated_stats[avg_offensive_rating])

// Defensive Efficiency Rating
Defensive Rating = AVERAGE(lineup_aggregated_stats[avg_defensive_rating])

// Minutes Filter (only show lineups with significant minutes)
Qualified Lineups =
VAR MinMinutes = 10
RETURN
    IF(SUM(lineup_aggregated_stats[total_minutes]) >= MinMinutes, 1, 0)
```

### Player-Specific Measures

```dax
// Player Impact (Plus/Minus per 48 minutes)
Player Impact per 48 = AVERAGE(player_impact_stats[plus_minus_per_48min])

// Player On-Court Net Rating
Player Net Rating = AVERAGE(player_impact_stats[avg_net_rating])

// Player Minutes
Player Total Minutes = SUM(player_impact_stats[total_minutes])
```

---

## Part 6: Building Your First Dashboard

### Dashboard 1: "Best Performing Lineups"

**Page Layout**:

1. **Card Visuals** (Top row)
   - Total Lineups Used
   - Average Net Rating
   - Total Games Analyzed

2. **Table Visual** - "Top 10 Lineups by Net Rating"
   - Columns:
     - Player 1, 2, 3, 4, 5 (from players table via relationships)
     - Total Minutes
     - Games Played
     - Avg Net Rating
     - Total Plus Minus
   - Sort by: Avg Net Rating (descending)
   - Filter: Total Minutes >= 10 (to exclude small sample sizes)

3. **Scatter Plot** - "Offensive vs Defensive Rating"
   - X-axis: Avg Offensive Rating
   - Y-axis: Avg Defensive Rating
   - Size: Total Minutes
   - Legend: Team Name
   - Add reference lines at league average (110 offensive, 110 defensive)

4. **Bar Chart** - "Plus/Minus by Lineup"
   - Axis: lineup_hash (or create concat of player names)
   - Values: Total Plus Minus
   - Sort: Total Plus Minus (descending)
   - Top N filter: Show top 15

### Dashboard 2: "Player Impact Analysis"

**Page Layout**:

1. **Slicer** - Team selector
   - Add team_name as slicer to filter everything

2. **Table Visual** - "Player Impact Rankings"
   - Columns:
     - Player Name
     - Position
     - Total Minutes
     - On Court Plus Minus
     - Avg Net Rating
     - Plus Minus per 48 min
   - Sort by: Plus Minus per 48 min
   - Conditional formatting: Color-code Net Rating column

3. **Clustered Bar Chart** - "Top Players by Net Rating"
   - Axis: Player Name
   - Values: Avg Net Rating
   - Sort: Avg Net Rating (descending)
   - Top N: 10 players

4. **Line Chart** - "Player Impact Over Season" (if you have game dates)
   - X-axis: Game Date
   - Y-axis: Plus Minus
   - Legend: Player Name
   - Filter: Select specific players

### Dashboard 3: "Win/Loss Analysis"

**Page Layout**:

1. **Pie Chart** - "Win/Loss Record"
   - Legend: game_result (W/L)
   - Values: Count of games

2. **Clustered Bar Chart** - "Lineup Performance: Wins vs Losses"
   - Axis: lineup_hash (or player names)
   - Values: Avg Plus Minus in Game
   - Legend: Game Result (W/L)
   - Shows which lineups perform better in wins

3. **Table** - "Clutch Lineups" (Lineups used in close games)
   - Custom filter: WHERE ABS(home_score - away_score) <= 5
   - Shows lineups used in tight games and their performance

---

## Part 7: Pro Tips for Better Visuals

### Formatting Tips

1. **Color Scheme**: Use team colors
   - Go to Format → Data colors → select team colors for consistency

2. **Conditional Formatting**:
   - For Net Rating columns: Green for positive, Red for negative
   - Data bars for Plus/Minus columns

3. **Tooltips**: Add custom tooltips showing:
   - Games played
   - Minutes together
   - Detailed breakdown of offensive/defensive stats

### Performance Tips

1. **Filter Early**: Add page-level filters for:
   - Season
   - Team
   - Minimum minutes played

2. **DirectQuery vs Import**:
   - Use **Import** mode (default) for best performance
   - Your data isn't that large (~118 games so far)

3. **Aggregations**: Always use the aggregated views, not raw play_by_play data

---

## Part 8: Example Insights You Can Find

With this setup, you can answer questions like:

### Lineup Questions
- "Which 5-man lineups have the best net rating?"
- "Which lineups are used most in wins vs losses?"
- "What's our best clutch-time lineup?"
- "Which lineups improve our defense the most?"

### Player Questions
- "Who has the highest on-court impact?"
- "Which players make the team better when they play?"
- "Who are the best +/- players per 48 minutes?"
- "Which position group performs best?"

### Team Questions
- "What's our offensive rating with different lineups?"
- "How does lineup performance vary by opponent?"
- "Which lineups play together most often?"
- "Are our starting lineups outperforming bench lineups?"

---

## Part 9: Refreshing Data

As you load more games into your database:

1. In Power BI, click **"Refresh"** in the Home ribbon
2. All views will automatically update with new data
3. Your dashboards will reflect the latest games

You can also set up:
- **Scheduled refresh** if you publish to Power BI Service
- **Automatic refresh** when opening the file

---

## Part 10: Sharing Your Dashboard

### Option 1: Save as .pbix file
- File → Save
- Share the .pbix file with others who have Power BI Desktop

### Option 2: Publish to Power BI Service (requires paid account)
- Home → Publish
- Upload to powerbi.com
- Create shareable links or embed in websites

### Option 3: Export to PDF/PowerPoint
- File → Export to PDF (for static reports)
- File → Export to PowerPoint (for presentations)

---

## Troubleshooting

### "Can't connect to database"
- Check that PostgreSQL is running
- Verify credentials in .env file match what you're entering
- Ensure localhost:5432 is correct port

### "Table relationships not working"
- Go to Model view
- Manually create relationships as described in Part 4
- Make sure cardinality is set correctly (many-to-one)

### "Measures showing wrong values"
- Check that you're using the correct aggregation (SUM vs AVERAGE)
- Verify filters aren't excluding data unexpectedly
- Use DAX Studio to debug complex measures

### "Performance is slow"
- Reduce visual count on each page (max 10-15 visuals)
- Add page-level filters to reduce data volume
- Close unused tables in the model

---

## Next Steps

1. ✅ Connect to database
2. ✅ Load tables and views
3. ✅ Create basic measures
4. ✅ Build first dashboard
5. 🎯 Experiment with different visualizations
6. 🎯 Add more advanced DAX calculations
7. 🎯 Share insights with others!

**Happy analyzing! 🏀📊**

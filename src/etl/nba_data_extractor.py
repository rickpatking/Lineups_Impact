import pandas as pd
from nba_api.stats.endpoints import playbyplayv3, leaguegamefinder, commonteamroster
from nba_api.stats.static import teams, players

def get_season_games(season='2023-24'):
    try:
        gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable=season)
        games_df = gamefinder.get_data_frames()[0]
        print(f'Successfully got games for {season}')
        return games_df
    except Exception as e:
        print(e)
        return None
    
def get_game_playbyplay(game_id):
    try:
        pbpfinder = playbyplayv3.PlayByPlayV3(game_id)
        pbp_df = pbpfinder.get_data_frames()[0]
        print(f'Successfully got pbp data for {game_id}')
        return pbp_df

    except Exception as e:
        print(e)
        return None
    
def get_teams():
    teams_list = teams.get_teams()
    teams_df = pd.DataFrame(teams_list)
    print(f'Got all nba teams')
    return teams_df
    
def get_active_players():
    players_list = players.get_active_players()
    players_df = pd.DataFrame(players_list)
    print(f'Got all active players')
    return players_df

def pbp_cleaner(pbp):
    pbp = pbp.copy()
    pbp = pbp.rename(columns={'gameId': 'game_id', 
                              'actionId': 'action_id', 
                              'personId': 'player_id',
                              'playerNameI': 'player_name',
                              'teamId': 'team_id',
                              'actionType': 'action_type',
                              'subType': 'action_subtype',
                              'shotValue': 'shot_value',
                              'shotResult': 'shot_result'})
    return pbp
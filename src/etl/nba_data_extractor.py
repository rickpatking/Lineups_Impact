import pandas as pd
from nba_api.stats.endpoints import playbyplayv3, leaguegamefinder, commonteamroster
from nba_api.stats.static import teams, players
import time

class NBADataExtractor:
    def __init__(self, rate_limiter):
        self.rate_limiter = rate_limiter
        
    def get_season_games(self, season='2023-24'):
        self.rate_limiter.wait_if_needed()

        try:
            gamefinder = leaguegamefinder.LeagueGameFinder(season_nullable=season)
            games_df = gamefinder.get_data_frames()[0]
            self.rate_limiter.record_request()
            print(f'Successfully got games for {season}')
            return games_df
        except Exception as e:
            print(e)
            return None
        
    def get_game_playbyplay(self, game_id):
        self.rate_limiter.wait_if_needed()

        try:
            pbpfinder = playbyplayv3.PlayByPlayV3(game_id)
            pbp_df = pbpfinder.get_data_frames()[0]
            self.rate_limiter.record_request()
            print(f'Successfully got pbp data for {game_id}')
            return pbp_df

        except Exception as e:
            print(e)
            return None
        
    def get_teams(self):
        teams_list = teams.get_teams()
        teams_df = pd.DataFrame(teams_list)
        print(f'Got all nba teams')
        return teams_df
        
    def get_players(self, season='2023-24'):
        players_list = players.get_active_players()
        players_df = pd.DataFrame(players_list)
        print(f'Got all active players')
        return players_df
import pandas as pd
from nba_api.stats.endpoints import playbyplayv3, leaguegamefinder, commonteamroster
from nba_api.stats.static import teams
import time

class NBADataExtractor:
    def __init__(self, rate_limiter):
        """Initialize with rate limiter"""
        
    def get_season_games(self, season='2023-24'):
        """Get all games for a season"""
        
    def get_game_playbyplay(self, game_id):
        """Get play-by-play for one game"""
        
    def get_teams(self):
        """Get all NBA teams"""
        
    def get_players(self, season='2023-24'):
        """Get all players for a season"""
        
    def get_box_score(self, game_id):
        """Get box score (for starters and validation)"""
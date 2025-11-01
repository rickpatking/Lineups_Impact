import pandas as pd
import numpy as np
from nba_api.stats.endpoints import CommonTeamRoster, gamerotation

def clean_subs_pbp(playbyplay, team_id):
    subs = playbyplay[playbyplay['actionType'] == 'Substitution'].copy()

    subs['prev_name'] = subs['description'].str.split(r': | FOR').str[2]
    subs['prev_name'] = subs['prev_name'].str.lstrip()
    subs['prev_id'] = subs['personId']
    subs['next_name'] = subs['description'].str.split(r': | FOR').str[1]
    subs['next_name'] = subs['next_name'].str.lstrip()
    subs['next_id'] = None
    
    all_subs = subs[subs['teamTricode'] == 'IND'].copy()
    sorted_prev = np.sort(all_subs['prev_name'].unique())
    sorted_next = np.sort(all_subs['next_name'].unique())

    intersection = np.intersect1d(sorted_prev, sorted_next)
    difference = np.setdiff1d(sorted_prev, sorted_next)
    difference2 = np.setdiff1d(sorted_next, sorted_prev)
    all_players = np.concatenate((intersection, difference, difference2), axis=0)

    player_id_dict = dict()
    for player in all_players:
        try:
            playerdf = playbyplay[playbyplay['playerName'] == player]
            id = ((playerdf.iloc[0])['personId'])
            player_id_dict[player] = id
        except Exception as e: 
            team_roster = CommonTeamRoster(team_id=1610612754, season='2024-25')
            roster_df = team_roster.get_data_frames()[0]
            roster_df2 = (roster_df[roster_df['PLAYER'].str.contains(player)]).copy()
            player_id_dict[player] = roster_df2['PLAYER_ID'].iloc[0]

    for player, id in player_id_dict.items():
        subs.loc[subs['next_name'] == player, 'next_id'] = id

    return subs

def get_quarter_starters(playbyplay, subs, quarter, team_id):
    """
    Returns a list of the 5 players on the court at the start of a quarter
    playbyplay: playbyplay df that is cleaned
    quarter: int quarter to search
    team_id: int team_id
    """
    df = playbyplay[playbyplay['period'] == quarter].copy()
    df2 = df[df['teamId'] == team_id].copy()
    first_sub = df2[df2['actionType'] == 'Substitution'].index[0]
    df3 = df2.loc[:df2.index[df2.index.get_loc(first_sub)-1]]
    unique_ids = df3['personId'].unique()
    if len(unique_ids) < 5:
        subs = subs[subs['period'] == quarter].copy()
        first_sub_series = subs[subs['teamId'] == team_id].copy()
        while True:
            sub_series = first_sub_series.iloc[0]
            if sub_series['prev_id'] not in unique_ids.tolist():
                unique_ids = np.append(unique_ids, sub_series['prev_id'])
                return (unique_ids.tolist())
            first_sub_series = first_sub_series.iloc[1:]
    return (unique_ids.tolist())


def clean_data(pbp):
    playbyplay = pbp.copy()
    playbyplay['minutes'] = playbyplay['clock'].str.split(r'PT|M|S').str[1]
    playbyplay['seconds'] = playbyplay['clock'].str.split(r'PT|M|S').str[2]
    playbyplay['seconds_left_in_quarter'] = (pd.to_numeric(playbyplay['minutes']) * 60) + pd.to_numeric(playbyplay['seconds']).round(1)
    playbyplay['seconds_left_in_game'] = (pd.to_numeric(playbyplay['minutes']) * 60) + pd.to_numeric(playbyplay['seconds']) + (abs(4 - pd.to_numeric(playbyplay['period'])) * 720).round(1)
    playbyplay['seconds_into_game'] = (2880.0 - playbyplay['seconds_left_in_game']).round(1)
    return playbyplay

def get_lineups(game_id, team_id):
    rotation = gamerotation.GameRotation(game_id)
    rotation = rotation.get_data_frames()[0]
    rotation['IN_TIME_REAL'] = pd.to_numeric(rotation['IN_TIME_REAL'])/10
    rotation['OUT_TIME_REAL'] = pd.to_numeric(rotation['OUT_TIME_REAL'])/10
    sorted_rotations = rotation.sort_values(by='IN_TIME_REAL')
    sorted_rotations = sorted_rotations.reset_index()

    lineups = []
    starting_5 = sorted_rotations['PERSON_ID'].iloc[:5].tolist()
    first_lineup = {"PLAYERS": starting_5,
                    "IN_TIME_REAL": sorted_rotations['IN_TIME_REAL'].iloc[:5].min(),
                    "OUT_TIME_REAL": sorted_rotations['OUT_TIME_REAL'].iloc[:5].min()}
    lineups.append(first_lineup)

    for i, (index, sub) in enumerate(sorted_rotations.iloc[5:].iterrows()):
        curr_lineup = lineups[-1]['PLAYERS']
        min_time = lineups[-1]["OUT_TIME_REAL"]
        if (i == len(sorted_rotations.iloc[5:]) - 1):
            max_time = 2880.0
        else:
            max_time = sorted_rotations['IN_TIME_REAL'].iloc[index + 1]
        to_remove_time = sorted_rotations['IN_TIME_REAL'].iloc[index]
        to_remove_player_series = sorted_rotations[sorted_rotations['OUT_TIME_REAL'] == to_remove_time].copy()
        to_remove_player_series = to_remove_player_series['PERSON_ID']

        # Find which player in the series is actually in the current lineup
        to_remove_player = None
        for player in to_remove_player_series:
            if player in curr_lineup:
                to_remove_player = player
                break

        # If we found a player to remove, remove them
        if to_remove_player is not None:
            curr_lineup.remove(to_remove_player)
        curr_lineup.append(sorted_rotations['PERSON_ID'].iloc[index])
        curr_5 = {"PLAYERS": curr_lineup,
                "IN_TIME_REAL": min_time,
                "OUT_TIME_REAL": max_time}
        lineups.append(curr_5)
    return lineups

def get_stints(playbyplay, all_lineups, team_id):
    col_names = ['game_id', 'team_id', 'start_num', 'end_num', 'duration_secs', 'player1_id', 'player2_id', 'player3_id', 'player4_id', 'player5_id', 'lineup_hash']
    df = pd.DataFrame(columns=col_names)

    game_id = playbyplay['gameId'].iloc[0]
    for i in range(len(all_lineups)):
        lineup = all_lineups[i]['PLAYERS']
        lineup_start = all_lineups[i]['IN_TIME_REAL']
        lineup_end = all_lineups[i]["OUT_TIME_REAL"]

        # start = playbyplay[playbyplay['seconds_into_game'] == lineup_start].copy()
        # start_num = start['actionId'].iloc[0]

        # end = playbyplay[playbyplay['seconds_into_game'] == lineup_end].copy()
        # end_num = end['actionId'].iloc[0]

        start = playbyplay.iloc[(playbyplay['seconds_into_game'] - lineup_end).abs().argsort()][:1]
        if len(start) == 0:
            raise ValueError(f"No play-by-play data found near lineup start time {lineup_end}")
        start_num = start['actionId'].iloc[0]

        end = playbyplay.iloc[(playbyplay['seconds_into_game'] - lineup_start).abs().argsort()][:1]
        if len(start) == 0:
            raise ValueError(f"No play-by-play data found near lineup start time {lineup_start}")
        end_num = start['actionId'].iloc[0]

        duration_secs = lineup_end - lineup_start
        player1_id = lineup[0]
        player2_id = lineup[1]
        player3_id = lineup[2]
        player4_id = lineup[3]
        player5_id = lineup[4]
        lineup_hash = '-'.join(str(id) for id in lineup)
        df.loc[len(df)] = [game_id, team_id, start_num, end_num, duration_secs, player1_id, player2_id, player3_id, player4_id, player5_id, lineup_hash]
    return df





# testing
# df = pd.read_csv('data/raw/thunder_pacers_game7.csv')
# pacers_id = 1610612754
# game_id = '0042400407'
# # # test pacers
# clean_subs_df = clean_subs_pbp(df, pacers_id)
# lineups = get_lineups(game_id, pacers_id)
# print(lineups)
# clean_pbp = clean_data(df)
# stints = get_stints(clean_pbp, lineups, pacers_id)
# print(stints.iloc[0])
# stints = get_stints(clean_pbp, lineups[0], lineups[1], pacers_id)
# stints = stints[stints['duration_secs'] != 0].copy()
# stints.to_csv('data/raw/thunder_pacers_game7_stints.csv', index=False)
# print(lineups)
# print(get_quarter_starters(df, clean_df, 3, pacers_id))
import pandas as pd
import numpy as np
from nba_api.stats.endpoints import CommonTeamRoster

def clean_pbp(playbyplay, team_id):
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

        # more_events = df.head(50)
        # more_uniques = more_events['personId'].unique()
        # missed_players = np.setdiff1d(more_uniques, unique_ids)
        # missed_players = missed_players.tolist()
        # for i in range(len(missed_players)):
        #     if missed_players[i] != first_sub_series['next_id']:
        #         unique_ids = np.append(unique_ids, first_sub_series['prev_id'])
        #         return (unique_ids.tolist())
    return (unique_ids.tolist())

def get_lineups(playbyplay, subs, team_id):
    all_lineups = []
    lineups_action_id = []

    team_subs = subs.loc[subs['teamId'] == team_id]
    for i in range(1, 5):

        quarter = team_subs[team_subs['period'] == i].copy()
        starters = get_quarter_starters(playbyplay, subs, i, team_id)
        all_lineups.append(starters)
        lineups_action_id.append(team_subs['actionId'].iloc[0])

        for index, sub in quarter.iterrows():
            try:
                current_five = all_lineups[-1][:]
                current_five.remove(sub['prev_id'])
                current_five.append(sub['next_id'])
                all_lineups.append(current_five)
                lineups_action_id.append(index+1)
            except Exception as e:
                print(e)
                print(index)
                print(current_five)
                print(all_lineups[-1][:])
                print()
    return all_lineups, lineups_action_id

# testing
# df = pd.read_csv('data/raw/thunder_pacers_game7.csv')
# pacers_id = 1610612754
# # test pacers
# clean_df = clean_pbp(df, pacers_id)
# lineups = get_lineups(df, clean_df, pacers_id)
# # print(lineups)
# # print(get_quarter_starters(df, clean_df, 3, pacers_id))
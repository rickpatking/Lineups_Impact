from nba_api.stats.endpoints import gamerotation

rotation = gamerotation.GameRotation('0042400407')
dfs = rotation.get_data_frames()

print(f'Number of dataframes returned: {len(dfs)}')

for i, df in enumerate(dfs):
    print(f'\nDataFrame {i}:')
    print(f'  Shape: {df.shape}')
    print(f'  Columns: {list(df.columns)}')
    if 'TEAM_ID' in df.columns:
        print(f'  Unique TEAM_IDs: {df["TEAM_ID"].unique()}')
        print(f'  Row count by team: {df["TEAM_ID"].value_counts().to_dict()}')

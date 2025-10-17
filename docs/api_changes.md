I'm using nba_api to get my data.

Endpoints:
leaguegamefinder
playbyplayv3

rate limit is probably around 20/min. I'm gonna try 10-15/min

blocks and steals aren't recorded in actionType. Will need to split description to get steals and blocks

the player id and name are for the person getting subbed out. Gonna have to split the description column to get both players

clock starts at 12m and counts down, clock doesnt show the quarter. Need both to figure out the time
# model_mlb_predictions.py

import sys
from datetime import datetime
from scrape_probable_pitchers_api import get_probable_pitchers
import pandas as pd
from sklearn.linear_model import LogisticRegression
import numpy as np

# --------------------------------------------------------
# STEP 1: Determine the date
# --------------------------------------------------------

if len(sys.argv) > 1:
    date_str = sys.argv[1]
else:
    date_str = datetime.today().strftime("%Y-%m-%d")

print(f"Getting games for: {date_str}")

# --------------------------------------------------------
# STEP 2: Scrape games from API
# --------------------------------------------------------

games = get_probable_pitchers(date_str)

if not games:
    print("⚠️ No games found for this date.")
    sys.exit()

# --------------------------------------------------------
# STEP 3: Load data into DataFrame
# --------------------------------------------------------

df = pd.DataFrame(games)

# Optional: save CSV for later
df.to_csv(f"data/mlb_games_{date_str}.csv", index=False)

# --------------------------------------------------------
# STEP 4: Flatten lineup info
# --------------------------------------------------------

df["away_lineup_size"] = df["lineup_away"].apply(
    lambda x: len(x) if isinstance(x, list) else 0
)

df["home_lineup_size"] = df["lineup_home"].apply(
    lambda x: len(x) if isinstance(x, list) else 0
)

# Check if Ohtani is in lineup
def has_player(lineup, player_name):
    if isinstance(lineup, list):
        return any(player_name in player["name"] for player in lineup)
    return False

df["away_has_ohtani"] = df["lineup_away"].apply(
    lambda x: has_player(x, "Ohtani")
)

df["home_has_ohtani"] = df["lineup_home"].apply(
    lambda x: has_player(x, "Ohtani")
)

# --------------------------------------------------------
# STEP 5: Scrape FanGraphs pitcher stats
# --------------------------------------------------------

print("Fetching FanGraphs pitcher stats...")

url = "https://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=0&type=c,5,6,8,13&season=2024"

tables = pd.read_html(url)
pitchers_df = tables[0]

pitchers_df = pitchers_df.rename(columns={
    "Name": "pitcher_name",
    "ERA": "ERA",
    "FIP": "FIP",
    "xFIP": "xFIP"
})

# --------------------------------------------------------
# STEP 6: Merge pitcher stats
# --------------------------------------------------------

df = df.merge(
    pitchers_df,
    left_on="away_probable_pitcher",
    right_on="pitcher_name",
    how="left",
    suffixes=("", "_away_pitcher")
)

df = df.merge(
    pitchers_df,
    left_on="home_probable_pitcher",
    right_on="pitcher_name",
    how="left",
    suffixes=("", "_home_pitcher")
)

# --------------------------------------------------------
# STEP 7: Prepare model features
# --------------------------------------------------------

# Features: away ERA, home ERA, lineup sizes
features = df[[
    "ERA",
    "ERA_home_pitcher",
    "away_lineup_size",
    "home_lineup_size"
]].fillna(4.50)

# Dummy target (for now) - random win/loss
df["home_team_wins"] = np.random.randint(0, 2, size=len(df))

y = df["home_team_wins"]

# --------------------------------------------------------
# STEP 8: Fit Logistic Regression
# --------------------------------------------------------

model = LogisticRegression()
model.fit(features, y)

# Predict win probabilities
df["home_win_prob"] = model.predict_proba(features)[:, 1]

# --------------------------------------------------------
# STEP 9: Show predictions
# --------------------------------------------------------

print(df[[
    "home_team",
    "away_team",
    "home_win_prob"
]])
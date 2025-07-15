#!/usr/bin/env python3
# ------------------------------------------------------------
# scrape_probable_pitchers_api.py
#
# Purpose:
#   Fetch MLB game data for a given date, including:
#       - Probable starting pitchers
#       - Game time
#       - Weather conditions
#       - Lineups for each team
#
# Usage:
#   python scrape_probable_pitchers_api.py
#   OR
#   python scrape_probable_pitchers_api.py YYYY-MM-DD
#
# Author: [Bearagamo]
# ------------------------------------------------------------

import requests
from datetime import date
from pprint import pprint


# ------------------------------------------------------------
# Function: get_lineup
# ------------------------------------------------------------
def get_lineup(team_data):
    """
    Extracts a team's lineup from the boxscore JSON.

    Parameters:
        team_data (dict): JSON data for one team's boxscore.

    Returns:
        list[dict]: List of players with names and positions.
    """
    lineup = []
    for player in team_data.get("players", {}).values():
        if "position" in player:
            lineup.append({
                "name": player["person"]["fullName"],
                "position": player["position"]["name"]
            })
    return lineup


# ------------------------------------------------------------
# Function: fetch_boxscore
# ------------------------------------------------------------
def fetch_boxscore(game_pk):
    """
    Downloads the boxscore JSON for a specific game.

    Parameters:
        game_pk (int): MLB game primary key ID.

    Returns:
        dict or None: Boxscore JSON, or None on error.
    """
    box_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"

    try:
        response = requests.get(box_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"⚠️ Error fetching boxscore for game {game_pk}: {e}")
        return None


# ------------------------------------------------------------
# Function: get_probable_pitchers
# ------------------------------------------------------------
def get_probable_pitchers(target_date=None):
    """
    Fetches MLB games and probable pitcher data for a specific date.

    Parameters:
        target_date (str, optional): Date string in YYYY-MM-DD format.
                                     Defaults to today if None.

    Returns:
        list[dict]: List of matchups including:
            - away_team
            - home_team
            - away_probable_pitcher
            - home_probable_pitcher
            - game_time_utc
            - weather_condition
            - weather_temp
            - weather_wind
            - lineup_home
            - lineup_away
    """
    # Default to today's date if none provided
    if target_date is None:
        target_date = date.today().isoformat()

    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "sportId": "1",  # MLB
        "date": target_date,
        "hydrate": "probablePitcher(note),game(content),linescore,team,weather,decisions",
        "language": "en"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch schedule: {e}")
        return []

    matchups = []

    for day in data.get("dates", []):
        for game in day.get("games", []):
            # ------------------------------------------------------------
            # Extract basic game details
            # ------------------------------------------------------------
            matchup = {
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_probable_pitcher": game["teams"]["away"].get("probablePitcher", {}).get("fullName"),
                "home_probable_pitcher": game["teams"]["home"].get("probablePitcher", {}).get("fullName"),
                "game_time_utc": game.get("gameDate"),
                "weather_condition": game.get("weather", {}).get("condition"),
                "weather_temp": game.get("weather", {}).get("temp"),
                "weather_wind": game.get("weather", {}).get("wind"),
                "lineup_home": [],
                "lineup_away": []
            }

            # ------------------------------------------------------------
            # Fetch boxscore for lineup data
            # ------------------------------------------------------------
            game_pk = game.get("gamePk")

            if game_pk:
                box_data = fetch_boxscore(game_pk)

                if box_data:
                    matchup["lineup_home"] = get_lineup(box_data["teams"]["home"])
                    matchup["lineup_away"] = get_lineup(box_data["teams"]["away"])

            matchups.append(matchup)

    return matchups


# ------------------------------------------------------------
# Main block: test run if called as standalone script
# ------------------------------------------------------------
if __name__ == "__main__":
    import sys

    # Check if user passed a date argument
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = None  # Use today

    games = get_probable_pitchers(target_date)

    if games:
        pprint(games)
    else:
        print("⚠️ No games found or an error occurred.")
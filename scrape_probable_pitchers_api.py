# scrape_probable_pitchers_api.py

import requests

def get_probable_pitchers(date_str):
    """
    Pulls probable pitchers and game info from MLB API for the given date.
    Returns a list of dictionaries (one per game).
    """

    # Build MLB Stats API URL
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=probablePitcher(lineups,person,stats),linescore,team,weather"

    response = requests.get(url)
    data = response.json()

    games = []

    for date in data.get("dates", []):
        for game in date.get("games", []):
            game_info = {
                "away_team": game["teams"]["away"]["team"]["name"],
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_probable_pitcher": None,
                "home_probable_pitcher": None,
                "game_time_utc": game.get("gameDate", None),
                "weather_condition": None,
                "weather_temp": None,
                "weather_wind": None,
                "lineup_away": [],
                "lineup_home": []
            }

            # Probable pitchers
            if "probablePitcher" in game["teams"]["away"]:
                game_info["away_probable_pitcher"] = game["teams"]["away"]["probablePitcher"]["fullName"]
            if "probablePitcher" in game["teams"]["home"]:
                game_info["home_probable_pitcher"] = game["teams"]["home"]["probablePitcher"]["fullName"]

            # Weather
            weather = game.get("weather", None)
            if weather:
                game_info["weather_condition"] = weather.get("condition", None)
                game_info["weather_temp"] = weather.get("temp", None)
                game_info["weather_wind"] = weather.get("wind", None)

            # Lineups (if available)
            away_lineup = []
            home_lineup = []

            away_players = game["teams"]["away"].get("probablePitcher", {}).get("lineup", {}).get("expected", [])
            home_players = game["teams"]["home"].get("probablePitcher", {}).get("lineup", {}).get("expected", [])

            if away_players:
                away_lineup = [
                    {"name": p.get("fullName", ""), "position": p.get("position", {}).get("name", "")}
                    for p in away_players
                ]

            if home_players:
                home_lineup = [
                    {"name": p.get("fullName", ""), "position": p.get("position", {}).get("name", "")}
                    for p in home_players
                ]

            game_info["lineup_away"] = away_lineup
            game_info["lineup_home"] = home_lineup

            games.append(game_info)

    return games
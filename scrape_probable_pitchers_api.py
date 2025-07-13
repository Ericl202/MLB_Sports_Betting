import requests
from datetime import date
from pprint import pprint

def get_probable_pitchers(target_date=None):
    if target_date is None:
        target_date = date.today().isoformat()

    url = f"https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "sportId": "1",
        "date": target_date,
        "hydrate": "probablePitcher(note),game(content),linescore,team,weather,decisions",
        "language": "en"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    matchups = []

    for day in data.get("dates", []):
        for game in day.get("games", []):
            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            away_pitcher = game["teams"]["away"].get("probablePitcher", {}).get("fullName")
            home_pitcher = game["teams"]["home"].get("probablePitcher", {}).get("fullName")

            game_time_utc = game.get("gameDate")

            matchup = {
                "away_team": away_team,
                "away_probable_pitcher": away_pitcher,
                "home_team": home_team,
                "home_probable_pitcher": home_pitcher,
                "game_time_utc": game_time_utc
            }

            weather_data = game.get("weather", {})
            weather_condition = weather_data.get("condition")
            weather_temp = weather_data.get("temp")
            weather_wind = weather_data.get("wind")
            
            matchup.update({
                "weather_condition": weather_condition,
                "weather_temp": weather_temp,
                "weather_wind": weather_wind
            })

            game_pk = game["gamePk"]
            box_url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
            box_res = requests.get(box_url)
            box_res.raise_for_status()
            box_data = box_res.json()
            
            lineup_home = []
            lineup_away = []
            
            for player_id, player in box_data["teams"]["home"]["players"].items():
                 if "position" in player:
                      lineup_home.append({
                           "name": player["person"]["fullName"],
                           "position": player["position"]["name"]
                        })
                      
            for player_id, player in box_data["teams"]["away"]["players"].items():
                 if "position" in player:
                      lineup_away.append({
                           "name": player["person"]["fullName"],
                           "position": player["position"]["name"]
                        })
                      
            matchup.update({
                "lineup_home": lineup_home,
                "lineup_away": lineup_away
            })

            matchups.append(matchup)

    return matchups

if __name__ == "__main__":
    pitchers = get_probable_pitchers("2024-07-12")
    pprint(pitchers)
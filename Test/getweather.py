import requests
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List
import google_calendar

load_dotenv()

app = Flask(__name__)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


def get_current_weather() -> dict:
    """Get current weather data from HKO API"""
    url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
    params = {
        "dataType": "rhrread",
        "lang": "en"
    }

    try:
        response = requests.get(url, params=params)
        weather_data = response.json()

        temp = None
        if 'temperature' in weather_data and 'data' in weather_data['temperature']:
            for temp_record in weather_data['temperature']['data']:
                if temp_record['place'] == 'Sha Tin':
                    temp = temp_record['value']
                    break
                elif temp is None:
                    temp = temp_record['value']

        humidity = None
        if 'humidity' in weather_data and 'data' in weather_data['humidity']:
            if weather_data['humidity']['data']:
                humidity = weather_data['humidity']['data'][0]['value']

        rainfall = None
        if 'rainfall' in weather_data and 'data' in weather_data['rainfall']:
            for rainfall_record in weather_data['rainfall']['data']:
                if rainfall_record['place'] == 'Sha Tin':
                    rainfall = rainfall_record.get('max', 0)
                    break
                elif rainfall is None:
                    rainfall = rainfall_record.get('max', 0)

        uv_index = None
        current_hour = datetime.now().hour
        is_daytime = 6 <= current_hour <= 18

        if 'uvindex' in weather_data:
            if isinstance(weather_data['uvindex'], (int, float)) or (
                    isinstance(weather_data['uvindex'], str) and weather_data['uvindex'].isdigit()):
                uv_index = str(weather_data['uvindex'])

            elif isinstance(weather_data['uvindex'], dict):
                if 'value' in weather_data['uvindex']:
                    uv_index = str(weather_data['uvindex']['value'])

                elif 'data' in weather_data['uvindex']:
                    data = weather_data['uvindex']['data']

                    if isinstance(data, list) and len(data) > 0:
                        for item in data:
                            if isinstance(item, dict) and 'value' in item:
                                uv_index = str(item['value'])
                                break

                    elif isinstance(data, dict) and 'value' in data:
                        uv_index = str(data['value'])

                elif 'current' in weather_data['uvindex'] and 'value' in weather_data['uvindex']['current']:
                    uv_index = str(weather_data['uvindex']['current']['value'])

            elif isinstance(weather_data['uvindex'], list) and len(weather_data['uvindex']) > 0:
                for item in weather_data['uvindex']:
                    if isinstance(item, dict) and 'value' in item:
                        uv_index = str(item['value'])
                        break
                    elif isinstance(item, (int, float, str)):
                        uv_index = str(item)
                        break

        if uv_index is None or uv_index == '':
            if is_daytime:
                uv_index = "1"
            else:
                uv_index = "0"

        icon = None
        if 'icon' in weather_data:
            if isinstance(weather_data['icon'], list) and len(weather_data['icon']) > 0:
                icon = weather_data['icon'][0]
            elif isinstance(weather_data['icon'], int):
                icon = weather_data['icon']
            else:
                icon = 62
        else:
            icon = 62

        return {
            "temperature": temp,
            "humidity": humidity,
            "rainfall": rainfall,
            "uv_index": uv_index,
            "icon": icon
        }
    except Exception as e:
        return {}


def get_weather_forecast() -> dict:
    """Get 9-day weather forecast from HKO API"""
    url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php"
    params = {
        "dataType": "fnd",
        "lang": "en"
    }

    try:
        response = requests.get(url, params=params)
        forecast_data = response.json()
        return forecast_data
    except Exception as e:
        return {}


def get_outfit_advice(weather_description: List[str], user: str, specialneed: str, events=None) -> str:
    filepath = f"Users/{user}"
    file_names = os.listdir(filepath)
    available_outfits = [f for f in file_names if os.path.isfile(os.path.join(filepath, f))]

    # Define important event keywords
    important_event_keywords = [
        "meeting", "conference", "presentation", "interview", "speech",
        "wedding", "ceremony", "dinner", "lunch", "party", "gala", 
        "function", "event", "celebration", "birthday", "anniversary",
        "sports", "game", "match", "competition", "tournament", "workout",
        "date", "formal", "official", "business", "exhibition", "show"
    ]
    
    # Filter for important events
    important_events = []
    if events and len(events) > 0:
        for event in events:
            event_summary = event.get('summary', '').lower()
            event_description = event.get('description', '').lower()
            
            # Check if any important keywords are in the event summary or description
            is_important = any(keyword in event_summary or keyword in event_description for keyword in important_event_keywords)
            
            if is_important:
                important_events.append(event)
    
    # Create event description section
    event_description = ""
    if important_events:
        event_description = "Important events today:\n"
        for event in important_events[:3]:  # Limit to 3 events to keep prompt reasonable
            event_time = event.get('time_str', 'All day')
            event_summary = event.get('summary', 'Untitled event')
            event_location = event.get('location', '')
            event_description += f"- {event_time}: {event_summary}"
            if event_location:
                event_description += f" at {event_location}"
            event_description += "\n"
    else:
        event_description = "No important events scheduled for today.\n"

    # Complete weather and events context for the AI 
    context_description = (
        f"Current weather conditions:\n"
        f"Temperature: {weather_description[0]}°C\n"
        f"Humidity: {weather_description[1]}%\n"
        f"Rainfall: {weather_description[2]} mm\n"
        f"UV Index: {weather_description[3]}\n\n"
        f"{event_description}\n"
        f"Available outfit options:\n"
        f"{', '.join(available_outfits)}\n\n"
        f"Based on the weather data above, the important events scheduled for today, and the available outfit options, "
        f"please recommend the most suitable outfit. If there are important meetings, presentations, dates, or other formal occasions, "
        f"recommend more formal attire. If there are sports activities, recommend suitable athletic wear."
        f"Special needs: {specialneed}\n"
        f"Please only reply with your recommended outfit filename, followed by a very short reason (include a clothing emoji). "
        f"Answer in English. Format: xxx.jpg:reason"
    )

    url = "https://api.deepseek.com/chat/completions"

    payload = json.dumps({
        "messages": [
            {
                "content": "You are a professional styling assistant who needs to recommend the most suitable outfit based on weather conditions and important scheduled events from the available options.",
                "role": "system"
            },
            {
                "content": context_description,
                "role": "user"
            }
        ],
        "model": "deepseek-chat",
        "temperature": 0.3,
        "max_tokens": 50
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer sk-8eb9823ca5184eb7b675d4b41131cb49'
    }

    response = requests.post(url, headers=headers, data=payload)
    response_data = response.json()

    # Get the AI outfit recommendation
    ai_recommendation = response_data["choices"][0]["message"]["content"].strip()
    recommended_outfit = ai_recommendation.split(":")
    outfit_path = os.path.join(filepath, recommended_outfit[0])
    filepath = outfit_path

    return ai_recommendation, filepath, important_events


def get_song_advice(mood=None):
    # MODIFY THIS LINE TO CHANGE THE MOOD MANUALLY - this is the only place to change
    test_mood = "love"  # Change this value to whatever mood you want
    mood = test_mood
    
    try:
        with open("songlist.js", "r", encoding="utf-8") as f:
            content = f.read()
            content = content.strip()
            if content.startswith('{') and content.endswith('}'):
                song_data = json.loads(content)
            else:
                print("Invalid JSON format in songlist.js")
                return None
                
        prompt = (
            f"You are a professional music recommendation assistant who needs to select the most suitable song based on the user's mood from the following list:\n"
            f"Current user mood: {mood}\n\n"
            f"Available songs:\n"
        )
        for song in song_data["songs"]:
            prompt += f"- {song['name']} by {song['artist']} genre: {song['genre']}\n"

        prompt += (
            f"\nBased on the user's mood ('{mood}'), please recommend the most suitable song."
            f"Please only reply with the song name and artist, using the exact names from the list I provided. Format: song name:artist"
        )
        
        # Call the AI model
        url = "https://api.deepseek.com/chat/completions"
        payload = json.dumps({
            "messages": [
                {
                    "content": "You are a professional music recommendation assistant who needs to select the most suitable song based on the user's mood from the given options.",
                    "role": "system"
                },
                {
                    "content": prompt,
                    "role": "user"
                }
            ],
            "model": "deepseek-chat",
            "temperature": 0.3,
            "max_tokens": 50
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer sk-8eb9823ca5184eb7b675d4b41131cb49'
        }
        response = requests.post(url, headers=headers, data=payload)
        response_data = response.json()
        ai_recommendation = response_data["choices"][0]["message"]["content"].strip()
        
        try:
            recommended_song, recommended_artist = ai_recommendation.split(":")
            recommended_song = recommended_song.strip()
            recommended_artist = recommended_artist.strip()
            
            for song in song_data["songs"]:
                if song["name"].lower() == recommended_song.lower() and song["artist"].lower() == recommended_artist.lower():
                    print(f"Recommended song: {song['name']} by {song['artist']} for mood: {mood}")
                    return {
                        "embed_url": song["soundcloud_embed"],
                        "name": song["name"],
                        "artist": song["artist"],
                        "genre": song["genre"],
                        "mood": mood
                    }
            
            for song in song_data["songs"]:
                if recommended_song.lower() in song["name"].lower() or song["name"].lower() in recommended_song.lower():
                    print(f"Partial match found: {song['name']} by {song['artist']} for mood: {mood}")
                    return {
                        "embed_url": song["soundcloud_embed"],
                        "name": song["name"],
                        "artist": song["artist"],
                        "genre": song["genre"],
                        "mood": mood
                    }
                    
            if song_data["songs"]:
                print(f"Using fallback song: {song_data['songs'][0]['name']} for mood: {mood}")
                song = song_data["songs"][0]
                return {
                    "embed_url": song["soundcloud_embed"],
                    "name": song["name"],
                    "artist": song["artist"],
                    "genre": song["genre"],
                    "mood": mood
                }
                
        except Exception as e:
            print(f"Error parsing recommendation: {e}")
            print(f"AI response was: {ai_recommendation}")
            
            # Fallback to first song
            if song_data["songs"]:
                song = song_data["songs"][0]
                return {
                    "embed_url": song["soundcloud_embed"],
                    "name": song["name"],
                    "artist": song["artist"],
                    "genre": song["genre"],
                    "mood": mood
                }
    except Exception as e:
        print(f"Error in get_song_advice: {e}")
        return None


@app.route('/weather')
def get_weather():
    current_weather = get_current_weather()
    forecast = get_weather_forecast()

    # Get today's calendar events
    calendar_service = google_calendar.get_calendar_service()
    calendar_events = google_calendar.get_upcoming_events(days=1, max_results=5)
    
    today_events = []
    if calendar_events and 'events' in calendar_events:
        today = datetime.now().strftime("%b %d, %Y")
        
        for event in calendar_events['events']:
            event_date = event.get('date_str', '')
            if event_date == today:
                today_events.append(event)

    weather_description = [current_weather["temperature"], current_weather["humidity"], current_weather["rainfall"],
                           current_weather["uv_index"]]
    user = "victor"

    # Include events in outfit advice request
    outfit_advice, filepath, important_events = get_outfit_advice(
        weather_description, 
        user, 
        specialneed="None", 
        events=today_events
    )
    
    outfit_advice = outfit_advice.split(":")
    outfit_advice = outfit_advice[1]
    print("Weather values used:", weather_description)
    print("Important events considered:", [e.get('summary', 'Untitled') for e in important_events])
    print("Outfit advice:", outfit_advice)
    print("Image path:", filepath)

    return jsonify({
        "weather": current_weather,
        "forecast": forecast,
        "outfit": outfit_advice,
        "image_path": filepath,
        "events": today_events,
        "important_events": important_events
    })


# New dedicated endpoint for outfit recommendations
@app.route('/outfit')
def get_outfit():
    # Get current weather
    current_weather = get_current_weather()
    
    # Get today's calendar events
    calendar_events = google_calendar.get_upcoming_events(days=1, max_results=5)
    
    today_events = []
    if calendar_events and 'events' in calendar_events:
        today = datetime.now().strftime("%b %d, %Y")
        
        for event in calendar_events['events']:
            event_date = event.get('date_str', '')
            if event_date == today:
                today_events.append(event)

    # Use real weather for the recommendation
    test_weather = [
        current_weather['temperature'],
        current_weather['humidity'],
        current_weather['rainfall'],
        current_weather['uv_index']
    ]

    user = "victor"
    outfit_advice, filepath, important_events = get_outfit_advice(
        test_weather, 
        user, 
        specialneed="None", 
        events=today_events
    )

    if ":" in outfit_advice:
        outfit_advice = outfit_advice.split(":")[1]

    print("Weather values used:", test_weather)
    print("Important events considered:", [e.get('summary', 'Untitled') for e in important_events])
    print("Outfit advice:", outfit_advice)
    print("Image path:", filepath)

    return jsonify({
        "advice": outfit_advice,
        "image_path": filepath,
        "test_weather": {
            "temperature": test_weather[0],
            "humidity": test_weather[1],
            "rainfall": test_weather[2],
            "uv_index": test_weather[3]
        },
        "events": today_events,
        "important_events": important_events
    })

# A new endpoint to get song recommendations
@app.route('/music')
def get_music():
    recommendation = get_song_advice()
    if recommendation:
        return jsonify(recommendation)
    else:
        return jsonify({"error": "Could not generate song recommendation"}), 500

# Add an endpoint to get the current mood
@app.route('/get_mood')
def get_mood():
    # Get the manually set mood from the function
    mood_data = get_song_advice()
    if mood_data and 'mood' in mood_data:
        return jsonify({"mood": mood_data['mood']})
    return jsonify({"mood": "Unknown"})


google_calendar.register_calendar_routes(app)

if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
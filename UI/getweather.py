import requests
import json
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

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
            if isinstance(weather_data['uvindex'], (int, float)) or (isinstance(weather_data['uvindex'], str) and weather_data['uvindex'].isdigit()):
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

def get_outfit_advice(weather_description: str) -> str:
    url = "https://api.deepseek.com/chat/completions"

    payload = json.dumps({
        "messages": [
            {
                "content": "You are a helpful fashion assistant. Based on the weather information provided, suggest an outfit with exactly 4 items: Head (hat or none), Top (shirt/jacket), Bottom (pants/shorts/skirt), and Shoes. Format your response as 4 separate lines, with each line containing an emoji followed by the item description. For example:\n🧢 Baseball cap\n👕 Light cotton t-shirt\n👖 Jeans\n👟 Sneakers",
                "role": "system"
            },
            {
                "content": weather_description,
                "role": "user"
            }
        ],
        "model": "deepseek-chat",
        "frequency_penalty": 0,
        "max_tokens": 2048,
        "presence_penalty": 0,
        "response_format": {
            "type": "text"
        },
        "stop": None,
        "stream": False,
        "stream_options": None,
        "temperature": 1,
        "top_p": 1,
        "tools": None,
        "tool_choice": "none",
        "logprobs": False,
        "top_logprobs": None
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {os.getenv("DEEPSEEK_API_KEY")}'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response_data = response.json()
        outfit_advice = response_data["choices"][0]["message"]["content"]
        return outfit_advice
    except Exception as e:
        return "🧢 Baseball cap\n👕 Light T-shirt\n👖 Jeans\n👟 Sneakers"


@app.route('/weather')
def get_weather():
    current_weather = get_current_weather()
    
    forecast = get_weather_forecast()
    
    weather_description = (
        f"Current weather conditions:\n"
        f"Temperature: {current_weather.get('temperature', 'N/A')}°C\n"
        f"Humidity: {current_weather.get('humidity', 'N/A')}%\n"
        f"Rainfall: {current_weather.get('rainfall', 'N/A')} mm\n"
        f"UV Index: {current_weather.get('uv_index', 'N/A')}\n"
        f"Please recommend appropriate outfit for today based on this weather."
    )
    
    outfit_advice = get_outfit_advice(weather_description)
    
    return jsonify({
        "weather": current_weather,
        "forecast": forecast,
        "outfit": outfit_advice
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
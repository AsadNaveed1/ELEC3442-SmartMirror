import requests
import json
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List

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


def get_outfit_advice(weather_description: List[str],user: str,specialneed: str) -> str:
    filepath = f"Users\{user}"
    file_names = os.listdir(filepath)
    available_outfits = [f for f in file_names if os.path.isfile(os.path.join(filepath, f))]

    weather_description = (
        f"当前天气条件如下:\n"
        f"温度: {weather_description[0]}°C\n"
        f"湿度: {weather_description[1]}%\n"
        f"降雨量: {weather_description[2]} mm\n"
        f"紫外线指数: {weather_description[3]}\n\n"
        f"可选的穿搭组合有:\n"
        f"{', '.join(available_outfits)}\n\n"
        f"根据上述天气数据和可选的穿搭组合，请推荐最适合的一套衣服。"
        f"特殊需求：{specialneed}"
        f"请只回复你推荐的穿搭图片的文件名，包含一句最简短的原因（加上衣服的emoji），以英文回答。格式为xxx.jpg:原因"
    )

    url = "https://api.deepseek.com/chat/completions"

    payload = json.dumps({
        "messages": [
            {
                "content": "你是一个专业的穿搭助手，需要根据天气情况从给定的穿搭选项中选择最合适的一套。",
                "role": "system"
            },
            {
                "content": weather_description,
                "role": "user"
            }
        ],
        "model": "deepseek-chat",
        "temperature": 0.3,  # 降低随机性，使选择更确定性
        "max_tokens": 50
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer sk-8eb9823ca5184eb7b675d4b41131cb49'
    }

    response = requests.post(url, headers=headers, data=payload)
    response_data = response.json()

    # 获取AI推荐的穿搭
    ai_recommendation = response_data["choices"][0]["message"]["content"].strip()
    recommended_outfit = ai_recommendation.split(":")
    outfit_path = os.path.join(filepath, recommended_outfit[0])
    filepath = outfit_path

    return ai_recommendation,filepath


@app.route('/weather')
def get_weather():
    current_weather = get_current_weather()

    forecast = get_weather_forecast()

    #weather_description = [current_weather["temperature"], current_weather["humidity"], current_weather["rainfall"],current_weather["uv_index"]]
    weather_description = ["1", "90", "20", "78"]
    user = "victor"

    outfit_advice, filepath = get_outfit_advice(weather_description, user,specialneed="None")  # access deepseek v3 and get recommendation
    outfit_advice = outfit_advice.split(":")
    outfit_advice = outfit_advice[1]
    print(outfit_advice)
    print(filepath)

    return jsonify({
        "weather": current_weather,
        "forecast": forecast,
        "outfit": outfit_advice,
        "image_path" : filepath
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')
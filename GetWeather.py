import requests
import deepl

def get_weather(city, WEATHER_API_KEY, DEEPL_AUTH_KEY):
    # 영어로 번역
    translator = deepl.Translator(DEEPL_AUTH_KEY)
    city = str(translator.translate_text(city, target_lang='EN-US'))
    
    api = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    
    result = requests.get(api)
    if result.status_code != 200:
        raise Exception(f"Failed to get weather data: {result.status_code} {result.text}")
    
    data = result.json()
    
    if 'weather' not in data or 'main' not in data:
        raise Exception("Invalid response from weather API")
    
    weather = data['weather'][0]['description']
    temp = data['main']['temp']
    return weather, temp
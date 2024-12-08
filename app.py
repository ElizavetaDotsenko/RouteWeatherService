import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

API_KEY = "RUHsTC8pTBp0L74bBGtnFV86G77yGCGZ"
BASE_URL = "http://dataservice.accuweather.com/"


def coordinates_by_city(city): #получаем координаты города по названию, чтобы потом использовать их
    try:
        url = f"{BASE_URL}locations/v1/cities/search"  #отдельно на accuweather
        params = {"apikey": API_KEY, "q": city}  #стандартные
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None, f"City '{city}' not found."  #сразу добавляю проверку на неправильно введенный город

        location_key = data[0]["Key"]
        return location_key, None
    except requests.RequestException as e:
        return None, f"API error for city '{city}': {e}"  #если проблемы с API

def weather_by_location(location_key): # Получаем данные о погоде по ключу города
    try:
        url = f"{BASE_URL}currentconditions/v1/{location_key}"
        params = {
            "apikey": API_KEY,
            "details": "true"  # Запрашиваем полные данные
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None, "Weather data not found"

        weather = data[0]
        result = {
            "weather_text": weather["WeatherText"],
            "temperature_celsius": weather["Temperature"]["Metric"]["Value"], #правильный вывод
            "humidity": weather.get("RelativeHumidity"),
            "wind_speed_kmh": weather.get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Value"),
        }
        return result, None
    except requests.RequestException as e:
        return None, str(e)

def precipitation_probability(location_key): #получаем вероятности осадков из другого url
    try:
        url = f"{BASE_URL}forecasts/v1/hourly/1hour/{location_key}"
        params = {
            "apikey": API_KEY,
            "metric": "true"  # Используем метрическую систему
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None, "Precipitation data not found"

        precipitation_probability = data[0].get("PrecipitationProbability", 0)
        return precipitation_probability, None
    except requests.RequestException as e:
        return None, str(e)

def weather_analysis(weather_data): # Анализируем погодные данные
    temperature = weather_data.get("temperature_celsius")
    wind_speed = weather_data.get("wind_speed_kmh")
    humidity = weather_data.get("humidity")
    weather_text = weather_data.get("weather_text", "").lower()
    precipitation_probability = weather_data.get("PrecipitationProbability", 0)

    if temperature < -10: #понизила, иначе по России всегда слишком холодно
        return "Weather is not fine: Too cold. (Stay home and drink cocoa)."
    if temperature > 35:
        return "Weather is not fine: Too hot. (Both weather and you)"
    if wind_speed and wind_speed > 50:
        return "Whether is not fine: Strong wind (You will be carried away, darling)"
    if humidity and humidity > 80:
        return "Whether is not fine: High humidity (It is harder to breath, and not because of new Billie Eilish song coming out)"
    if precipitation_probability > 65:
        return "Weather is not fine: High chance of precipitation (Take your fancy pink umbrella)."
    if any(condition in weather_text for condition in ["rain", "snow", "storm"]):
        return "Whether is not fine: Precipitation expected (rain, snow, or storm). Too dangerous for you, darling."

    return "Weather is fine!!! Go and have fun outside!"

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/route-weather', methods=['POST'])
def route_weather():
    start_city = request.form.get('start')
    end_city = request.form.get('end')
    return render_template('result.html', start_city=start_city, end_city=end_city)


if __name__ == '__main__':
    app.run(debug=True)

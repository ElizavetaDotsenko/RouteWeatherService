import requests
from flask import Flask, render_template, request, jsonify
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc


app = Flask(__name__, static_folder='static')

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

def forecast_one(location_key): # добавила прогноз погоды на 1 день + анализ
    try:
        url = f"{BASE_URL}forecasts/v1/daily/5day/{location_key}"
        params = {"apikey": API_KEY, "metric": "true"}  # Используем метрику (градусы Цельсия)
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            return None, "Forecast data not found"

        # Берем только первый день
        day = data["DailyForecasts"][0]
        avg_temp = (day["Temperature"]["Minimum"]["Value"] + day["Temperature"]["Maximum"]["Value"]) / 2
        analysis = weather_analysis({
            # в прогнозе нет влажности и ветра, добавила среднюю температуру и описание дня и ночи
            "temperature_celsius": avg_temp,
            "humidity": None,
            "wind_speed_kmh": None,
            "weather_text": day["Day"]["IconPhrase"]
        })
        forecast = {
            "date": day["Date"],
            "avg_temp": avg_temp,
            "day_text": day["Day"]["IconPhrase"],
            "night_text": day["Night"]["IconPhrase"],
            "analysis": analysis
        }
        return forecast, None
    except requests.RequestException as e:
        return None, str(e)

@app.route('/')
def home():
    # Отображение главной страницы
    return render_template('index.html')


@app.route('/route-weather', methods=['POST']) #маршрут польщователя на сайте
def route_weather():
    start_city = request.form.get('start')
    end_city = request.form.get('end')

    if not start_city or not end_city:
        return render_template('index.html', error="Please enter both start and end cities.") #добавляю предупреждение об ошибке

    try:
        # Данные для начального города
        start_location_key, error_start = coordinates_by_city(start_city)
        #все if обрабатывают потенциальные ошибки
        if error_start:
            return render_template('index.html', error=f"Error for start city: {error_start}")

        start_weather, error_start_weather = weather_by_location(start_location_key)
        if error_start_weather:
            return render_template('index.html', error=f"Error getting weather for start city: {error_start_weather}")

        start_precipitation_probability, error_start_precipitation = precipitation_probability(start_location_key)
        if error_start_precipitation:
            return render_template('index.html', error=f"Error getting precipitation data for start city: {error_start_precipitation}")

        start_forecast, error_start_forecast = forecast_one(start_location_key)
        if error_start_forecast:
            return render_template('index.html', error=f"Error getting forecast for start city: {error_start_forecast}")

        # Данные для конечного города
        end_location_key, error_end = coordinates_by_city(end_city)
        if error_end:
            return render_template('index.html', error=f"Error for end city: {error_end}")

        end_weather, error_end_weather = weather_by_location(end_location_key)
        if error_end_weather:
            return render_template('index.html', error=f"Error getting weather for end city: {error_end_weather}")

        end_precipitation_probability, error_end_precipitation = precipitation_probability(end_location_key)
        if error_end_precipitation:
            return render_template('index.html', error=f"Error getting precipitation data for end city: {error_end_precipitation}")

        end_forecast, error_end_forecast = forecast_one(end_location_key)
        if error_end_forecast:
            return render_template('index.html', error=f"Error getting forecast for end city: {error_end_forecast}")

        # Анализ
        start_analysis = weather_analysis(start_weather)
        end_analysis = weather_analysis(end_weather)

        # Передача данных в шаблон html
        return render_template(
            'result.html',
            start_city=start_city,
            end_city=end_city,
            start_weather=start_weather,
            end_weather=end_weather,
            start_precipitation_probability=start_precipitation_probability,
            end_precipitation_probability=end_precipitation_probability,
            start_forecast=start_forecast,
            end_forecast=end_forecast,
            start_analysis=start_analysis,
            end_analysis=end_analysis
        )

    except requests.RequestException as e:
        return render_template('index.html', error="Network error or API unavailable.")
    except Exception as e:
        return render_template('index.html', error="An unexpected error occurred.")

from dash import Input, Output

# Настраиваю приложение Dash
app_dash = Dash(
    __name__,
    server=app,  # Использую Flask как сервер
    routes_pathname_prefix="/dashboard/",
    external_stylesheets=[dbc.themes.BOOTSTRAP]  # Подключаю Bootstrap
)

app_dash.layout = dbc.Container([
    html.H1("Weather Route Dashboard", className="text-center my-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Выбор маршрута", className="card-title"),
                dcc.Dropdown(
                    id="route-selector",
                    options=[
                        {"label": "Первый маршрут", "value": "route1"},
                        {"label": "Второй маршрут", "value": "route2"},
                    ],
                    placeholder="Выберите маршрут"
                )
            ])
        ]), width=4),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("График температуры", className="card-title"),
                dcc.Graph(id="temperature-graph")
            ])
        ]), width=8),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("График осадков", className="card-title"),
                dcc.Graph(id="precipitation-graph")
            ])
        ]), width=6),

        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("График ветра", className="card-title"),
                dcc.Graph(id="wind-graph")
            ])
        ]), width=6),
    ])
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)



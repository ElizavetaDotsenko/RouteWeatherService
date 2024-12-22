import requests
from flask import Flask, render_template
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

app = Flask(__name__, static_folder='static')

dash_app = Dash(
    __name__,
    server=app,
    url_base_pathname='/',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

API_KEY = "kG8ERWGHZjndfaM31iVkGlfPUqHGkq9p"
BASE_URL = "http://dataservice.accuweather.com/"

def coordinates_by_city(city):
    try:
        url = f"{BASE_URL}locations/v1/cities/search"
        params = {"apikey": API_KEY, "q": city}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None, f"City '{city}' not found."
        return data[0]["Key"], None
    except requests.RequestException as e:
        return None, f"API error: {e}"

def get_weather_data(location_key, days): #Получает данные о погоде для указанного количества дней
    try:
        url = f"{BASE_URL}forecasts/v1/daily/5day/{location_key}"
        params = {"apikey": API_KEY, "metric": "true"}
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        if not data or "DailyForecasts" not in data:
            return None, "Weather data not found"

        forecasts = []
        for day in data["DailyForecasts"][:days]:  # Берем данные только на указанный интервал
            forecasts.append({
                "date": day["Date"],
                "min_temp": day["Temperature"]["Minimum"]["Value"],
                "max_temp": day["Temperature"]["Maximum"]["Value"],
                "wind_speed": day["Day"].get("Wind", {}).get("Speed", {}).get("Value", 0),
                "precipitation_probability": max(
                    day["Day"].get("PrecipitationProbability", 0),
                    day["Night"].get("PrecipitationProbability", 0)
                ),
            })
        return forecasts, None
    except requests.RequestException as e:
        return None, str(e)

dash_app.layout = dbc.Container([
    html.H1("Weather Forecast for Route", className="text-center my-4"),
    dbc.Row([
        dbc.Col(dcc.Input(id="start-city-input", type="text", placeholder="Enter Start City", className="mb-3"), width=4),
        dbc.Col(dcc.Input(id="end-city-input", type="text", placeholder="Enter End City", className="mb-3"), width=4),
        dbc.Col(dcc.Dropdown(
            id="interval-dropdown",
            options=[
                {"label": "1 Day", "value": 1},
                {"label": "3 Days", "value": 3},
                {"label": "5 Days", "value": 5},
            ],
            value=3,  # Значение по умолчанию
            clearable=False,
            className="mb-3"
        ), width=2),
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id="metric-dropdown",
            options=[
                {"label": "Min Temperature (°C)", "value": "min_temp"},
                {"label": "Max Temperature (°C)", "value": "max_temp"},
                {"label": "Wind Speed (km/h)", "value": "wind_speed"},
                {"label": "Precipitation Probability (%)", "value": "precipitation_probability"},
            ],
            value="max_temp",
            clearable=False,
            className="mb-3"
        ), width=12),
    ]),
    dbc.Row([
        dbc.Col(html.Button("Submit", id="submit-button", className="btn btn-primary mb-3"), width=12),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="start-city-forecast"), width=6),
        dbc.Col(dcc.Graph(id="end-city-forecast"), width=6),
    ])
])

@dash_app.callback(
    [Output("start-city-forecast", "figure"), Output("end-city-forecast", "figure")],
    [Input("submit-button", "n_clicks")],
    [Input("start-city-input", "value"), Input("end-city-input", "value"),
     Input("interval-dropdown", "value"), Input("metric-dropdown", "value")]
)
def update_graphs(n_clicks, start_city, end_city, interval, selected_metric):
    if not start_city or not end_city:
        return {}, {}

    start_location_key, start_error = coordinates_by_city(start_city)
    if start_error or not start_location_key:
        return {}, {}

    end_location_key, end_error = coordinates_by_city(end_city)
    if end_error or not end_location_key:
        return {}, {}

    start_data, start_error = get_weather_data(start_location_key, interval)
    if start_error or not start_data:
        return {}, {}

    end_data, end_error = get_weather_data(end_location_key, interval)
    if end_error or not end_data:
        return {}, {}

    start_dates = [day["date"] for day in start_data]
    start_values = [day[selected_metric] for day in start_data]

    end_dates = [day["date"] for day in end_data]
    end_values = [day[selected_metric] for day in end_data]

    start_figure = {
        "data": [
            {"x": start_dates, "y": start_values, "type": "scatter", "mode": "lines+markers"}
        ],
        "layout": {"title": f"Forecast for {start_city} ({interval} days)"}
    }

    end_figure = {
        "data": [
            {"x": end_dates, "y": end_values, "type": "scatter", "mode": "lines+markers"}
        ],
        "layout": {"title": f"Forecast for {end_city} ({interval} days)"}
    }

    return start_figure, end_figure

if __name__ == '__main__':
    app.run(debug=True)
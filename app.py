import requests
from flask import Flask, render_template
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

app = Flask(__name__, static_folder='static')

dash_app = Dash(
    __name__,
    server=app,
    url_base_pathname='/',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

API_KEY = "INmBZUWrxDx1TJIUE3kOHCt5KAm7a1PG"
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

def get_weather_data(location_key, days):
    try:
        url = f"{BASE_URL}forecasts/v1/daily/5day/{location_key}"
        params = {"apikey": API_KEY, "metric": "true"}
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        if not data or "DailyForecasts" not in data:
            return None, "Weather data not found"

        forecasts = []
        for day in data["DailyForecasts"][:days]:
            has_precipitation = day["Day"].get("HasPrecipitation", False) or day["Night"].get("HasPrecipitation", False)
            forecasts.append({
                "date": day["Date"],
                "min_temp": day["Temperature"]["Minimum"]["Value"],
                "max_temp": day["Temperature"]["Maximum"]["Value"],
                "has_precipitation": int(has_precipitation)  # Преобразуем в 0 или 1 для графика
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
            value=3,
            clearable=False,
            className="mb-3"
        ), width=2),
    ]),
    dbc.Row([
        dbc.Col(html.Button("Add Stop", id="add-stop-button", className="btn btn-secondary mb-3"), width=4),
    ]),
    dbc.Row([
        dbc.Col(html.Div(id="stops-container", children=[]), width=12),  # Контейнер для промежуточных точек
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id="metric-dropdown",
            options=[
                {"label": "Min Temperature (°C)", "value": "min_temp"},
                {"label": "Max Temperature (°C)", "value": "max_temp"},
                {"label": "Has Precipitation", "value": "has_precipitation"},
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
        dbc.Col(html.Div(id="error-message", className="text-danger mb-3"), width=12),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="forecast-graph"), width=12),
    ]),
])

@dash_app.callback(
    Output("stops-container", "children"),
    Input("add-stop-button", "n_clicks"),
    State("stops-container", "children")
)
def add_stop(n_clicks, children):
    if n_clicks is None:
        return children
    new_input = dcc.Input(type="text", placeholder="Enter Stop City", className="mb-3")
    children.append(new_input)
    return children

@dash_app.callback(
    [Output("forecast-graph", "figure"), Output("error-message", "children")],
    [Input("submit-button", "n_clicks")],
    [State("start-city-input", "value"), State("end-city-input", "value"),
     State("stops-container", "children"), State("interval-dropdown", "value"), State("metric-dropdown", "value")]
)
def update_graph(n_clicks, start_city, end_city, stops, interval, selected_metric):
    if not start_city or not end_city:
        return {}, "Please enter both start and end cities."

    stop_cities = [stop.get("props", {}).get("value", "") for stop in stops if stop.get("props", {}).get("value", "")]
    all_cities = [start_city] + stop_cities + [end_city]

    all_data = []
    for city in all_cities:
        location_key, error = coordinates_by_city(city)
        if error or not location_key:
            return {}, f"Error with city {city}: {error}"

        city_data, error = get_weather_data(location_key, interval)
        if error or not city_data:
            return {}, f"Error fetching data for city {city}: {error}"

        all_data.append((city, city_data))

    figure = {
        "data": [],
        "layout": {"title": "Weather Forecast for Route", "xaxis": {"title": "Date"}, "yaxis": {"title": selected_metric}}
    }

    for city, data in all_data:
        dates = [day["date"] for day in data]
        values = [day[selected_metric] for day in data]
        figure["data"].append({"x": dates, "y": values, "type": "scatter", "mode": "lines+markers", "name": city})

    return figure, ""

if __name__ == '__main__':
    app.run(debug=True)

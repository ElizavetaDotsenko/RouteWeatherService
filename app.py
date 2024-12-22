import requests
from flask import Flask
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

app = Flask(__name__, static_folder='static')

dash_app = Dash(
    __name__,
    server=app,
    url_base_pathname='/',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

API_KEY = "0ETBDN5MCtwn1PGcDvxQowlPg5s126d2"
BASE_URL = "http://dataservice.accuweather.com/"


def coordinates_by_city(city):
    try:
        url = f"{BASE_URL}locations/v1/cities/search"
        params = {"apikey": API_KEY, "q": city}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None, None, f"City '{city}' not found."

        location_key = data[0]["Key"]
        lat = data[0]["GeoPosition"]["Latitude"]
        lon = data[0]["GeoPosition"]["Longitude"]
        return location_key, (lat, lon), None
    except requests.RequestException as e:
        return None, None, f"API error: {e}"


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
            has_precipitation = (
                    day["Day"].get("HasPrecipitation", False) or
                    day["Night"].get("HasPrecipitation", False)
            )
            forecasts.append({
                "date": day["Date"],
                "min_temp": day["Temperature"]["Minimum"]["Value"],
                "max_temp": day["Temperature"]["Maximum"]["Value"],
                "has_precipitation": int(has_precipitation)
            })
        return forecasts, None
    except requests.RequestException as e:
        return None, str(e)

dash_app.layout = dbc.Container([
    html.H1("Weather Forecast for Route", className="text-center my-4"),

    dbc.Row([
        dbc.Col(
            dcc.Input(
                id="start-city-input",
                type="text",
                placeholder="Enter Start City",
                className="mb-3",
                debounce=True
            ), width=4
        ),
        dbc.Col(
            dcc.Input(
                id="end-city-input",
                type="text",
                placeholder="Enter End City",
                className="mb-3",
                debounce=True
            ), width=4
        ),
        dbc.Col(
            dcc.Dropdown(
                id="interval-dropdown",
                options=[
                    {"label": "1 Day", "value": 1},
                    {"label": "3 Days", "value": 3},
                    {"label": "5 Days", "value": 5},
                ],
                value=3,
                clearable=False,
                className="mb-3"
            ), width=2
        ),
    ]),

    dbc.Row([
        dbc.Col(
            html.Button(
                "Add Stop",
                id="add-stop-button",
                className="btn btn-secondary mb-3"
            ), width=4
        ),
    ]),

    dbc.Row([
        dbc.Col(html.Div(id="stops-container", children=[]), width=12),
    ]),

    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id="metric-dropdown",
                options=[
                    {"label": "Min Temperature (°C)", "value": "min_temp"},
                    {"label": "Max Temperature (°C)", "value": "max_temp"},
                    {"label": "Has Precipitation", "value": "has_precipitation"},
                ],
                value="max_temp",
                clearable=False,
                className="mb-3"
            ), width=12
        ),
    ]),

    dbc.Row([
        dbc.Col(
            html.Div(id="error-message", className="text-danger mb-3"),
            width=12
        ),
    ]),

    dbc.Row([
        dbc.Col(
            dcc.Graph(id="forecast-graph"),
            width=12
        ),
    ]),

    dbc.Row([
        dbc.Col(
            dcc.Graph(id="map-graph"),
            width=12
        ),
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
    new_input = dcc.Input(
        type="text",
        placeholder="Enter Stop City",
        className="mb-3",
        debounce=True
    )
    children.append(new_input)
    return children

@dash_app.callback(
    [
        Output("error-message", "children"),
        Output("forecast-graph", "figure"),
        Output("map-graph", "figure")
    ],
    [
        Input("start-city-input", "value"),
        Input("end-city-input", "value"),
        Input("stops-container", "children"),
        Input("interval-dropdown", "value"),
        Input("metric-dropdown", "value")
    ]
)
def update_all(start_city, end_city, stops_children, interval, selected_metric):
    empty_figure = {
        "data": [],
        "layout": {"title": "No data available"}
    }

    if not start_city or not end_city:
        return ("Please enter both start and end cities.", empty_figure, empty_figure)


    stop_cities = []
    if stops_children:
        stop_cities = [
            c.get("props", {}).get("value", "")
            for c in stops_children
            if c.get("props", {}).get("value", "")
        ]

    all_cities = [start_city] + stop_cities + [end_city]

    route_data = []
    for city in all_cities:
        location_key, coords, error = coordinates_by_city(city)
        if error or not location_key:
            return (f"Error with city {city}: {error}", empty_figure, empty_figure)

        lat, lon = coords
        city_data, error = get_weather_data(location_key, interval)
        if error or not city_data:
            return (f"Error fetching data for city {city}: {error}", empty_figure, empty_figure)

        route_data.append({
            "city": city,
            "forecast": city_data,
            "lat": lat,
            "lon": lon
        })


    forecast_traces = []
    for entry in route_data:
        city_name = entry["city"]
        forecast = entry["forecast"]
        dates = [day["date"] for day in forecast]
        values = [day[selected_metric] for day in forecast]

        forecast_traces.append({
            "x": dates,
            "y": values,
            "type": "scatter",
            "mode": "lines+markers",
            "name": city_name
        })

    forecast_fig = {
        "data": forecast_traces,
        "layout": {
            "title": "Weather Forecast for Route",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": selected_metric}
        }
    }

    lons, lats, hover_texts = [], [], []
    for entry in route_data:
        city_name = entry["city"]
        lat = entry["lat"]
        lon = entry["lon"]
        forecast = entry["forecast"]

        if forecast:
            first_day = forecast[0]
            min_temp = first_day["min_temp"]
            max_temp = first_day["max_temp"]
            hover_txt = (
                f"<b>{city_name}</b><br>"
                f"Min: {min_temp}°C<br>"
                f"Max: {max_temp}°C"
            )
        else:
            hover_txt = f"<b>{city_name}</b><br>No data"

        lats.append(lat)
        lons.append(lon)
        hover_texts.append(hover_txt)

    map_data = [
        go.Scattergeo(
            lon=lons,
            lat=lats,
            text=hover_texts,
            mode="markers",
            marker=dict(
                size=8,
                symbol="circle",
                color="blue",
                line=dict(width=1, color="white")
            ),
            hoverinfo="text"
        )
    ]
    map_layout = go.Layout(
        title="Cities on Map",
        geo=dict(
            scope="world",
            projection=dict(type="natural earth"),
            showland=True,
            landcolor="rgb(217, 217, 217)",
            subunitwidth=1,
            countrywidth=1,
            showlakes=True,
            lakecolor="rgb(255, 255, 255)",
            showcoastlines=True,
            coastlinecolor="rgb(204, 204, 204)",
            countrycolor="rgb(204, 204, 204)"
        )
    )
    map_fig = go.Figure(data=map_data, layout=map_layout)

    return ("", forecast_fig, map_fig)


if __name__ == '__main__':
    app.run(debug=True)


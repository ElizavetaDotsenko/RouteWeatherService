from dash import Dash, html
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Макет
app.layout = dbc.Container(
    [
        html.H1("Weather Route Service Dashboard", className="text-center my-4"),
        html.P("Visualize and plan your travel routes with detailed weather data.", className="text-center"),
    ],
    fluid=True,
)

if __name__ == "__main__":
    app.run_server(debug=True)
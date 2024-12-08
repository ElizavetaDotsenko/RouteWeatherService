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

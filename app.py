from flask import Flask, render_template, request

app = Flask(__name__)

API_KEY = "RUHsTC8pTBp0L74bBGtnFV86G77yGCGZ"
BASE_URL = "http://dataservice.accuweather.com/"

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
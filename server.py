from flask import Flask, request, render_template
from main import start

app = Flask(__name__)


@app.route('/exchange_currency', methods=['POST'])
def exchange_currency():
    data = request.get_json()
    amount = data.get('amount')
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')
    exchange_rate = get_exchange_rate(from_currency, to_currency)

    if exchange_rate:
        converted_amount = amount * exchange_rate
        return {'converted_amount': converted_amount}
    else:
        return {'error': 'Invalid currency exchange rate'}


def get_exchange_rate(from_currency, to_currency):
    # Логика получения курса обмена валюты
    return 5


@app.route('/')
def index():
    start()
    return render_template('exchange_currency.html')


if __name__ == '__main__':
    app.run(debug=True)

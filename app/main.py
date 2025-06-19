from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os, threading, ccxt
from app.trade_logic import run_trade_logic

load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
API_PASSPHRASE = os.getenv("BITGET_API_PASSPHRASE")

bitget = ccxt.bitget({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'password': API_PASSPHRASE,
    'enableRateLimit': True,
    'options': { 'defaultType': 'swap' }
})

app = Flask(__name__)
capital = [100.0]
position_state = {"side": None, "entry_price": 0, "amount": 0, "stop_loss": 0, "step": 0}

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📱 웹훅 수신:", data)
    try:
        signal = data.get('signal')
        symbol = data.get('symbol', 'ETH/USDT:USDT')
        if signal in ['buy', 'sell']:
            threading.Thread(target=run_trade_logic, args=(bitget, symbol, signal, capital, position_state)).start()
            return jsonify({'status': 'success', 'message': f'{signal} 신호 처리 중'})
        else:
            return jsonify({'status': 'ignored', 'message': '유효하지 않은 신호'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    print("✅ Flask 서버 실행 중... 포트 5000")
    app.run(host='0.0.0.0', port=5000)
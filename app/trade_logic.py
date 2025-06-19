import time
import threading
from .utils import send_telegram, log_trade

def run_trade_logic(bitget, symbol, signal, capital, position_state):
    try:
        if capital[0] >= 1000:
            send_telegram("💰 자본 1000 USDT 도달 → 자본 리셋 (100 USDT 유지)")
            capital[0] = 100.0

        current_side, entry_price, size = get_position(bitget, symbol)
        if current_side:
            print("📌 기존 포지션 존재 → 진입 보류")
            return

        order_amount = round(capital[0] * 0.98, 2)
        side_text = "롱" if signal == "buy" else "숏"
        order_result = place_order(bitget, symbol, signal, order_amount)
        if not order_result:
            return

        price = order_result['average']
        stop_loss = price * (1 - 0.005 if signal == "buy" else 1 + 0.005)
        position_state.update({
            "side": signal, "entry_price": price, "amount": order_amount,
            "stop_loss": stop_loss, "step": 0
        })
        send_telegram(f"🚀 {side_text} 진입 @ {price:.2f}, 금액: {order_amount} USDT")
        log_trade("entry", signal, symbol, price, order_amount)

        while True:
            time.sleep(10)
            last_price = bitget.fetch_ticker(symbol)['last']
            if position_state['side'] == "buy":
                if last_price <= stop_loss:
                    bitget.create_market_order(symbol, 'sell', order_amount)
                    send_telegram("⚠️ 손절 실행")
                    capital[0] -= order_amount * 0.005
                    log_trade("stop_loss", "buy", symbol, last_price, order_amount)
                    break
                elif last_price >= price * 1.005 and position_state['step'] == 0:
                    take = round(order_amount * 0.3, 2)
                    bitget.create_market_order(symbol, 'sell', take)
                    stop_loss = price * 1.001
                    position_state['step'] = 1
                    capital[0] += take * 0.005
                    send_telegram("✅ 1차 익절: +0.5% (30%)")
                    log_trade("take1", "buy", symbol, last_price, take)
                elif last_price >= price * 1.011 and position_state['step'] == 1:
                    take = round(order_amount * 0.3, 2)
                    bitget.create_market_order(symbol, 'sell', take)
                    position_state['step'] = 2
                    capital[0] += take * 0.011
                    send_telegram("✅ 2차 익절: +1.1% (30%)")
                    log_trade("take2", "buy", symbol, last_price, take)
            elif position_state['side'] == "sell":
                if last_price >= stop_loss:
                    bitget.create_market_order(symbol, 'buy', order_amount)
                    send_telegram("⚠️ 손절 실행")
                    capital[0] -= order_amount * 0.005
                    log_trade("stop_loss", "sell", symbol, last_price, order_amount)
                    break
    except Exception as e:
        send_telegram(f"❌ 오류 발생: {e}")
        try:
            if position_state['side'] == "buy":
                bitget.create_market_order(symbol, 'sell', position_state['amount'])
            elif position_state['side'] == "sell":
                bitget.create_market_order(symbol, 'buy', position_state['amount'])
        except:
            pass
        position_state.update({"side": None, "entry_price": 0, "amount": 0, "stop_loss": 0, "step": 0})


def get_position(bitget, symbol):
    try:
        positions = bitget.fetch_positions([symbol])
        for p in positions:
            if p['symbol'] == symbol and float(p['contracts']) > 0:
                return p['side'], float(p['entryPrice']), float(p['contracts'])
    except:
        pass
    return None, 0, 0

def place_order(bitget, symbol, side, amount):
    try:
        order_side = 'buy' if side == 'buy' else 'sell'
        return bitget.create_market_order(symbol, order_side, amount)
    except Exception as e:
        send_telegram(f"❌ 주문 실패: {e}")
        return None
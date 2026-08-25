import ccxt
import pandas as pd
import requests
from datetime import datetime, timezone

BOT_TOKEN = "8626042409:AAHElsiJD8_Jk9R7r5VHUj8fPjcl8Meacp4"
CHAT_ID = "706694019"

def format_utc_time(ts_ms):
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%H:%M UTC")

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram status: {response.status_code}")
    except Exception as e:
        print(f"Telegram error: {e}")

def check_volume_spike():
    exchange = ccxt.delta()
    
    # Delta Exchange na main High-Volume Contracts (TradingView ETHUSD.P / BTCUSD.P)
    symbols = ['BTC/USD:BTC', 'ETH/USD:USD']
    timeframe = '5m'
    
    for symbol in symbols:
        try:
            # 100 candles fetch karvi accurate SMA mate
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # True 20 SMA: Pheli 20 candles no average (Current closed candle sivay)
            df['vol_sma_20'] = df['volume'].shift(1).rolling(window=20).mean()
            
            # iloc[-2] = Recently closed candle
            closed_candle = df.iloc[-2]
            vol_sma20 = closed_candle['vol_sma_20']
            latest_vol = closed_candle['volume']
            
            # Clean symbol name (BTC ya ETH)
            clean_sym = symbol.split('/')[0]
            
            # Calculation of exact multiplier
            if pd.isna(vol_sma20) or vol_sma20 == 0:
                continue
                
            ratio = latest_vol / vol_sma20
            
            # Condition: Jo volume 20 SMA karta 2x (2.0) ke vadhare hoy to j trigger thase
            if ratio >= 2.0:
                candle_type = "🟢 Bullish" if closed_candle['close'] >= closed_candle['open'] else "🔴 Bearish"
                latest_time = format_utc_time(closed_candle['timestamp'])
                
                # Previous 3 closed candles
                p1, p2, p3 = df.iloc[-3], df.iloc[-4], df.iloc[-5]
                t1, t2, t3 = format_utc_time(p1['timestamp']), format_utc_time(p2['timestamp']), format_utc_time(p3['timestamp'])
                
                msg = (
                    f"🚨 *Delta 5M Volume Alert ({clean_sym})*\n\n"
                    f"📊 *Triggered Candle (Closed):*\n"
                    f"• Time: `{latest_time}`\n"
                    f"• Direction: {candle_type}\n"
                    f"• Close Price: `${closed_candle['close']}`\n"
                    f"• Volume: `{latest_vol:,.2f}`\n"
                    f"• 20 SMA Vol: `{vol_sma20:,.2f}`\n"
                    f"• Exact Spike: `{ratio:.2f}x` 🔥\n\n"
                    f"📜 *Previous 3 Candles:*\n"
                    f"1️⃣ `{t1}`: Price `${p1['close']}` | Vol `{p1['volume']:,.2f}`\n"
                    f"2️⃣ `{t2}`: Price `${p2['close']}` | Vol `{p2['volume']:,.2f}`\n"
                    f"3️⃣ `{t3}`: Price `${p3['close']}` | Vol `{p3['volume']:,.2f}`"
                )
                
                send_telegram_alert(msg)
                print(f"Alert sent for {clean_sym} (Ratio: {ratio:.2f}x)")
            else:
                print(f"{clean_sym}: No spike (Vol: {latest_vol:,.0f} | SMA: {vol_sma20:,.0f} | Ratio: {ratio:.2f}x)")
                
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

if __name__ == "__main__":
    check_volume_spike()

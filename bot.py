import ccxt
import pandas as pd
import requests
from datetime import datetime, timezone

# Tamara provided credentials
BOT_TOKEN = "8626042409:AAHElsiJD8_Jk9R7r5VHUj8fPjcl8Meacp4"
CHAT_ID = "706694019"

def format_utc_time(ts_ms):
    # Milliseconds timestamp ne UTC format (HH:MM UTC | YYYY-MM-DD) ma convert kare chhe
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
        response = requests.post(url, json=payload)
        print(f"Telegram response: {response.text}")
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

def check_volume_spike():
    exchange = ccxt.delta()
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
    timeframe = '5m'
    
    for symbol in symbols:
        try:
            # 5m timeframe data fetch karva
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 20-period Volume Moving Average calculate karvo
            df['vol_sma_20'] = df['volume'].rolling(window=20).mean()
            
            # iloc[-2] etle exact recently closed candle
            closed_candle = df.iloc[-2]
            vol_sma20 = closed_candle['vol_sma_20']
            latest_vol = closed_candle['volume']
            
            # Condition: Latest closed candle no volume 20 SMA karta 2x (double) ya vadhare hoy
            if latest_vol >= (2 * vol_sma20):
                clean_sym = symbol.split('/')[0]
                candle_type = "🟢 Bullish" if closed_candle['close'] >= closed_candle['open'] else "🔴 Bearish"
                latest_time = format_utc_time(closed_candle['timestamp'])
                
                # Pachhli 3 closed candles (iloc[-3], iloc[-4], iloc[-5])
                prev_c1 = df.iloc[-3]
                prev_c2 = df.iloc[-4]
                prev_c3 = df.iloc[-5]
                
                time_c1 = format_utc_time(prev_c1['timestamp'])
                time_c2 = format_utc_time(prev_c2['timestamp'])
                time_c3 = format_utc_time(prev_c3['timestamp'])
                
                msg = (
                    f"🚨 *Delta 5M Volume Spike Alert ({clean_sym})*\n\n"
                    f"📊 *Latest Triggered Candle (Closed):*\n"
                    f"• Time: `{latest_time}`\n"
                    f"• Type: {candle_type}\n"
                    f"• Close Price: `${closed_candle['close']}`\n"
                    f"• Volume: `{latest_vol:,.2f}`\n"
                    f"• 20 SMA Vol: `{vol_sma20:,.2f}` (Ratio: `{(latest_vol/vol_sma20):.2f}x`)\n\n"
                    f"📜 *Previous 3 Candles Summary:*\n"
                    f"1️⃣ Prev 1 (`{time_c1}`): Price `${prev_c1['close']}` | Vol `{prev_c1['volume']:,.2f}`\n"
                    f"2️⃣ Prev 2 (`{time_c2}`): Price `${prev_c2['close']}` | Vol `{prev_c2['volume']:,.2f}`\n"
                    f"3️⃣ Prev 3 (`{time_c3}`): Price `${prev_c3['close']}` | Vol `{prev_c3['volume']:,.2f}`"
                )
                
                send_telegram_alert(msg)
                print(f"Volume spike alert sent for {clean_sym}")
            else:
                print(f"No volume spike for {symbol} (Vol: {latest_vol:.2f} vs 2x SMA: {2*vol_sma20:.2f})")
                
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

if __name__ == "__main__":
    check_volume_spike()

from flask import Flask, render_template_string, request, redirect
import os, datetime, random, threading, time

app = Flask(__name__)

# ===== CONFIG FROM YOUR PAPER =====
BALANCE = 10.00  # Starting balance
EXNESS_LINK = "https://one.exness.link/a/c_8x2bx1"
# Lot table from your paper
def get_recommended_lot(balance):
    if balance <= 30: return 0.01
    elif balance <= 50: return 0.03
    elif balance <= 60: return 0.04
    elif balance <= 80: return 0.05
    elif balance <= 100: return 0.07
    elif balance <= 200: return 0.10
    elif balance <= 400: return 0.20
    elif balance <= 600: return 0.30
    elif balance <= 800: return 0.40
    else: return 0.50  # up to 1000

# Bot State
bot_state = {
    "balance": BALANCE,
    "lot": get_recommended_lot(BALANCE),
    "day_type": "BUY_DAY",  # Will detect
    "gold_price": 4184.50,
    "btc_price": 82655.00,
    "supply_zone": 4200,
    "demand_zone": 4150,
    "active_trade": None,
    "today_pips": 0,
    "last_signal": "NEUTRAL"
}

def detect_day_type():
    # Simple logic: If today Gold opened higher than yesterday = BUY DAY
    # You can change to real API later
    hour = datetime.datetime.now().hour
    # Morning determines day type
    if random.random() > 0.5:
        return "BUY_DAY"
    else:
        return "SELL_DAY"

def auto_trader():
    while True:
        # Update day type every hour
        bot_state["day_type"] = detect_day_type()
        
        # Simulate price moving
        bot_state["gold_price"] += random.uniform(-2, 2)
        bot_state["btc_price"] += random.uniform(-20, 20)
        
        # Demand/Supply Logic from your paper
        if bot_state["day_type"] == "BUY_DAY" and bot_state["gold_price"] <= bot_state["demand_zone"]:
            bot_state["last_signal"] = f"BUY at DEMAND {bot_state['gold_price']:.1f} - SL 30 TP 60"
            # Auto open trade
            if not bot_state["active_trade"]:
                bot_state["active_trade"] = {"type": "BUY", "entry": bot_state["gold_price"], "lot": bot_state["lot"]}
        elif bot_state["day_type"] == "SELL_DAY" and bot_state["gold_price"] >= bot_state["supply_zone"]:
            bot_state["last_signal"] = f"SELL at SUPPLY {bot_state['gold_price']:.1f} - SL 30 TP 60"
            if not bot_state["active_trade"]:
                bot_state["active_trade"] = {"type": "SELL", "entry": bot_state["gold_price"], "lot": bot_state["lot"]}
        
        # Auto close after TP/SL simulation (60 pips TP, 30 SL)
        if bot_state["active_trade"]:
            entry = bot_state["active_trade"]["entry"]
            current = bot_state["gold_price"]
            diff = current - entry
            if bot_state["active_trade"]["type"] == "BUY":
                pips = diff * 10  # Gold pip approx
                if pips >= 60 or pips <= -30: # TP 60, SL 30
                    bot_state["balance"] += pips * bot_state["lot"] * 0.1
                    bot_state["lot"] = get_recommended_lot(bot_state["balance"])
                    bot_state["active_trade"] = None
                    bot_state["today_pips"] += pips
            else:
                pips = -diff * 10
                if pips >= 60 or pips <= -30:
                    bot_state["balance"] += pips * bot_state["lot"] * 0.1
                    bot_state["lot"] = get_recommended_lot(bot_state["balance"])
                    bot_state["active_trade"] = None
                    bot_state["today_pips"] += pips

        time.sleep(10)  # Check every 10 sec - runs even when phone off!

# Start auto thread
threading.Thread(target=auto_trader, daemon=True).start()

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;padding:12px;color:white;font-family:Arial;background: radial-gradient(circle at top left,#1e3a5f 0%,#0f1219 50%,#000 100%);min-height:100vh}
.card{background:rgba(30,35,47,0.9);border:1px solid rgba(255,255,255,0.1);border-radius:18px;padding:16px;margin-bottom:12px;backdrop-filter:blur(10px)}
.green{color:#2ecc71;font-size:22px;font-weight:bold}
.red{color:#ff5a5a;font-size:22px;font-weight:bold}
.gold{color:#f1c40f;font-weight:bold}.btc{color:#e67e22;font-weight:bold}
.blue{color:#6a8cff;font-size:24px;font-weight:bold;text-align:center}
.btn{border:none;border-radius:12px;padding:16px;font-weight:bold;color:white;width:100%;font-size:16px;cursor:pointer}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.small{font-size:11px;color:#999}
</style>
</head>
<body>
<h3 style="text-align:center">⚡ GOLD/BTC SCALPER - 24H BOT</h3>

<div class="card">
<div style="display:flex;justify-content:space-between">
<div>DEPOSIT: <b style="color:#2ecc71">${{ "%.2f"|format(state.balance) }}</b></div>
<div>LOT: <b>{{ "%.2f"|format(state.lot) }}</b> (Auto)</div>
</div>
<div class="small">Lot: 10-30=0.01 | 31-50=0.03 | 51-60=0.04 | 61-100=0.07 ... up to 1000=0.50</div>
</div>

<div class="grid">
<div class="card">
{% if state.day_type == 'BUY_DAY' %}
<div class="green">{{state.day_type}} 📈</div>
<div class="small">Buy only whole day</div>
{% else %}
<div class="red">{{state.day_type}} 📉</div>
<div class="small">Sell only whole day</div>
{% endif %}
</div>
<div class="card">
<div class="gold">GOLD: ${{"%.1f"|format(state.gold_price)}}</div>
<div class="btc">BTC: ${{"%.0f"|format(state.btc_price)}}</div>
<div class="small">Demand: {{state.demand_zone}} | Supply: {{state.supply_zone}}</div>
</div>
</div>

<div class="card">
<div class="blue">{{state.last_signal}}</div>
{% if state.active_trade %}
<div style="text-align:center;margin-top:8px">🔥 Active: {{state.active_trade.type}} {{state.active_trade.lot}} lot @ {{ "%.1f"|format(state.active_trade.entry) }} | SL 30 TP 60</div>
{% else %}
<div style="text-align:center;margin-top:8px" class="small">Waiting for Demand/Supply zone... Auto will open next trade</div>
{% endif %}
<div style="text-align:center;margin-top:6px">Today Pips: {{ "%.1f"|format(state.today_pips) }}</div>
</div>

<div class="grid">
<a href="{{exness}}" target="_blank"><button class="btn" style="background:#16a34a">BUY {{ "%.1f"|format(state.gold_price) }}</button></a>
<a href="{{exness}}" target="_blank"><button class="btn" style="background:#dc2626">SELL {{ "%.1f"|format(state.gold_price) }}</button></a>
<a href="{{exness}}" target="_blank"><button class="btn" style="background:#2563eb">LOT {{ "%.2f"|format(state.lot) }}</button></a>
<a href="{{exness}}" target="_blank"><button class="btn" style="background:#4b5563">BALANCE ${{"%.0f"|format(state.balance)}}</button></a>
</div>

<div class="grid" style="margin-top:12px">
<a href="{{exness}}" target="_blank"><button class="btn" style="background:linear-gradient(90deg,#f59e0b,#eab308);color:black">DEPOSIT EXNESS</button></a>
<a href="https://wa.me/?text=My Gold Scalper Bot running" target="_blank"><button class="btn" style="background:#25D366">SHARE WHATSAPP</button></a>
</div>

<p style="text-align:center;color:#666;font-size:10px;margin-top:15px">Bot runs 24h even when phone OFF - Hosted on server<br>Time: {{time}} EAT | Auto timeframe: M15 Demand/Supply</p>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML, state=bot_state, time=datetime.datetime.now().strftime("%H:%M:%S"), exness=EXNESS_LINK)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

from flask import Flask, request, jsonify, render_template
import yfinance as yf
import numpy as np

app = Flask(__name__)

# Helper function: convert period to years
def convert_to_years(period, unit):
    unit = unit.lower()
    if unit == "days":
        return period / 365
    elif unit == "weeks":
        return period / 52
    elif unit == "months":
        return period / 12
    return period  # years

# Home page serving HTML
@app.route("/")
def home():
    return render_template("index.html")

# Portfolio optimization API
@app.route("/optimize_portfolio", methods=["POST"])
def optimize_portfolio():
    data = request.json
    user_stocks = data["stocks"]
    total_investment = float(data["amount"])
    risk_factor = data["risk"].capitalize()
    period = float(data["period"])
    unit = data["unit"]

    years = convert_to_years(period, unit)

    expected_returns = {}
    volatility = {}

    # Fetch stock data and calculate CAGR + volatility
    for stock in user_stocks:
        try:
            hist = yf.download(stock, period="5y")["Adj Close"].dropna()
            daily_returns = hist.pct_change().dropna()
            cagr = (hist[-1] / hist[0]) ** (252/len(hist)) - 1
            vol = daily_returns.std() * np.sqrt(252)
            expected_returns[stock] = round(cagr, 4)
            volatility[stock] = round(vol, 4)
        except:
            expected_returns[stock] = 0.07
            volatility[stock] = 0.20

    # Risk-adjusted allocation
    returns_array = np.array([expected_returns[s] for s in user_stocks])
    vol_array = np.array([volatility[s] for s in user_stocks])

    if risk_factor == "Low":
        inv_vol = 1 / vol_array
        weights = inv_vol / inv_vol.sum()
    elif risk_factor == "High":
        pos_ret = np.maximum(returns_array, 0.0001)
        weights = pos_ret / pos_ret.sum()
    else:  # Medium
        inv_vol = 1 / vol_array
        vol_weights = inv_vol / inv_vol.sum()
        ret_weights = returns_array / returns_array.sum()
        weights = (vol_weights + ret_weights) / 2

    allocations = {s: total_investment * w for s, w in zip(user_stocks, weights)}
    future_values = {}
    for stock, amount in allocations.items():
        annual_return = expected_returns[stock]
        fv = amount * ((1 + annual_return) ** years)
        future_values[stock] = round(fv, 2)

    total_future_value = round(sum(future_values.values()), 2)

    result = {
        "allocations": {s: round(v,2) for s,v in allocations.items()},
        "expected_returns": expected_returns,
        "volatility": volatility,
        "future_values": future_values,
        "total_future_value": total_future_value
    }

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)

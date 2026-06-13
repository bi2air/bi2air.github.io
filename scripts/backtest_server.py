from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os
import requests
import plotly.graph_objects as go
import plotly.io as pio

app = Flask(__name__)
CORS(app) # Allow Jekyll to talk to Flask

# --- CONFIG (Synchronized with inference scripts) ---
MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'
MAX_HORIZON = 72
WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation']

CITY_MAP = {
    "hanoi": {
        "coords": (21.0245, 105.8412),
        "data_file": 'data/external/processed/hanoi/public-air-quality/hourly_canonical_records.csv',
        "model_weights": f'{MODELS_DIR}/t72_delta_skip_best.pt',
        "train_script": "tmp/air-quality-analysis-upstream/scripts/train_t72_delta_skip.py",
        "maes": {1: 7.58, 6: 13.20, 12: 14.27, 24: 14.24, 48: 15.17, 72: 16.09}
    },
    "hcmc": {
        "coords": (10.7834, 106.7006),
        "data_file": 'tmp/air-quality-analysis-upstream/data/external/processed/ho-chi-minh-city/public-air-quality/hourly_canonical_records.csv',
        "model_weights": f'{MODELS_DIR}/hcmc_t72_delta_skip_best.pt',
        "train_script": "tmp/air-quality-analysis-upstream/scripts/train_hcmc_t72_delta_skip.py",
        "maes": {1: 8.44, 6: 15.71, 12: 18.59, 24: 20.99, 48: 23.90, 72: 24.47}
    }
}

class DeltaSkipMLP(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DeltaSkipMLP, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )
    def forward(self, x, current_val):
        delta = self.net(x)
        return current_val + delta

@app.route('/predict', methods=['GET'])
def predict():
    site = request.args.get('site', 'hanoi')
    date_str = request.args.get('date') # YYYY-MM-DD
    hour = int(request.args.get('hour', 1))
    
    cfg = CITY_MAP[site]
    
    # 1. Load Data
    df = pd.read_csv(cfg['data_file'])
    df['time'] = pd.to_datetime(df['observation_hour_local']).dt.tz_localize(None)
    df = df.groupby('time')['pm25_ugm3'].mean().reset_index()
    df = df.sort_values('time').set_index('time').resample('1h').mean()
    df['pm25_ugm3'] = df['pm25_ugm3'].interpolate(limit=3)
    df = df.reset_index()

    if date_str:
        t0 = pd.to_datetime(f"{date_str} {hour:02d}:00")
    else:
        t0 = df['time'].max() # Live mode if no date provided

    # History & Unseen
    history_24h = df[df['time'] <= t0].tail(24).copy()
    if len(history_24h) < 24:
        return jsonify({"error": f"Insufficient history before {t0}"}), 400
        
    past_pm25 = history_24h['pm25_ugm3'].values
    current_val = past_pm25[-1]
    unseen_72h = df[(df['time'] > t0) & (df['time'] <= t0 + pd.Timedelta(hours=MAX_HORIZON))].copy()
    
    # 2. Weather
    params = {
        "latitude": cfg['coords'][0], "longitude": cfg['coords'][1],
        "start_date": t0.strftime('%Y-%m-%d'),
        "end_date": (t0 + pd.Timedelta(days=4)).strftime('%Y-%m-%d'),
        "hourly": ",".join(WEATHER_COLS), "timezone": "Asia/Ho_Chi_Minh", "wind_speed_unit": "kmh"
    }
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params).json()
    w_df = pd.DataFrame(r['hourly'])
    w_df['time'] = pd.to_datetime(w_df['time']).dt.tz_localize(None)
    future_w = w_df[(w_df['time'] > t0) & (w_df['time'] <= t0 + pd.Timedelta(hours=MAX_HORIZON))].copy()
    
    future_w['sin_hour'] = np.sin(2 * np.pi * future_w['time'].dt.hour / 24)
    future_w['cos_hour'] = np.cos(2 * np.pi * future_w['time'].dt.hour / 24)
    future_w['sin_month'] = np.sin(2 * np.pi * future_w['time'].dt.month / 12)
    future_w['cos_month'] = np.cos(2 * np.pi * future_w['time'].dt.month / 12)
    weather_inputs = future_w[WEATHER_COLS + ['sin_hour', 'cos_hour', 'sin_month', 'cos_month']].values.flatten()
    
    if len(weather_inputs) < MAX_HORIZON * 10:
        weather_inputs = np.pad(weather_inputs, (0, MAX_HORIZON*10 - len(weather_inputs)))
        
    # 3. Predict
    mom_inputs = np.array([past_pm25[-1]-past_pm25[-2], past_pm25[-1]-past_pm25[-3], past_pm25[-1]-past_pm25[-4], past_pm25[-1]-past_pm25[-7]])
    X_new = np.concatenate([past_pm25, weather_inputs, mom_inputs]).reshape(1, -1)
    
    # Scaler
    import importlib.util
    spec = importlib.util.spec_from_file_location("tm", cfg['train_script'])
    tm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tm)
    X_train_s, _, _, _, _, _, scaler_x = tm.prep_data()
    
    model = DeltaSkipMLP(X_new.shape[1], MAX_HORIZON)
    model.load_state_dict(torch.load(cfg['model_weights'], map_location='cpu', weights_only=True))
    model.eval()
    
    with torch.no_grad():
        X_t = torch.FloatTensor(scaler_x.transform(X_new))
        C_t = torch.FloatTensor([[current_val]])
        y_pred = model(X_t, C_t).numpy()[0]
        
    # 4. Plotly Data
    forecast_times = [t0 + pd.Timedelta(hours=i) for i in range(1, MAX_HORIZON + 1)]
    all_h = np.arange(1, MAX_HORIZON + 1)
    interp_mae = np.interp(all_h, list(cfg['maes'].keys()), list(cfg['maes'].values()))
    
    fig = go.Figure()
    # Uncertainty
    fig.add_trace(go.Scatter(
        x=forecast_times + forecast_times[::-1], y=(y_pred + interp_mae).tolist() + (np.maximum(0, y_pred - interp_mae)).tolist()[::-1],
        fill='toself', fillcolor='rgba(128, 128, 128, 0.2)', line=dict(color='rgba(255,255,255,0)'), name='Expected Range (±1 MAE)'
    ))
    # Forecast
    fig.add_trace(go.Scatter(x=forecast_times, y=y_pred.tolist(), mode='lines', name='Forecast (Central)', line=dict(color='gray', width=3)))
    # Actuals
    fig.add_trace(go.Scatter(x=unseen_72h['time'].tolist(), y=unseen_72h['pm25_ugm3'].tolist(), mode='lines+markers', name='Actual Measurements', line=dict(color='blue', width=2), marker=dict(size=6, symbol='x')))
    
    fig.update_layout(
        title=f'{site.upper()} 72h Forecast/Backtest - Origin: {t0}', template='plotly_white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=80, b=0), height=500
    )
    
    return pio.to_json(fig)

if __name__ == '__main__':
    app.run(port=5000, debug=True)

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import os
import pickle
import requests
import argparse
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler

# --- CONFIG ---
MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'
MAX_HORIZON = 72
WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation']

# City Configs
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

def run_backtest(site, t0):
    cfg = CITY_MAP[site]
    print(f"--- Backtesting {site.upper()} starting at {t0} ---")
    
    # 1. Load Measurements
    df = pd.read_csv(cfg['data_file'])
    df['time'] = pd.to_datetime(df['observation_hour_local']).dt.tz_localize(None)
    df = df.groupby('time')['pm25_ugm3'].mean().reset_index()
    df = df.sort_values('time').set_index('time').resample('1h').mean()
    df['pm25_ugm3'] = df['pm25_ugm3'].interpolate(limit=3)
    df = df.reset_index()
    
    # History for lags (24h before T0)
    history_24h = df[df['time'] <= t0].tail(24).copy()
    if len(history_24h) < 24:
        # Check available range
        d_min, d_max = df['time'].min(), df['time'].max()
        raise ValueError(f"Insufficient history leading to {t0}. Data range: {d_min} to {d_max}. Need 24h leading up to start time.")
        
    past_pm25 = history_24h['pm25_ugm3'].values
    current_val = past_pm25[-1]
    
    # Actuals for comparison (72h after T0)
    unseen_72h = df[(df['time'] > t0) & (df['time'] <= t0 + pd.Timedelta(hours=MAX_HORIZON))].copy()
    
    # 2. Weather Forecast (as it would have looked at T0)
    print("Fetching weather forecast data...")
    params = {
        "latitude": cfg['coords'][0],
        "longitude": cfg['coords'][1],
        "start_date": t0.strftime('%Y-%m-%d'),
        "end_date": (t0 + pd.Timedelta(days=4)).strftime('%Y-%m-%d'),
        "hourly": ",".join(WEATHER_COLS),
        "timezone": "Asia/Ho_Chi_Minh",
        "wind_speed_unit": "kmh",
    }
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params).json()
    w_df = pd.DataFrame(r['hourly'])
    w_df['time'] = pd.to_datetime(w_df['time']).dt.tz_localize(None)
    
    future_w = w_df[(w_df['time'] > t0) & (w_df['time'] <= t0 + pd.Timedelta(hours=MAX_HORIZON))].copy()
    future_w['hour'] = future_w['time'].dt.hour
    future_w['month'] = future_w['time'].dt.month
    future_w['sin_hour'] = np.sin(2 * np.pi * future_w['hour'] / 24)
    future_w['cos_hour'] = np.cos(2 * np.pi * future_w['hour'] / 24)
    future_w['sin_month'] = np.sin(2 * np.pi * future_w['month'] / 12)
    future_w['cos_month'] = np.cos(2 * np.pi * future_w['month'] / 12)
    weather_inputs = future_w[WEATHER_COLS + ['sin_hour', 'cos_hour', 'sin_month', 'cos_month']].values.flatten()
    
    if len(weather_inputs) < MAX_HORIZON * 10:
        weather_inputs = np.pad(weather_inputs, (0, MAX_HORIZON*10 - len(weather_inputs)))
        
    # 3. Momentum
    mom_inputs = np.array([
        past_pm25[-1] - past_pm25[-2],
        past_pm25[-1] - past_pm25[-3],
        past_pm25[-1] - past_pm25[-4],
        past_pm25[-1] - past_pm25[-7]
    ])
    
    # 4. Predict
    X_new = np.concatenate([past_pm25, weather_inputs, mom_inputs]).reshape(1, -1)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = DeltaSkipMLP(X_new.shape[1], MAX_HORIZON).to(device)
    model.load_state_dict(torch.load(cfg['model_weights'], map_location=device, weights_only=True))
    model.eval()
    
    # Get Scaler
    import importlib.util
    spec = importlib.util.spec_from_file_location("train_mod", cfg['train_script'])
    train_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(train_mod)
    X_train_s, _, _, _, _, _, scaler_x = train_mod.prep_data()
    
    X_scaled = scaler_x.transform(X_new)
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X_scaled).to(device)
        C_tensor = torch.FloatTensor([[current_val]]).to(device)
        y_pred = model(X_tensor, C_tensor).cpu().numpy()[0]
        
    # 5. Plotly (72h Window only)
    print("Plotting 72h window...")
    forecast_times = [t0 + pd.Timedelta(hours=i) for i in range(1, MAX_HORIZON + 1)]
    
    # MAE Band
    all_h = np.arange(1, MAX_HORIZON + 1)
    interp_mae = np.interp(all_h, list(cfg['maes'].keys()), list(cfg['maes'].values()))
    upper_bound = y_pred + interp_mae
    lower_bound = np.maximum(0, y_pred - interp_mae)
    
    fig = go.Figure()
    
    # Uncertainty
    fig.add_trace(go.Scatter(
        x=forecast_times + forecast_times[::-1],
        y=upper_bound.tolist() + lower_bound.tolist()[::-1],
        fill='toself', fillcolor='rgba(128, 128, 128, 0.2)',
        line=dict(color='rgba(255,255,255,0)'), name='Expected Range (±1 MAE)'
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_times, y=y_pred,
        mode='lines', name=f'Forecast (T+0: {t0})',
        line=dict(color='gray', width=3)
    ))
    
    # ACTUAL MEASUREMENTS (24h history + any available unseen)
    actuals_df = pd.concat([history_24h, unseen_72h])
    fig.add_trace(go.Scatter(
        x=actuals_df['time'], y=actuals_df['pm25_ugm3'],
        mode='lines+markers', name='Actual PM2.5 (CEM)',
        line=dict(color='black', width=1, dash='dash'), marker=dict(size=4, color='black')
    ))
    
    fig.update_layout(
        title=f'{site.upper()} 72h Backtest: {t0.strftime("%Y-%m-%d %H:%M")} Issue Time',
        xaxis_title='Time (Forecast Horizon)',
        yaxis_title='PM2.5 (µg/m³)',
        template='plotly_white',
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=80, b=0)
    )
    
    out_file = f"_includes/{site}-t72-forecast.html"
    # Remove HTML, head, body tags so it can be cleanly included in Markdown
    fig.write_html(out_file, full_html=False, include_plotlyjs='cdn')
    print(f"Success. Backtest saved to {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", choices=["hanoi", "hcmc"], default="hanoi")
    parser.add_argument("--date", help="YYYY-MM-DD format", default="2026-06-11")
    parser.add_argument("--hour", type=int, help="Start hour (0-23)", default=1)
    args = parser.parse_args()
    
    t0 = pd.to_datetime(f"{args.date} {args.hour:02d}:00")
    run_backtest(args.site, t0)

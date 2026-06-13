import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import os
import importlib.util

MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'
MAX_HORIZON = 72
WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation']

# Load MLP Architecture
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

CITY_MAP = {
    "hanoi": {
        "data_file": 'tmp/air-quality-analysis-upstream/data/airnow_hanoi_pm25_2015_2025_clean.csv',
        "weather_file": 'tmp/air-quality-analysis-upstream/data/open_meteo_hanoi/open_meteo_hanoi_hourly_2015_2025.csv',
        "model_weights": f'{MODELS_DIR}/t72_delta_skip_best.pt',
        "train_script": "tmp/air-quality-analysis-upstream/scripts/train_t72_delta_skip.py",
        "periods": [
            {"name": "week1", "start": "2024-01-08", "end": "2024-01-14"}, # Jan 2024 (Validation)
            {"name": "week2", "start": "2024-05-08", "end": "2024-05-14"}  # May 2024 (Validation)
        ]
    },
    "hcmc": {
        "data_file": 'tmp/air-quality-analysis-upstream/data/airnow_hcmc_pm25_2016_2024_clean.csv',
        "weather_file": 'tmp/air-quality-analysis-upstream/data/external/interim/ho-chi-minh-city/open_meteo_hourly_2015-01-01_2025-04-09.csv',
        "model_weights": f'{MODELS_DIR}/hcmc_t72_delta_skip_best.pt',
        "train_script": "tmp/air-quality-analysis-upstream/scripts/train_hcmc_t72_delta_skip.py",
        "periods": [
            {"name": "week1", "start": "2023-01-08", "end": "2023-01-14"}, # Jan 2023 (Validation)
            {"name": "week2", "start": "2023-05-08", "end": "2023-05-14"}  # May 2023 (Validation)
        ]
    }
}

HORIZONS = [1, 24, 48, 72]
OUT_DIR = "assets/images/val_plots"
os.makedirs(OUT_DIR, exist_ok=True)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

for site, cfg in CITY_MAP.items():
    print(f"Processing {site.upper()}...")
    
    # 1. Load Data
    pm25_df = pd.read_csv(cfg['data_file'])
    pm25_df['time'] = pd.to_datetime(pm25_df['DATE']).dt.tz_localize(None)
    pm25_df = pm25_df[(pm25_df['raw_pm25'] > 0) & (pm25_df['raw_pm25'] < 500)].copy()
    pm25_df = pm25_df[['time', 'raw_pm25']].rename(columns={'raw_pm25': 'pm25_ugm3'})
    
    weather_df = pd.read_csv(cfg['weather_file'], low_memory=False)
    weather_df['time'] = pd.to_datetime(weather_df['time']).dt.tz_localize(None)
    weather_df = weather_df[['time'] + WEATHER_COLS]
    
    df = pd.merge(pm25_df, weather_df, on='time', how='inner')
    df = df.sort_values('time').set_index('time')
    df = df.resample('1h').mean()
    df['pm25_ugm3'] = df['pm25_ugm3'].interpolate(limit=3)
    df = df.reset_index()
    
    df['hour'] = df['time'].dt.hour
    df['month'] = df['time'].dt.month
    df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
    
    df['mom_1h'] = df['pm25_ugm3'] - df['pm25_ugm3'].shift(1)
    df['mom_2h'] = df['pm25_ugm3'] - df['pm25_ugm3'].shift(2)
    df['mom_3h'] = df['pm25_ugm3'] - df['pm25_ugm3'].shift(3)
    df['mom_6h'] = df['pm25_ugm3'] - df['pm25_ugm3'].shift(6)
    
    # 2. Extract Scaler
    spec = importlib.util.spec_from_file_location("train_mod", cfg['train_script'])
    train_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(train_mod)
    _, _, _, _, _, _, scaler_x = train_mod.prep_data()
    
    # 3. Load Model
    # Need to know input shape.
    X_train_s, _, _, _, _, _, _ = train_mod.prep_data()
    input_dim = X_train_s.shape[1]
    
    model = DeltaSkipMLP(input_dim, MAX_HORIZON).to(device)
    model.load_state_dict(torch.load(cfg['model_weights'], map_location=device, weights_only=True))
    model.eval()
    
    pm25_vals = df['pm25_ugm3'].values
    weather_vals = df[WEATHER_COLS + ['sin_hour', 'cos_hour', 'sin_month', 'cos_month']].values
    mom_vals = df[['mom_1h', 'mom_2h', 'mom_3h', 'mom_6h']].values
    times = df['time'].values
    
    print("Running inference over validation period...")
    pred_matrix = np.full((len(df), MAX_HORIZON), np.nan)
    nowcast_matrix = np.full((len(df), MAX_HORIZON), np.nan)
    rolling_matrix = np.full((len(df), MAX_HORIZON), np.nan)
    
    start_idx = 23
    
    X_list = []
    idx_map = []
    current_vals = []
    
    for i in range(start_idx, len(df) - MAX_HORIZON):
        x_hist = pm25_vals[i-23 : i+1]
        if np.isnan(x_hist).any(): continue
        x_future_weather = weather_vals[i+1 : i+1+MAX_HORIZON].flatten()
        if np.isnan(x_future_weather).any(): continue
        x_mom = mom_vals[i]
        if np.isnan(x_mom).any(): continue
        
        curr = pm25_vals[i]
        roll = np.mean(x_hist)
        
        x_full = np.concatenate([x_hist, x_future_weather, x_mom])
        X_list.append(x_full)
        current_vals.append(curr)
        idx_map.append(i)
        
        for h in range(1, MAX_HORIZON+1):
            target_i = i + h
            nowcast_matrix[target_i, h-1] = curr
            rolling_matrix[target_i, h-1] = roll
            
    if len(X_list) == 0:
        print(f"ERROR: X_list is empty for {site}! Check NaNs.")
        print(f"NaNs in pm25: {np.isnan(pm25_vals).sum()}, weather: {np.isnan(weather_vals).sum()}, mom: {np.isnan(mom_vals).sum()}")
        continue

    X_mat = np.array(X_list)
    curr_mat = np.array(current_vals).reshape(-1, 1)
    X_scaled = scaler_x.transform(X_mat)
    
    batch_size = 512
    with torch.no_grad():
        for b in range(0, len(X_scaled), batch_size):
            X_b = torch.FloatTensor(X_scaled[b:b+batch_size]).to(device)
            C_b = torch.FloatTensor(curr_mat[b:b+batch_size]).to(device)
            preds = model(X_b, C_b).cpu().numpy()
            
            for j, p in enumerate(preds):
                base_i = idx_map[b+j]
                for h in range(1, MAX_HORIZON+1):
                    target_i = base_i + h
                    pred_matrix[target_i, h-1] = p[h-1]
                    
    df['time'] = pd.to_datetime(df['time'])
    
    # 4. Generate Plots
    for p in cfg['periods']:
        mask = (df['time'] >= pd.to_datetime(p['start'])) & (df['time'] <= pd.to_datetime(p['end']) + pd.Timedelta(days=1))
        plot_df = df[mask].copy()
        
        if len(plot_df) == 0:
            print(f"No data for {site} in {p['name']}")
            continue
            
        indices = plot_df.index
        t_vals = plot_df['time']
        
        for h in HORIZONS:
            plt.figure(figsize=(12, 5))
            
            # Extend actuals back by h hours to show T0 context
            extended_start = pd.to_datetime(p['start']) - pd.Timedelta(hours=h)
            mask_ext = (df['time'] >= extended_start) & (df['time'] <= pd.to_datetime(p['end']) + pd.Timedelta(days=1))
            ext_df = df[mask_ext].copy()
            
            # Actual: black marker with dashes thin line
            plt.plot(ext_df['time'], ext_df['pm25_ugm3'], color='black', marker='.', linestyle='--', linewidth=1, label='Measured PM2.5', markersize=6)
            
            # MLP
            mlp_preds = pred_matrix[indices, h-1]
            plt.plot(t_vals, mlp_preds, color='blue', linewidth=2, label=f'Delta-Skip MLP (T+{h})')

            # Baselines
            if h == 1:
                nowc = nowcast_matrix[indices, h-1]
                plt.plot(t_vals, nowc, color='red', linestyle=':', label='Nowcast (T0 PM2.5)')
                
            roll = rolling_matrix[indices, h-1]
            plt.plot(t_vals, roll, color='orange', linestyle='-.', label=f'Rolling 24h Mean (T0)')
            
            # Note about the first point
            plt.text(0.02, 0.95, f"Note: First prediction point made at -{h}h", 
                     transform=plt.gca().transAxes, fontsize=10, 
                     verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='lightgray'))
            
            plt.title(f"{site.upper()} Validation - {p['name']} (Horizon: T+{h})")
            plt.xlabel(f"Time (Predicted Time, with previous {h}h history)")
            plt.ylabel("PM2.5 (µg/m³)")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            out_path = f"{OUT_DIR}/{site}_{p['name']}_T{h}.png"
            plt.savefig(out_path, dpi=150)
            plt.close()
            print(f"Saved {out_path}")

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import os
import pickle
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight

# --- CONFIG ---
DATA_DIR = 'tmp/air-quality-analysis-upstream/data'
MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'
MAX_HORIZON = 72
BATCH_SIZE = 1024
EPOCHS = 50
LEARNING_RATE = 1e-3

WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation', 'shortwave_radiation', 'wind_direction_10m']
NEW_WEATHER_COLS = ['precip_washout', 'wind_stagnant', 'wind_clearing', 'sin_wind_dir', 'cos_wind_dir', 'delta_temp_3h', 'delta_pressure_3h', 'delta_wind_speed_3h', 'rh_swelling', 'wind_NE', 'wind_SE', 'pre_rain_push', 'sun_uplift', 'inversion_proxy']
ALL_WEATHER_COLS = WEATHER_COLS + NEW_WEATHER_COLS
TIME_COLS = ['sin_hour', 'cos_hour', 'sin_month', 'cos_month']
PROXY_TIME_COLS = ['hour', 'month', 'sin_hour', 'cos_hour', 'sin_month', 'cos_month']

class AQIMultiOutputMLP(nn.Module):
    def __init__(self, input_dim, horizons, num_classes):
        super(AQIMultiOutputMLP, self).__init__()
        self.horizons = horizons
        self.num_classes = num_classes
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512), nn.BatchNorm1d(512), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(512, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, horizons * num_classes)
        )
    def forward(self, x):
        return self.net(x).view(-1, self.num_classes, self.horizons)

class DeltaSkipMLPV4(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DeltaSkipMLPV4, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512), nn.BatchNorm1d(512), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(512, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, output_dim)
        )
    def forward(self, x, current_val):
        return current_val + self.net(x)

def get_aqi_bin_vectorized(pm25_array):
    bins = np.zeros_like(pm25_array, dtype=np.int64)
    bins[(pm25_array > 12.0) & (pm25_array <= 35.4)] = 1
    bins[(pm25_array > 35.4) & (pm25_array <= 55.4)] = 2
    bins[(pm25_array > 55.4) & (pm25_array <= 150.4)] = 3
    bins[pm25_array > 150.4] = 4
    return bins

def weighted_mse_loss(input, target, weights):
    out = (input - target)**2
    return (out * weights).mean()

def prep_data_v4():
    print("Loading and preparing V4 data...")
    pm25_df = pd.read_csv(f'{DATA_DIR}/airnow_hanoi_pm25_2015_2025_clean.csv')
    pm25_df['time'] = pd.to_datetime(pm25_df['DATE']).dt.tz_localize(None)
    pm25_df = pm25_df[['time', 'raw_pm25']].rename(columns={'raw_pm25': 'pm25_ugm3'})
    
    weather_df = pd.read_csv(f'{DATA_DIR}/open_meteo_hanoi/open_meteo_hanoi_hourly_2015_2025.csv', low_memory=False)
    weather_df['time'] = pd.to_datetime(weather_df['time']).dt.tz_localize(None)
    
    df = pd.merge(pm25_df, weather_df[['time'] + WEATHER_COLS], on='time', how='inner')
    df = df.sort_values('time').set_index('time')
    df = df.resample('1h').mean()
    df['pm25_ugm3'] = df['pm25_ugm3'].interpolate(limit=3)
    df = df.reset_index()
    
    df['precip_washout'] = 1 / (1 + np.exp(-(df['precipitation'] - 1.0) * 4))
    df['wind_stagnant'] = np.exp(-df['wind_speed_10m'])
    df['wind_clearing'] = 1 / (1 + np.exp(-(df['wind_speed_10m'] - 3.0) * 2))
    df['sin_wind_dir'] = np.sin(np.radians(df['wind_direction_10m']))
    df['cos_wind_dir'] = np.cos(np.radians(df['wind_direction_10m']))
    df['delta_temp_3h'] = df['temperature_2m'] - df['temperature_2m'].shift(3)
    df['delta_pressure_3h'] = df['surface_pressure'] - df['surface_pressure'].shift(3)
    df['delta_wind_speed_3h'] = df['wind_speed_10m'] - df['wind_speed_10m'].shift(3)
    df['rh_swelling'] = np.where(df['relative_humidity_2m'] > 80, np.exp((df['relative_humidity_2m'] - 80) / 10), 1.0)
    df['wind_NE'] = ((df['wind_direction_10m'] >= 0) & (df['wind_direction_10m'] < 90)).astype(float)
    df['wind_SE'] = ((df['wind_direction_10m'] >= 90) & (df['wind_direction_10m'] < 180)).astype(float)
    df['pre_rain_push'] = ((df['cloud_cover'] > 70) & (df['precipitation'] == 0) & (df['precipitation'].shift(-1) > 0)).astype(float)
    df['sun_uplift'] = (df['shortwave_radiation'] * (df['temperature_2m'] > 30) / 1000.0).astype(float)
    df['inversion_proxy'] = ((df['wind_speed_10m'] < 2.0) & (df['cloud_cover'] < 30) & ((df['time'].dt.hour < 7) | (df['time'].dt.hour > 18))).astype(float)
    
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
    
    pm25_ma_6h = df['pm25_ugm3'].rolling(window=6, min_periods=1).mean()
    wind_ma_6h = df['wind_speed_10m'].rolling(window=6, min_periods=1).mean()
    df['accumulation_proxy'] = pm25_ma_6h / (wind_ma_6h + 1.0)
    
    df.fillna(0, inplace=True)
    
    pm25_vals = df['pm25_ugm3'].values
    weather_vals = df[ALL_WEATHER_COLS + TIME_COLS].values
    proxy_weather_vals = df[ALL_WEATHER_COLS + PROXY_TIME_COLS].values
    mom_vals = df[['mom_1h', 'mom_2h', 'mom_3h', 'mom_6h', 'accumulation_proxy']].values
    times = df['time'].values
    
    X_list, y_list, current_vals, valid_times, proxy_weather_list = [], [], [], [], []
    y_bins_list = []
    
    for i in range(23, len(df) - MAX_HORIZON - 1):
        y_block = pm25_vals[i+1 : i+1+MAX_HORIZON]
        if np.isnan(y_block).any(): continue
        
        x_hist = pm25_vals[i-23 : i+1]
        if np.isnan(x_hist).any(): continue
        
        x_future_weather = weather_vals[i+1 : i+1+MAX_HORIZON].flatten()
        if np.isnan(x_future_weather).any(): continue
        
        x_proxy_weather = proxy_weather_vals[i+1 : i+1+MAX_HORIZON]
        x_mom = mom_vals[i]
        curr = pm25_vals[i]
        
        x_full = np.concatenate([x_hist, x_future_weather, x_mom])
        X_list.append(x_full)
        y_list.append(y_block)
        y_bins_list.append(get_aqi_bin_vectorized(y_block))
        current_vals.append(curr)
        valid_times.append(times[i])
        proxy_weather_list.append(x_proxy_weather)
        
    X_mat = np.array(X_list)
    y_mat = np.array(y_list)
    y_bins_mat = np.array(y_bins_list)
    curr_mat = np.array(current_vals).reshape(-1, 1)
    proxy_weather_mat = np.array(proxy_weather_list)
    
    split_date = np.datetime64('2024-01-01')
    train_mask = np.array(valid_times) < split_date
    valid_mask = ~train_mask
    
    X_train, y_train, c_train, y_bins_train = X_mat[train_mask], y_mat[train_mask], curr_mat[train_mask], y_bins_mat[train_mask]
    X_valid, y_valid, c_valid, y_bins_valid = X_mat[valid_mask], y_mat[valid_mask], curr_mat[valid_mask], y_bins_mat[valid_mask]
    
    scaler_x = StandardScaler()
    X_train_scaled = scaler_x.fit_transform(X_train)
    X_valid_scaled = scaler_x.transform(X_valid)
    
    # 2. Train AQI Classifier
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("--- Training AQI Classifier (V4 features) ---")
    
    y_train_flat = y_bins_train.flatten()
    class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y_train_flat), y=y_train_flat)
    weight_tensor = torch.FloatTensor(class_weights).to(device)
    
    train_ds_aqi = TensorDataset(torch.FloatTensor(X_train_scaled), torch.LongTensor(y_bins_train))
    valid_ds_aqi = TensorDataset(torch.FloatTensor(X_valid_scaled), torch.LongTensor(y_bins_valid))
    loader_train_aqi = DataLoader(train_ds_aqi, batch_size=BATCH_SIZE, shuffle=True)
    loader_valid_aqi = DataLoader(valid_ds_aqi, batch_size=BATCH_SIZE, shuffle=False)
    
    aqi_model = AQIMultiOutputMLP(X_train_scaled.shape[1], MAX_HORIZON, 5).to(device)
    optimizer_aqi = optim.Adam(aqi_model.parameters(), lr=LEARNING_RATE)
    criterion_aqi = nn.CrossEntropyLoss(weight=weight_tensor)
    
    best_loss = float('inf')
    for epoch in range(15): # Faster epochs for pipeline
        aqi_model.train()
        for bx, by in loader_train_aqi:
            bx, by = bx.to(device), by.to(device)
            optimizer_aqi.zero_grad()
            loss = criterion_aqi(aqi_model(bx), by)
            loss.backward()
            optimizer_aqi.step()
            
        aqi_model.eval()
        v_loss = 0
        with torch.no_grad():
            for bx, by in loader_valid_aqi:
                bx, by = bx.to(device), by.to(device)
                v_loss += criterion_aqi(aqi_model(bx), by).item()
        
        if v_loss < best_loss:
            best_loss = v_loss
            torch.save(aqi_model.state_dict(), f'{MODELS_DIR}/aqi_v4_tmp.pt')
            
    aqi_model.load_state_dict(torch.load(f'{MODELS_DIR}/aqi_v4_tmp.pt', weights_only=True))
    aqi_model.eval()
    
    with torch.no_grad():
        X_t_tensor = torch.FloatTensor(X_train_scaled).to(device)
        aqi_train_flat = torch.softmax(aqi_model(X_t_tensor), dim=1).view(X_train_scaled.shape[0], -1).cpu().numpy()
        X_v_tensor = torch.FloatTensor(X_valid_scaled).to(device)
        aqi_valid_flat = torch.softmax(aqi_model(X_v_tensor), dim=1).view(X_valid_scaled.shape[0], -1).cpu().numpy()

    # 3. Train LightGBM Proxies
    print("--- Training Atmospheric Proxies (V4 features) ---")
    igra_df = pd.read_csv(f'{DATA_DIR}/igra_hanoi_inversion_features_2015_2026.csv')
    igra_df['time'] = pd.to_datetime(igra_df['datetime']).dt.tz_convert('Asia/Ho_Chi_Minh').dt.tz_localize(None)
    proxy_merged = pd.merge(df, igra_df[['time', 'is_surface_inversion', 'is_very_stable']], on='time', how='inner')
    proxy_merged.dropna(subset=ALL_WEATHER_COLS + PROXY_TIME_COLS + ['is_surface_inversion', 'is_very_stable'], inplace=True)
    
    p_train = proxy_merged[proxy_merged['time'] < split_date]
    p_valid = proxy_merged[proxy_merged['time'] >= split_date]
    
    proxy_models = {}
    for target in ['is_surface_inversion', 'is_very_stable']:
        pos_w = (len(p_train) - p_train[target].sum()) / max(1, p_train[target].sum())
        model = lgb.LGBMClassifier(n_estimators=100, learning_rate=0.05, max_depth=6, scale_pos_weight=pos_w, random_state=42)
        model.fit(p_train[ALL_WEATHER_COLS + PROXY_TIME_COLS], p_train[target], eval_set=[(p_valid[ALL_WEATHER_COLS + PROXY_TIME_COLS], p_valid[target])], callbacks=[lgb.early_stopping(50, verbose=False)])
        proxy_models[target] = model
        
    proxy_train_weather = proxy_weather_mat[train_mask].reshape(-1, len(ALL_WEATHER_COLS + PROXY_TIME_COLS))
    proxy_valid_weather = proxy_weather_mat[valid_mask].reshape(-1, len(ALL_WEATHER_COLS + PROXY_TIME_COLS))
    
    inv_train_probs = proxy_models['is_surface_inversion'].predict_proba(proxy_train_weather)[:, 1].reshape(X_train.shape[0], MAX_HORIZON)
    inv_valid_probs = proxy_models['is_surface_inversion'].predict_proba(proxy_valid_weather)[:, 1].reshape(X_valid.shape[0], MAX_HORIZON)
    stab_train_probs = proxy_models['is_very_stable'].predict_proba(proxy_train_weather)[:, 1].reshape(X_train.shape[0], MAX_HORIZON)
    stab_valid_probs = proxy_models['is_very_stable'].predict_proba(proxy_valid_weather)[:, 1].reshape(X_valid.shape[0], MAX_HORIZON)
    
    X_train_combined = np.hstack([X_train_scaled, aqi_train_flat, inv_train_probs, stab_train_probs])
    X_valid_combined = np.hstack([X_valid_scaled, aqi_valid_flat, inv_valid_probs, stab_valid_probs])
    
    return X_train_combined, y_train, X_valid_combined, y_valid, c_train, c_valid

def train_pipeline():
    X_train, y_train, X_valid, y_valid, c_train, c_valid = prep_data_v4()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n--- Training DeltaSkipMLP V4+Proxies on {device} | Input Dim: {X_train.shape[1]} ---")
    
    train_ds = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train), torch.FloatTensor(c_train))
    valid_ds = TensorDataset(torch.FloatTensor(X_valid), torch.FloatTensor(y_valid), torch.FloatTensor(c_valid))
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    model = DeltaSkipMLPV4(X_train.shape[1], MAX_HORIZON).to(device)
    weights = torch.ones(MAX_HORIZON).to(device)
    weights[0], weights[1], weights[2] = 20.0, 10.0, 5.0
    
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_loss = float('inf')
    best_model_path = f'{MODELS_DIR}/t72_delta_skip_v4_phase3_best.pt'
    
    for epoch in range(EPOCHS):
        model.train()
        for bx, by, bc in train_loader:
            bx, by, bc = bx.to(device), by.to(device), bc.to(device)
            optimizer.zero_grad()
            loss = weighted_mse_loss(model(bx, bc), by, weights)
            loss.backward()
            optimizer.step()
            
        model.eval()
        v_loss = 0
        with torch.no_grad():
            for bx, by, bc in valid_loader:
                bx, by, bc = bx.to(device), by.to(device), bc.to(device)
                v_loss += weighted_mse_loss(model(bx, bc), by, weights).item()
        
        avg_v = v_loss / len(valid_loader)
        scheduler.step(avg_v)
        if avg_v < best_loss:
            best_loss = avg_v
            torch.save(model.state_dict(), best_model_path)
            
    print(f"Training complete. Best Validation Loss: {best_loss:.4f}")
    
    model.load_state_dict(torch.load(best_model_path, weights_only=True))
    model.eval()
    all_preds = []
    with torch.no_grad():
        for bx, by, bc in valid_loader:
            bx, bc = bx.to(device), bc.to(device)
            all_preds.append(model(bx, bc).cpu().numpy())
    
    y_pred = np.concatenate(all_preds)
    
    print("\n--- V4+Proxies Evaluation on Validation Set ---")
    results = []
    for h in [1, 6, 12, 24, 48, 72]:
        h_idx = h - 1
        rmse = np.sqrt(mean_squared_error(y_valid[:, h_idx], y_pred[:, h_idx]))
        r2 = r2_score(y_valid[:, h_idx], y_pred[:, h_idx])
        results.append(f"T+{h:02d}h | RMSE: {rmse:.3f} | R2: {r2:.3f}")
        print(results[-1])
        
    ov_rmse = np.sqrt(mean_squared_error(y_valid, y_pred))
    ov_r2 = r2_score(y_valid.flatten(), y_pred.flatten())
    print(f"OVERALL | RMSE: {ov_rmse:.3f} | R2: {ov_r2:.3f}")

if __name__ == "__main__":
    train_pipeline()

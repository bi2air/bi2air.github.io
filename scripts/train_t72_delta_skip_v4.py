import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import os
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

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
MOM_COLS = ['mom_1h', 'mom_2h', 'mom_3h', 'mom_6h', 'accumulation_proxy']

# --- MODEL ---
class DeltaSkipMLPV4(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DeltaSkipMLPV4, self).__init__()
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

def prep_data_v4():
    print("Loading and preparing V4 data...")
    pm25_df = pd.read_csv(f'{DATA_DIR}/airnow_hanoi_pm25_2015_2025_clean.csv')
    pm25_df['time'] = pd.to_datetime(pm25_df['DATE']).dt.tz_localize(None)
    pm25_df = pm25_df[['time', 'raw_pm25']].rename(columns={'raw_pm25': 'pm25_ugm3'})
    
    weather_df = pd.read_csv(f'{DATA_DIR}/open_meteo_hanoi/open_meteo_hanoi_hourly_2015_2025.csv', low_memory=False)
    weather_df['time'] = pd.to_datetime(weather_df['time']).dt.tz_localize(None)
    weather_df = weather_df[['time'] + WEATHER_COLS]
    
    df = pd.merge(pm25_df, weather_df, on='time', how='inner')
    df = df.sort_values('time').set_index('time')
    df = df.resample('1h').mean()
    df['pm25_ugm3'] = df['pm25_ugm3'].interpolate(limit=3)
    df = df.reset_index()
    
    # --- PHASE 1.2 FEATURE ENGINEERING ---
    # 1. Precipitation Washout (Sigmoid-like threshold around 1mm)
    df['precip_washout'] = 1 / (1 + np.exp(-(df['precipitation'] - 1.0) * 4))
    
    # 2. Wind Speed Proxies
    df['wind_stagnant'] = np.exp(-df['wind_speed_10m'])
    df['wind_clearing'] = 1 / (1 + np.exp(-(df['wind_speed_10m'] - 3.0) * 2))
    
    # 3. Wind Direction Components
    df['sin_wind_dir'] = np.sin(np.radians(df['wind_direction_10m']))
    df['cos_wind_dir'] = np.cos(np.radians(df['wind_direction_10m']))
    
    # 4. Convective Deltas (Frontal / Weather change proxies)
    df['delta_temp_3h'] = df['temperature_2m'] - df['temperature_2m'].shift(3)
    df['delta_pressure_3h'] = df['surface_pressure'] - df['surface_pressure'].shift(3)
    df['delta_wind_speed_3h'] = df['wind_speed_10m'] - df['wind_speed_10m'].shift(3)
    
    # 5. Hygroscopic Swelling (RH > 80%)
    df['rh_swelling'] = np.where(df['relative_humidity_2m'] > 80, np.exp((df['relative_humidity_2m'] - 80) / 10), 1.0)
    
    # 6. Wind Quadrants (NE = Winter/Cold, SE = Warm/Moist)
    df['wind_NE'] = ((df['wind_direction_10m'] >= 0) & (df['wind_direction_10m'] < 90)).astype(float)
    df['wind_SE'] = ((df['wind_direction_10m'] >= 90) & (df['wind_direction_10m'] < 180)).astype(float)
    
    # 7. Pre-Rain PM2.5 Push (Cloudy, dry now, raining next hour)
    df['pre_rain_push'] = ((df['cloud_cover'] > 70) & (df['precipitation'] == 0) & (df['precipitation'].shift(-1) > 0)).astype(float)
    
    # 8. Summer Sun Uplift (High radiation + high temp -> dilution)
    df['sun_uplift'] = (df['shortwave_radiation'] * (df['temperature_2m'] > 30) / 1000.0).astype(float)
    
    # 9. Inversion Proxy (Clear night, calm wind)
    df['inversion_proxy'] = ((df['wind_speed_10m'] < 2.0) & (df['cloud_cover'] < 30) & ((df['time'].dt.hour < 7) | (df['time'].dt.hour > 18))).astype(float)
    
    # --- Time Encodings ---
    df['hour'] = df['time'].dt.hour
    df['month'] = df['time'].dt.month
    df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
    
    # --- PHASE 1.3 MASS BALANCE PROXY ---
    df['mom_1h'] = df['pm25_ugm3'] - df['pm25_ugm3'].shift(1)
    df['mom_2h'] = df['pm25_ugm3'] - df['pm25_ugm3'].shift(2)
    df['mom_3h'] = df['pm25_ugm3'] - df['pm25_ugm3'].shift(3)
    df['mom_6h'] = df['pm25_ugm3'] - df['pm25_ugm3'].shift(6)
    
    pm25_ma_6h = df['pm25_ugm3'].rolling(window=6, min_periods=1).mean()
    wind_ma_6h = df['wind_speed_10m'].rolling(window=6, min_periods=1).mean()
    df['accumulation_proxy'] = pm25_ma_6h / (wind_ma_6h + 1.0)
    
    # Fill NAs generated by rolling/shift
    df.fillna(0, inplace=True)
    
    pm25_vals = df['pm25_ugm3'].values
    weather_vals = df[ALL_WEATHER_COLS + TIME_COLS].values
    mom_vals = df[MOM_COLS].values
    times = df['time'].values
    
    X_list, y_list, current_vals, valid_times = [], [], [], []
    
    for i in range(23, len(df) - MAX_HORIZON):
        y_block = pm25_vals[i+1 : i+1+MAX_HORIZON]
        if np.isnan(y_block).any(): continue
        
        x_hist = pm25_vals[i-23 : i+1]
        if np.isnan(x_hist).any(): continue
        
        x_future_weather = weather_vals[i+1 : i+1+MAX_HORIZON].flatten()
        if np.isnan(x_future_weather).any(): continue
        
        x_mom = mom_vals[i]
        if np.isnan(x_mom).any(): continue
        
        curr = pm25_vals[i]
        
        x_full = np.concatenate([x_hist, x_future_weather, x_mom])
        X_list.append(x_full)
        y_list.append(y_block)
        current_vals.append(curr)
        valid_times.append(times[i])
        
    X_mat = np.array(X_list)
    y_mat = np.array(y_list)
    curr_mat = np.array(current_vals).reshape(-1, 1)
    
    split_date = np.datetime64('2024-01-01')
    train_mask = np.array(valid_times) < split_date
    valid_mask = ~train_mask
    
    X_train, y_train, c_train = X_mat[train_mask], y_mat[train_mask], curr_mat[train_mask]
    X_valid, y_valid, c_valid = X_mat[valid_mask], y_mat[valid_mask], curr_mat[valid_mask]
    
    scaler_x = StandardScaler()
    X_train_scaled = scaler_x.fit_transform(X_train)
    X_valid_scaled = scaler_x.transform(X_valid)
    
    return X_train_scaled, y_train, X_valid_scaled, y_valid, c_train, c_valid, scaler_x

def weighted_mse_loss(input, target, weights):
    out = (input - target)**2
    out = out * weights
    return out.mean()

def train():
    X_train, y_train, X_valid, y_valid, c_train, c_valid, scaler_x = prep_data_v4()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training V2 Features on {device} | Input Dim: {X_train.shape[1]}")
    
    train_ds = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train), torch.FloatTensor(c_train))
    valid_ds = TensorDataset(torch.FloatTensor(X_valid), torch.FloatTensor(y_valid), torch.FloatTensor(c_valid))
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    model = DeltaSkipMLPV4(X_train.shape[1], MAX_HORIZON).to(device)
    
    weights = torch.ones(MAX_HORIZON).to(device)
    weights[0] = 20.0
    weights[1] = 10.0
    weights[2] = 5.0
    
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_loss = float('inf')
    best_model_path = f'{MODELS_DIR}/t72_delta_skip_v4_best.pt'
    
    for epoch in range(EPOCHS):
        model.train()
        t_loss = 0
        for bx, by, bc in train_loader:
            bx, by, bc = bx.to(device), by.to(device), bc.to(device)
            optimizer.zero_grad()
            pred = model(bx, bc)
            loss = weighted_mse_loss(pred, by, weights)
            loss.backward()
            optimizer.step()
            t_loss += loss.item()
            
        model.eval()
        v_loss = 0
        with torch.no_grad():
            for bx, by, bc in valid_loader:
                bx, by, bc = bx.to(device), by.to(device), bc.to(device)
                pred = model(bx, bc)
                v_loss += weighted_mse_loss(pred, by, weights).item()
        
        avg_v = v_loss / len(valid_loader)
        scheduler.step(avg_v)
        if (epoch+1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:02d}/{EPOCHS} | Train Loss: {t_loss/len(train_loader):.4f} | Valid Loss: {avg_v:.4f}")
        
        if avg_v < best_loss:
            best_loss = avg_v
            torch.save(model.state_dict(), best_model_path)
            
    print(f"Training complete. Best Validation Loss: {best_loss:.4f}")
    
    # Evaluation
    model.load_state_dict(torch.load(best_model_path, weights_only=True))
    model.eval()
    all_preds = []
    with torch.no_grad():
        for bx, by, bc in valid_loader:
            bx, bc = bx.to(device), bc.to(device)
            pred = model(bx, bc)
            all_preds.append(pred.cpu().numpy())
    
    y_pred = np.concatenate(all_preds)
    
    # Metrics
    results = []
    print("\n--- Evaluation on Validation Set ---")
    for h in [1, 6, 12, 24, 48, 72]:
        h_idx = h - 1
        y_true_h = y_valid[:, h_idx]
        y_pred_h = y_pred[:, h_idx]
        rmse = np.sqrt(mean_squared_error(y_true_h, y_pred_h))
        r2 = r2_score(y_true_h, y_pred_h)
        results.append({"horizon": h, "rmse": rmse, "r2": r2})
        print(f"T+{h:02d}h | RMSE: {rmse:.3f} | R2: {r2:.3f}")
        
    ov_rmse = np.sqrt(mean_squared_error(y_valid, y_pred))
    ov_r2 = r2_score(y_valid.flatten(), y_pred.flatten())
    print(f"OVERALL | RMSE: {ov_rmse:.3f} | R2: {ov_r2:.3f}")
    
    # Save V4 results
    with open('docs/results_v4_features.pkl', 'wb') as f:
        pickle.dump({"metrics": results, "overall": {"rmse": ov_rmse, "r2": ov_r2}}, f)

if __name__ == "__main__":
    if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
    train()

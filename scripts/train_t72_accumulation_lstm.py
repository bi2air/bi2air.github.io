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
BATCH_SIZE = 256
EPOCHS = 50
LEARNING_RATE = 1e-3
HIDDEN_DIM = 128

WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation']
NEW_WEATHER_COLS = ['precip_washout', 'wind_stagnant', 'wind_clearing']
ALL_WEATHER_COLS = WEATHER_COLS + NEW_WEATHER_COLS
TIME_COLS = ['sin_hour', 'cos_hour', 'sin_month', 'cos_month']

# --- MODEL ---
class AccumulationLSTM(nn.Module):
    def __init__(self, enc_input_dim, dec_input_dim, hidden_dim):
        super(AccumulationLSTM, self).__init__()
        self.encoder = nn.LSTM(enc_input_dim, hidden_dim, batch_first=True, num_layers=1)
        self.decoder = nn.LSTM(dec_input_dim, hidden_dim, batch_first=True, num_layers=1)
        
        # Small MLP head for the delta prediction
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
    def forward(self, x_enc, x_dec, current_val):
        # x_enc: [B, 24, 14]
        # x_dec: [B, 72, 13]
        
        # 1. Encoder processes history
        _, (hidden, cell) = self.encoder(x_enc)
        
        # 2. Decoder processes future weather
        dec_out, _ = self.decoder(x_dec, (hidden, cell))
        
        # 3. Predict step-by-step Deltas
        # dec_out is [B, 72, hidden_dim] -> deltas is [B, 72, 1] -> squeeze to [B, 72]
        deltas = self.fc(dec_out).squeeze(-1)
        
        # 4. Integrate (Skip Connection via Cumulative Sum)
        # pm25(t) = current_val + sum(deltas up to t)
        pred_pm25 = current_val + torch.cumsum(deltas, dim=1)
        
        return pred_pm25

def prep_data_lstm():
    print("Loading and preparing Sequence Data for LSTM...")
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
    df['precip_washout'] = 1 / (1 + np.exp(-(df['precipitation'] - 1.0) * 4))
    df['wind_stagnant'] = np.exp(-df['wind_speed_10m'])
    df['wind_clearing'] = 1 / (1 + np.exp(-(df['wind_speed_10m'] - 3.0) * 2))
    
    df['hour'] = df['time'].dt.hour
    df['month'] = df['time'].dt.month
    df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
    
    df.fillna(0, inplace=True)
    
    pm25_vals = df['pm25_ugm3'].values
    weather_vals = df[ALL_WEATHER_COLS + TIME_COLS].values
    times = df['time'].values
    
    X_enc_list, X_dec_list, y_list, current_vals, valid_times = [], [], [], [], []
    
    for i in range(23, len(df) - MAX_HORIZON):
        y_block = pm25_vals[i+1 : i+1+MAX_HORIZON]
        if np.isnan(y_block).any(): continue
        
        x_hist_pm25 = pm25_vals[i-23 : i+1].reshape(-1, 1)
        x_hist_weather = weather_vals[i-23 : i+1]
        if np.isnan(x_hist_pm25).any() or np.isnan(x_hist_weather).any(): continue
        
        x_enc = np.concatenate([x_hist_pm25, x_hist_weather], axis=1)
        
        x_dec = weather_vals[i+1 : i+1+MAX_HORIZON]
        if np.isnan(x_dec).any(): continue
        
        curr = pm25_vals[i]
        
        X_enc_list.append(x_enc)
        X_dec_list.append(x_dec)
        y_list.append(y_block)
        current_vals.append(curr)
        valid_times.append(times[i])
        
    X_enc_mat = np.array(X_enc_list)
    X_dec_mat = np.array(X_dec_list)
    y_mat = np.array(y_list)
    curr_mat = np.array(current_vals).reshape(-1, 1)
    
    split_date = np.datetime64('2024-01-01')
    train_mask = np.array(valid_times) < split_date
    valid_mask = ~train_mask
    
    X_enc_train, X_enc_valid = X_enc_mat[train_mask], X_enc_mat[valid_mask]
    X_dec_train, X_dec_valid = X_dec_mat[train_mask], X_dec_mat[valid_mask]
    y_train, y_valid = y_mat[train_mask], y_mat[valid_mask]
    c_train, c_valid = curr_mat[train_mask], curr_mat[valid_mask]
    
    scaler_enc = StandardScaler()
    X_enc_train_flat = X_enc_train.reshape(-1, X_enc_train.shape[2])
    X_enc_train_scaled = scaler_enc.fit_transform(X_enc_train_flat).reshape(X_enc_train.shape)
    X_enc_valid_flat = X_enc_valid.reshape(-1, X_enc_valid.shape[2])
    X_enc_valid_scaled = scaler_enc.transform(X_enc_valid_flat).reshape(X_enc_valid.shape)
    
    scaler_dec = StandardScaler()
    X_dec_train_flat = X_dec_train.reshape(-1, X_dec_train.shape[2])
    X_dec_train_scaled = scaler_dec.fit_transform(X_dec_train_flat).reshape(X_dec_train.shape)
    X_dec_valid_flat = X_dec_valid.reshape(-1, X_dec_valid.shape[2])
    X_dec_valid_scaled = scaler_dec.transform(X_dec_valid_flat).reshape(X_dec_valid.shape)
    
    return X_enc_train_scaled, X_dec_train_scaled, y_train, X_enc_valid_scaled, X_dec_valid_scaled, y_valid, c_train, c_valid

def weighted_mse_loss(input, target, weights):
    out = (input - target)**2
    out = out * weights
    return out.mean()

def train():
    (X_enc_train, X_dec_train, y_train, 
     X_enc_valid, X_dec_valid, y_valid, 
     c_train, c_valid) = prep_data_lstm()
     
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    enc_dim = X_enc_train.shape[2]
    dec_dim = X_dec_train.shape[2]
    
    print(f"Training AccumulationLSTM on {device} | Enc Dim: {enc_dim} | Dec Dim: {dec_dim}")
    
    train_ds = TensorDataset(torch.FloatTensor(X_enc_train), torch.FloatTensor(X_dec_train), 
                             torch.FloatTensor(y_train), torch.FloatTensor(c_train))
    valid_ds = TensorDataset(torch.FloatTensor(X_enc_valid), torch.FloatTensor(X_dec_valid), 
                             torch.FloatTensor(y_valid), torch.FloatTensor(c_valid))
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    model = AccumulationLSTM(enc_dim, dec_dim, HIDDEN_DIM).to(device)
    
    weights = torch.ones(MAX_HORIZON).to(device)
    weights[0] = 20.0
    weights[1] = 10.0
    weights[2] = 5.0
    
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_loss = float('inf')
    best_model_path = f'{MODELS_DIR}/t72_accumulation_lstm_best.pt'
    
    for epoch in range(EPOCHS):
        model.train()
        t_loss = 0
        for b_enc, b_dec, by, bc in train_loader:
            b_enc, b_dec, by, bc = b_enc.to(device), b_dec.to(device), by.to(device), bc.to(device)
            optimizer.zero_grad()
            pred = model(b_enc, b_dec, bc)
            loss = weighted_mse_loss(pred, by, weights)
            loss.backward()
            optimizer.step()
            t_loss += loss.item()
            
        model.eval()
        v_loss = 0
        with torch.no_grad():
            for b_enc, b_dec, by, bc in valid_loader:
                b_enc, b_dec, by, bc = b_enc.to(device), b_dec.to(device), by.to(device), bc.to(device)
                pred = model(b_enc, b_dec, bc)
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
        for b_enc, b_dec, by, bc in valid_loader:
            b_enc, b_dec, bc = b_enc.to(device), b_dec.to(device), bc.to(device)
            pred = model(b_enc, b_dec, bc)
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
    
    with open('doc-work/results_accumulation_lstm.pkl', 'wb') as f:
        pickle.dump({"metrics": results, "overall": {"rmse": ov_rmse, "r2": ov_r2}}, f)

if __name__ == "__main__":
    if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
    train()

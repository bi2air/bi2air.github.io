import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import os
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils.class_weight import compute_class_weight

# --- CONFIG ---
DATA_DIR = 'tmp/air-quality-analysis-upstream/data'
MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'
MAX_HORIZON = 72
NUM_CLASSES = 5
BATCH_SIZE = 1024
EPOCHS = 50
LEARNING_RATE = 1e-3

WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation', 'shortwave_radiation', 'wind_direction_10m']
NEW_WEATHER_COLS = ['precip_washout', 'wind_stagnant', 'wind_clearing', 'sin_wind_dir', 'cos_wind_dir', 'delta_temp_3h', 'delta_pressure_3h', 'delta_wind_speed_3h']
ALL_WEATHER_COLS = WEATHER_COLS + NEW_WEATHER_COLS
TIME_COLS = ['sin_hour', 'cos_hour', 'sin_month', 'cos_month']
MOM_COLS = ['mom_1h', 'mom_2h', 'mom_3h', 'mom_6h', 'accumulation_proxy']

def get_aqi_bin_vectorized(pm25_array):
    bins = np.zeros_like(pm25_array, dtype=np.int64)
    bins[(pm25_array > 12.0) & (pm25_array <= 35.4)] = 1
    bins[(pm25_array > 35.4) & (pm25_array <= 55.4)] = 2
    bins[(pm25_array > 55.4) & (pm25_array <= 150.4)] = 3
    bins[pm25_array > 150.4] = 4
    return bins

class AQIMultiOutputMLP(nn.Module):
    def __init__(self, input_dim, horizons, num_classes):
        super(AQIMultiOutputMLP, self).__init__()
        self.horizons = horizons
        self.num_classes = num_classes
        
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
            nn.Linear(128, horizons * num_classes)
        )
        
    def forward(self, x):
        out = self.net(x)
        # Reshape to (batch, num_classes, horizons) for PyTorch CrossEntropyLoss
        out = out.view(-1, self.num_classes, self.horizons)
        return out

def prep_data_v3_multi_classification():
    print("Loading and preparing V3 data for multi-horizon classification...")
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
    
    df['precip_washout'] = 1 / (1 + np.exp(-(df['precipitation'] - 1.0) * 4))
    df['wind_stagnant'] = np.exp(-df['wind_speed_10m'])
    df['wind_clearing'] = 1 / (1 + np.exp(-(df['wind_speed_10m'] - 3.0) * 2))
    df['sin_wind_dir'] = np.sin(np.radians(df['wind_direction_10m']))
    df['cos_wind_dir'] = np.cos(np.radians(df['wind_direction_10m']))
    df['delta_temp_3h'] = df['temperature_2m'] - df['temperature_2m'].shift(3)
    df['delta_pressure_3h'] = df['surface_pressure'] - df['surface_pressure'].shift(3)
    df['delta_wind_speed_3h'] = df['wind_speed_10m'] - df['wind_speed_10m'].shift(3)
    
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
    mom_vals = df[MOM_COLS].values
    times = df['time'].values
    
    X_list, y_list, valid_times = [], [], []
    
    for i in range(23, len(df) - MAX_HORIZON):
        y_block = pm25_vals[i+1 : i+1+MAX_HORIZON]
        if np.isnan(y_block).any(): continue
        
        x_hist = pm25_vals[i-23 : i+1]
        if np.isnan(x_hist).any(): continue
        
        x_future_weather = weather_vals[i+1 : i+1+MAX_HORIZON].flatten()
        if np.isnan(x_future_weather).any(): continue
        
        x_mom = mom_vals[i]
        if np.isnan(x_mom).any(): continue
        
        x_full = np.concatenate([x_hist, x_future_weather, x_mom])
        y_bins = get_aqi_bin_vectorized(y_block)
        
        X_list.append(x_full)
        y_list.append(y_bins)
        valid_times.append(times[i])
        
    X_mat = np.array(X_list)
    y_mat = np.array(y_list)
    
    split_date = np.datetime64('2024-01-01')
    train_mask = np.array(valid_times) < split_date
    valid_mask = ~train_mask
    
    X_train, y_train = X_mat[train_mask], y_mat[train_mask]
    X_valid, y_valid = X_mat[valid_mask], y_mat[valid_mask]
    
    scaler_x = StandardScaler()
    X_train_scaled = scaler_x.fit_transform(X_train)
    X_valid_scaled = scaler_x.transform(X_valid)
    
    return X_train_scaled, y_train, X_valid_scaled, y_valid, scaler_x

def train():
    X_train, y_train, X_valid, y_valid, scaler_x = prep_data_v3_multi_classification()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training Multi-Output Classifier on {device} | Input Dim: {X_train.shape[1]}")
    
    # Compute class weights using all training targets flattened
    y_train_flat = y_train.flatten()
    classes = np.unique(y_train_flat)
    class_weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_train_flat)
    weight_tensor = torch.FloatTensor(class_weights).to(device)
    print(f"Computed Class Weights: {class_weights}")
    
    train_ds = TensorDataset(torch.FloatTensor(X_train), torch.LongTensor(y_train))
    valid_ds = TensorDataset(torch.FloatTensor(X_valid), torch.LongTensor(y_valid))
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    model = AQIMultiOutputMLP(X_train.shape[1], MAX_HORIZON, NUM_CLASSES).to(device)
    
    criterion = nn.CrossEntropyLoss(weight=weight_tensor)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_loss = float('inf')
    best_model_path = f'{MODELS_DIR}/aqi_classifier_mlp_v3_best.pt'
    
    for epoch in range(EPOCHS):
        model.train()
        t_loss = 0
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            pred = model(bx)
            loss = criterion(pred, by)
            loss.backward()
            optimizer.step()
            t_loss += loss.item()
            
        model.eval()
        v_loss = 0
        with torch.no_grad():
            for bx, by in valid_loader:
                bx, by = bx.to(device), by.to(device)
                pred = model(bx)
                loss = criterion(pred, by)
                v_loss += loss.item()
                
        avg_v = v_loss / len(valid_loader)
        scheduler.step(avg_v)
        
        if (epoch+1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:02d}/{EPOCHS} | Train Loss: {t_loss/len(train_loader):.4f} | Valid Loss: {avg_v:.4f}")
            
        if avg_v < best_loss:
            best_loss = avg_v
            torch.save(model.state_dict(), best_model_path)
            
    print(f"Training complete. Best Validation Loss: {best_loss:.4f}")
    
    # Validation evaluation at specific horizons
    model.load_state_dict(torch.load(best_model_path, weights_only=True))
    model.eval()
    
    all_preds = []
    with torch.no_grad():
        for bx, _ in valid_loader:
            bx = bx.to(device)
            # pred is (batch, num_classes, horizon)
            pred = model(bx)
            # get argmax over classes -> (batch, horizon)
            pred_class = torch.argmax(pred, dim=1)
            all_preds.append(pred_class.cpu().numpy())
            
    y_pred = np.concatenate(all_preds)
    
    print("\n--- Evaluation on Validation Set ---")
    for h in [1, 6, 12, 24, 48, 72]:
        h_idx = h - 1
        y_true_h = y_valid[:, h_idx]
        y_pred_h = y_pred[:, h_idx]
        
        acc = accuracy_score(y_true_h, y_pred_h)
        print(f"\nT+{h:02d}h Classification Report (Accuracy: {acc:.3f}):")
        print(classification_report(y_true_h, y_pred_h, target_names=['Good', 'Moderate', 'USG', 'Unhealthy', 'Hazardous']))

if __name__ == "__main__":
    if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
    train()

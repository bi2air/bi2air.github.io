import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import pickle

DATA_DIR = 'tmp/air-quality-analysis-upstream/data'
MODELS_DIR = 'models'
os.makedirs(MODELS_DIR, exist_ok=True)

MAX_HORIZON = 72
BATCH_SIZE = 128
EPOCHS = 50
LEARNING_RATE = 1e-3

# We only use Temporal Columns
TIME_COLS = ['sin_hour', 'cos_hour', 'sin_month', 'cos_month', 'sin_dow', 'cos_dow']

class DeltaSkipMLPTemporal(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DeltaSkipMLPTemporal, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, output_dim)
        )
        
    def forward(self, x, current_val):
        delta = self.net(x)
        return current_val + delta

def prep_data_temporal():
    print("Loading and preparing Temporal-Only data...")
    pm25_df = pd.read_csv(f'{DATA_DIR}/airnow_hanoi_pm25_2015_2025_clean.csv')
    pm25_df['time'] = pd.to_datetime(pm25_df['DATE']).dt.tz_localize(None)
    pm25_df = pm25_df[['time', 'raw_pm25']].rename(columns={'raw_pm25': 'pm25_ugm3'})
    
    df = pm25_df.copy()
    
    # --- Time Encodings ---
    df['hour'] = df['time'].dt.hour
    df['month'] = df['time'].dt.month
    df['dow'] = df['time'].dt.dayofweek
    
    df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12.0)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12.0)
    df['sin_dow'] = np.sin(2 * np.pi * df['dow'] / 7.0)
    df['cos_dow'] = np.cos(2 * np.pi * df['dow'] / 7.0)
    
    df = df.dropna().reset_index(drop=True)
    
    X, y, c_vals = [], [], []
    valid_indices = []
    
    for i in range(len(df) - MAX_HORIZON):
        if i % 10000 == 0:
            print(f"Processing row {i}/{len(df)}")
            
        current_time = df['time'].iloc[i]
        
        # Build temporal sequence for the next 72 hours
        x_future_time = []
        for h in range(1, MAX_HORIZON + 1):
            future_row = df.iloc[i + h]
            x_future_time.extend([
                future_row['sin_hour'], future_row['cos_hour'],
                future_row['sin_month'], future_row['cos_month'],
                future_row['sin_dow'], future_row['cos_dow']
            ])
            
        x_row = np.array(x_future_time)
        
        y_row = df['pm25_ugm3'].iloc[i+1 : i+MAX_HORIZON+1].values
        c_val = df['pm25_ugm3'].iloc[i]
        
        X.append(x_row)
        y.append(y_row)
        c_vals.append(c_val)
        
        if current_time >= pd.Timestamp('2023-01-01'):
            valid_indices.append(i)

    X = np.array(X)
    y = np.array(y)
    c_vals = np.array(c_vals)
    
    train_idx = list(set(range(len(X))) - set(valid_indices))
    
    X_train, y_train, c_train = X[train_idx], y[train_idx], c_vals[train_idx]
    X_valid, y_valid, c_valid = X[valid_indices], y[valid_indices], c_vals[valid_indices]
    
    scaler_x = StandardScaler()
    X_train_scaled = scaler_x.fit_transform(X_train)
    X_valid_scaled = scaler_x.transform(X_valid)
    
    return X_train_scaled, y_train, X_valid_scaled, y_valid, c_train, c_valid, scaler_x

class PM25Dataset(Dataset):
    def __init__(self, X, y, c):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
        self.c = torch.FloatTensor(c).unsqueeze(1)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx], self.c[idx]

def custom_weighted_loss(pred, target, weights):
    err = (pred - target) ** 2
    weighted_err = err * weights
    return weighted_err.mean()

def train():
    X_train, y_train, X_valid, y_valid, c_train, c_valid, scaler_x = prep_data_temporal()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training Temporal Delta-Skip on {device} | Input Dim: {X_train.shape[1]}")
    
    train_ds = PM25Dataset(X_train, y_train, c_train)
    valid_ds = PM25Dataset(X_valid, y_valid, c_valid)
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    model = DeltaSkipMLPTemporal(X_train.shape[1], MAX_HORIZON).to(device)
    
    weights = torch.ones(MAX_HORIZON).to(device)
    weights[0] = 20.0
    weights[5] = 10.0
    weights[11] = 5.0
    weights[23] = 2.0
    
    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    best_loss = float('inf')
    best_model_path = f'{MODELS_DIR}/t72_delta_skip_temporal_best.pt'
    
    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0
        for batch_X, batch_y, batch_c in train_loader:
            batch_X, batch_y, batch_c = batch_X.to(device), batch_y.to(device), batch_c.to(device)
            
            optimizer.zero_grad()
            pred = model(batch_X, batch_c)
            loss = custom_weighted_loss(pred, batch_y, weights)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            
        model.eval()
        valid_loss = 0
        with torch.no_grad():
            for batch_X, batch_y, batch_c in valid_loader:
                batch_X, batch_y, batch_c = batch_X.to(device), batch_y.to(device), batch_c.to(device)
                pred = model(batch_X, batch_c)
                loss = custom_weighted_loss(pred, batch_y, weights)
                valid_loss += loss.item()
                
        train_loss /= len(train_loader)
        valid_loss /= len(valid_loader)
        scheduler.step(valid_loss)
        
        if valid_loss < best_loss:
            best_loss = valid_loss
            torch.save(model.state_dict(), best_model_path)
            
        if (epoch+1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:02d}/{EPOCHS} | Train Loss: {train_loss:.4f} | Valid Loss: {valid_loss:.4f}")
            
    print(f"Training complete. Best Validation Loss: {best_loss:.4f}")
    
    model.load_state_dict(torch.load(best_model_path))
    model.eval()
    
    all_preds = []
    with torch.no_grad():
        for batch_X, batch_y, batch_c in valid_loader:
            batch_X, batch_c = batch_X.to(device), batch_c.to(device)
            pred = model(batch_X, batch_c)
            all_preds.append(pred.cpu().numpy())
            
    y_pred = np.vstack(all_preds)
    
    print("\n--- Evaluation on Validation Set ---")
    results = {}
    for h in [1, 6, 12, 24, 48, 72]:
        idx = h - 1
        rmse = np.sqrt(mean_squared_error(y_valid[:, idx], y_pred[:, idx]))
        r2 = r2_score(y_valid[:, idx], y_pred[:, idx])
        print(f"T+{h:02d}h | RMSE: {rmse:.3f} | R2: {r2:.3f}")
        results[h] = {"rmse": rmse, "r2": r2}
        
    ov_rmse = np.sqrt(mean_squared_error(y_valid.flatten(), y_pred.flatten()))
    ov_r2 = r2_score(y_valid.flatten(), y_pred.flatten())
    print(f"OVERALL | RMSE: {ov_rmse:.3f} | R2: {ov_r2:.3f}")

if __name__ == "__main__":
    train()

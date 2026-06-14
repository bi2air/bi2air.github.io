import pandas as pd
import numpy as np
import os
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, log_loss
import lightgbm as lgb

# --- CONFIG ---
DATA_DIR = 'tmp/air-quality-analysis-upstream/data'
MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'
TARGET_HORIZON = 24 # Predict AQI bin at T+24 as a starting point

WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation', 'shortwave_radiation', 'wind_direction_10m']
NEW_WEATHER_COLS = ['precip_washout', 'wind_stagnant', 'wind_clearing', 'sin_wind_dir', 'cos_wind_dir', 'delta_temp_3h', 'delta_pressure_3h', 'delta_wind_speed_3h']
ALL_WEATHER_COLS = WEATHER_COLS + NEW_WEATHER_COLS
TIME_COLS = ['sin_hour', 'cos_hour', 'sin_month', 'cos_month']
MOM_COLS = ['mom_1h', 'mom_2h', 'mom_3h', 'mom_6h', 'accumulation_proxy']

def get_aqi_bin(pm25):
    if pm25 <= 12.0: return 0
    elif pm25 <= 35.4: return 1
    elif pm25 <= 55.4: return 2
    elif pm25 <= 150.4: return 3
    else: return 4

def prep_data_v3_classification():
    print("Loading and preparing V3 data for classification...")
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
    df['sin_wind_dir'] = np.sin(np.radians(df['wind_direction_10m']))
    df['cos_wind_dir'] = np.cos(np.radians(df['wind_direction_10m']))
    df['delta_temp_3h'] = df['temperature_2m'] - df['temperature_2m'].shift(3)
    df['delta_pressure_3h'] = df['surface_pressure'] - df['surface_pressure'].shift(3)
    df['delta_wind_speed_3h'] = df['wind_speed_10m'] - df['wind_speed_10m'].shift(3)
    
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
    
    df.fillna(0, inplace=True)
    
    pm25_vals = df['pm25_ugm3'].values
    weather_vals = df[ALL_WEATHER_COLS + TIME_COLS].values
    mom_vals = df[MOM_COLS].values
    times = df['time'].values
    
    X_list, y_list, valid_times = [], [], []
    
    # We want to predict AQI at T+TARGET_HORIZON
    for i in range(23, len(df) - TARGET_HORIZON):
        y_val = pm25_vals[i + TARGET_HORIZON]
        if np.isnan(y_val): continue
        
        x_hist = pm25_vals[i-23 : i+1]
        if np.isnan(x_hist).any(): continue
        
        x_future_weather = weather_vals[i+1 : i+1+TARGET_HORIZON].flatten()
        if np.isnan(x_future_weather).any(): continue
        
        x_mom = mom_vals[i]
        if np.isnan(x_mom).any(): continue
        
        y_bin = get_aqi_bin(y_val)
        
        x_full = np.concatenate([x_hist, x_future_weather, x_mom])
        X_list.append(x_full)
        y_list.append(y_bin)
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

def train_classifier():
    X_train, y_train, X_valid, y_valid, scaler = prep_data_v3_classification()
    print(f"Train shapes: X={X_train.shape}, y={y_train.shape}")
    print(f"Valid shapes: X={X_valid.shape}, y={y_valid.shape}")
    
    unique, counts = np.unique(y_train, return_counts=True)
    print("Training class distribution:")
    for u, c in zip(unique, counts):
        print(f"Class {u}: {c} ({c/len(y_train)*100:.2f}%)")
        
    # Calculate class weights inversely proportional to class frequencies to handle severe imbalance (esp. for class 4)
    from sklearn.utils.class_weight import compute_class_weight
    class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y_train), y=y_train)
    class_weight_dict = {i: w for i, w in zip(np.unique(y_train), class_weights)}
    print(f"Computed class weights: {class_weight_dict}")
    
    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_eval = lgb.Dataset(X_valid, y_valid, reference=lgb_train)
    
    params = {
        'objective': 'multiclass',
        'num_class': 5,
        'metric': 'multi_logloss',
        'boosting_type': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'verbose': -1,
        'random_state': 42
    }
    
    print("Training LightGBM classifier...")
    gbm = lgb.train(
        params,
        lgb_train,
        num_boost_round=500,
        valid_sets=[lgb_eval],
        callbacks=[lgb.early_stopping(stopping_rounds=50)]
    )
    
    y_pred_probs = gbm.predict(X_valid, num_iteration=gbm.best_iteration)
    y_pred_class = np.argmax(y_pred_probs, axis=1)
    
    print("\n--- Evaluation on Validation Set ---")
    print(f"Log Loss: {log_loss(y_valid, y_pred_probs):.4f}")
    print(f"Accuracy: {accuracy_score(y_valid, y_pred_class):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_valid, y_pred_class, target_names=['Good', 'Moderate', 'USG', 'Unhealthy', 'Hazardous']))
    
    # Save the model
    if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
    with open(f'{MODELS_DIR}/aqi_classifier_t{TARGET_HORIZON}_v3.pkl', 'wb') as f:
        pickle.dump(gbm, f)
        
    print(f"Model saved to {MODELS_DIR}/aqi_classifier_t{TARGET_HORIZON}_v3.pkl")

if __name__ == "__main__":
    train_classifier()

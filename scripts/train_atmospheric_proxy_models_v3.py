import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, classification_report
import os
import pickle

DATA_DIR = 'tmp/air-quality-analysis-upstream/data'
MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'

WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation', 'shortwave_radiation', 'wind_direction_10m']
NEW_WEATHER_COLS = ['precip_washout', 'wind_stagnant', 'wind_clearing', 'sin_wind_dir', 'cos_wind_dir', 'delta_temp_3h', 'delta_pressure_3h', 'delta_wind_speed_3h']
ALL_WEATHER_COLS = WEATHER_COLS + NEW_WEATHER_COLS
TIME_COLS = ['hour', 'month', 'sin_hour', 'cos_hour', 'sin_month', 'cos_month']

def prep_data():
    print("Loading IGRA and Weather data for proxy model training...")
    igra_df = pd.read_csv(f'{DATA_DIR}/igra_hanoi_inversion_features_2015_2026.csv')
    igra_df['time'] = pd.to_datetime(igra_df['datetime']).dt.tz_convert('Asia/Ho_Chi_Minh').dt.tz_localize(None)
    
    weather_df = pd.read_csv(f'{DATA_DIR}/open_meteo_hanoi/open_meteo_hanoi_hourly_2015_2025.csv', low_memory=False)
    weather_df['time'] = pd.to_datetime(weather_df['time']).dt.tz_localize(None)
    
    df = weather_df.copy()
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
    
    merged = pd.merge(df, igra_df[['time', 'is_surface_inversion', 'is_very_stable']], on='time', how='inner')
    merged.dropna(subset=ALL_WEATHER_COLS + TIME_COLS + ['is_surface_inversion', 'is_very_stable'], inplace=True)
    
    return merged

def train_proxy():
    df = prep_data()
    features = ALL_WEATHER_COLS + TIME_COLS
    
    split_date = np.datetime64('2024-01-01')
    train_mask = df['time'] < split_date
    
    train_df = df[train_mask]
    valid_df = df[~train_mask]
    
    X_train = train_df[features]
    X_valid = valid_df[features]
    
    for target in ['is_surface_inversion', 'is_very_stable']:
        y_train = train_df[target]
        y_valid = valid_df[target]
        
        pos_weight = (len(y_train) - y_train.sum()) / max(1, y_train.sum())
        print(f"\n--- Training {target} ---")
        print(f"Positive ratio: {y_train.mean():.4f} | scale_pos_weight: {pos_weight:.2f}")
        
        model = lgb.LGBMClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=pos_weight,
            random_state=42
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_valid, y_valid)],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)]
        )
        
        preds_proba = model.predict_proba(X_valid)[:, 1]
        auc = roc_auc_score(y_valid, preds_proba)
        preds = model.predict(X_valid)
        
        print(f"\n[{target}] Validation AUC: {auc:.4f}")
        print(classification_report(y_valid, preds))
        
        with open(f'{MODELS_DIR}/proxy_{target}_v3.pkl', 'wb') as f:
            pickle.dump(model, f)
            
if __name__ == "__main__":
    if not os.path.exists(MODELS_DIR): os.makedirs(MODELS_DIR)
    train_proxy()

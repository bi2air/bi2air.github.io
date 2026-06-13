import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
import importlib.util

# Load V3 validation data (targets are identical across V3/V4, only X changes)
script_path = 'scripts/train_t72_delta_skip_v3.py'
spec = importlib.util.spec_from_file_location("data_mod_v3", script_path)
data_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_mod)

X_train, y_train, X_valid, y_valid, c_train, c_valid, scaler_x = data_mod.prep_data_v3()

horizons = [1, 6, 12, 24, 48, 72]
print("--- Naive Baselines ---")

# Nowcast (Persistence): Prediction is simply current PM2.5 value (which is c_valid)
for h in horizons:
    idx = h - 1
    y_true = y_valid[:, idx]
    # For nowcast, we just predict the current value (T=0). 
    # Because our model target is y = delta + current, meaning y_true = current + delta. 
    # Therefore, current = c_valid.
    y_pred_nowcast = c_valid
    rmse_nowcast = np.sqrt(mean_squared_error(y_true, y_pred_nowcast))
    print(f"T+{h:02d}h | Nowcast RMSE: {rmse_nowcast:.3f}")

# Rolling mean (e.g. 24h historical mean)
# Since c_valid is the current value, to get the 24h rolling mean we'd need the historical PM2.5 sequence.
# Let's extract mom_1h to mom_24h from X_valid.
# Actually, the user's data prep might only have mom_1h, mom_2h, mom_3h, mom_6h. 
# Let's check X_train.shape to see if we can compute rolling. We don't have exactly 24h history.
# Let's approximate rolling mean using the current value and the available momentum terms.
# Or better yet, just use the raw DataFrame to calculate rolling mean.

DATA_DIR = 'tmp/air-quality-analysis-upstream/data'
pm25_df = pd.read_csv(f'{DATA_DIR}/airnow_hanoi_pm25_2015_2025_clean.csv')
pm25_df['time'] = pd.to_datetime(pm25_df['DATE']).dt.tz_localize(None)
pm25_df = pm25_df[['time', 'raw_pm25']].rename(columns={'raw_pm25': 'pm25_ugm3'})
pm25_df['rolling_24h'] = pm25_df['pm25_ugm3'].rolling(window=24, min_periods=1).mean()

# Align the rolling mean with the validation dataset.
# The split is at '2023-01-01'. 
valid_df = pm25_df[pm25_df['time'] >= '2023-01-01'].copy()
valid_df = valid_df.reset_index(drop=True)

# For each horizon h, the true value is pm25_ugm3 shifted by -h.
# The prediction is rolling_24h at the current step.
for h in horizons:
    valid_df[f'target_{h}h'] = valid_df['pm25_ugm3'].shift(-h)

valid_df = valid_df.dropna()

print("\n--- Raw DataFrame Rolling Mean Baseline (Post 2023) ---")
for h in horizons:
    y_true = valid_df[f'target_{h}h']
    y_pred = valid_df['rolling_24h']
    rmse_rolling = np.sqrt(mean_squared_error(y_true, y_pred))
    print(f"T+{h:02d}h | Rolling 24h RMSE: {rmse_rolling:.3f}")
    
print("\n--- Raw DataFrame Nowcast Baseline (Post 2023) ---")
for h in horizons:
    y_true = valid_df[f'target_{h}h']
    y_pred = valid_df['pm25_ugm3']
    rmse_now = np.sqrt(mean_squared_error(y_true, y_pred))
    print(f"T+{h:02d}h | Nowcast RMSE: {rmse_now:.3f}")

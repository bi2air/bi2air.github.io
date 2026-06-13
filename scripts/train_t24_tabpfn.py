import numpy as np
import torch
import importlib.util
from sklearn.metrics import mean_squared_error, r2_score
import sys

def run_tabpfn_t24():
    try:
        from tabpfn import TabPFNRegressor
    except ImportError:
        print("TabPFN is not installed. Please install it with 'pip install tabpfn'.")
        return

    # Load prep_data_v2
    TRAIN_SCRIPT = 'scripts/train_t72_delta_skip_v2.py'
    spec = importlib.util.spec_from_file_location("train_mod", TRAIN_SCRIPT)
    train_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(train_mod)
    
    print("Loading V2 Data...")
    X_train, y_train, X_valid, y_valid, c_train, c_valid, scaler_x = train_mod.prep_data_v2()
    
    # We want to isolate T+24. Index is 23.
    target_idx = 23
    y_train_24 = y_train[:, target_idx]
    y_valid_24 = y_valid[:, target_idx]
    
    # Isolate Features
    # 0:24 -> History
    # 24:960 -> Future weather (72 steps * 13 cols)
    # 960:965 -> Momentum
    
    # T+24 weather features start at 24 + 23*13 = 323
    w_start = 24 + 23 * 13
    w_end = w_start + 13
    
    hist_idx = list(range(24))
    weath_idx = list(range(w_start, w_end))
    mom_idx = list(range(960, 965))
    
    selected_features = hist_idx + weath_idx + mom_idx
    print(f"Selected {len(selected_features)} features for TabPFN.")
    
    X_train_sub = X_train[:, selected_features]
    X_valid_sub = X_valid[:, selected_features]
    
    # TabPFN is memory intensive and fits max 10k samples
    MAX_SAMPLES = 10000
    if X_train_sub.shape[0] > MAX_SAMPLES:
        print(f"Subsampling training data from {X_train_sub.shape[0]} to {MAX_SAMPLES}...")
        indices = np.random.choice(X_train_sub.shape[0], MAX_SAMPLES, replace=False)
        X_train_sub = X_train_sub[indices]
        y_train_24 = y_train_24[indices]
        
    print(f"Training TabPFN on {X_train_sub.shape[0]} samples...")
    reg = TabPFNRegressor(device='cuda' if torch.cuda.is_available() else 'cpu')
    reg.fit(X_train_sub, y_train_24)
    
    print("Predicting on validation set...")
    # Process in batches if validation is too large
    preds = []
    batch_sz = 1000
    for i in range(0, len(X_valid_sub), batch_sz):
        b = X_valid_sub[i:i+batch_sz]
        p = reg.predict(b)
        preds.append(p)
    
    y_pred = np.concatenate(preds)
    
    rmse = np.sqrt(mean_squared_error(y_valid_24, y_pred))
    r2 = r2_score(y_valid_24, y_pred)
    
    print("\n--- TabPFN Results (T+24h) ---")
    print(f"RMSE: {rmse:.3f}")
    print(f"R2:   {r2:.3f}")

if __name__ == "__main__":
    run_tabpfn_t24()

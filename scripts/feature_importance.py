import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import os
import importlib.util
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# --- CONFIG ---
DATA_DIR = 'tmp/air-quality-analysis-upstream/data'
MODELS_DIR = 'tmp/air-quality-analysis-upstream/models/pipeline'
TRAIN_SCRIPT = 'tmp/air-quality-analysis-upstream/scripts/train_t72_delta_skip.py'
MODEL_WEIGHTS = f'{MODELS_DIR}/t72_delta_skip_best.pt'
MAX_HORIZON = 72
BATCH_SIZE = 1024

WEATHER_COLS = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'surface_pressure', 'cloud_cover', 'precipitation']
TIME_COLS = ['sin_hour', 'cos_hour', 'sin_month', 'cos_month']

def load_data_and_model():
    # Load prep_data and DeltaSkipMLP dynamically
    spec = importlib.util.spec_from_file_location("train_mod", TRAIN_SCRIPT)
    train_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(train_mod)
    
    print("Preparing data...")
    X_train_scaled, y_train, X_valid_scaled, y_valid, c_train, c_valid, scaler_x = train_mod.prep_data()
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("Loading model...")
    model = train_mod.DeltaSkipMLP(X_valid_scaled.shape[1], MAX_HORIZON).to(device)
    model.load_state_dict(torch.load(MODEL_WEIGHTS, map_location=device, weights_only=True))
    model.eval()
    
    return X_valid_scaled, y_valid, c_valid, model, device

def evaluate(model, X, C, y, device):
    ds = TensorDataset(torch.FloatTensor(X), torch.FloatTensor(y), torch.FloatTensor(C))
    loader = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False)
    
    all_preds = []
    with torch.no_grad():
        for bx, by, bc in loader:
            bx, bc = bx.to(device), bc.to(device)
            pred = model(bx, bc)
            all_preds.append(pred.cpu().numpy())
            
    y_pred = np.concatenate(all_preds)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    return rmse

def permutation_importance():
    X_valid, y_valid, c_valid, model, device = load_data_and_model()
    
    print("Evaluating baseline...")
    baseline_rmse = evaluate(model, X_valid, c_valid, y_valid, device)
    print(f"Baseline RMSE: {baseline_rmse:.4f}")
    
    # Define feature groups and their indices
    feature_groups = {}
    feature_groups['pm25_history'] = list(range(24))
    
    weather_start = 24
    for idx, col in enumerate(WEATHER_COLS + TIME_COLS):
        group_indices = [weather_start + i * 10 + idx for i in range(MAX_HORIZON)]
        feature_groups[col] = group_indices
        
    mom_start = 24 + 720
    feature_groups['momentum'] = list(range(mom_start, mom_start + 4))
    
    importance = {}
    
    print("Running permutation tests...")
    for group_name, indices in feature_groups.items():
        X_shuffled = X_valid.copy()
        shuffled_rows = np.random.permutation(X_shuffled.shape[0])
        X_shuffled[:, indices] = X_shuffled[shuffled_rows][:, indices]
        
        shuffled_rmse = evaluate(model, X_shuffled, c_valid, y_valid, device)
        imp = shuffled_rmse - baseline_rmse
        importance[group_name] = imp
        print(f"Group: {group_name:20s} | Shuffled RMSE: {shuffled_rmse:.4f} | Importance (Delta RMSE): {imp:.4f}")
        
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=False)
    
    names = [x[0] for x in sorted_imp]
    scores = [x[1] for x in sorted_imp]
    
    plt.figure(figsize=(10, 6))
    plt.barh(names, scores, color='skyblue')
    plt.xlabel('Increase in RMSE (Importance)')
    plt.title('Permutation Feature Importance (Validation Set)')
    plt.tight_layout()
    out_path = 'doc-work/feature_importance.png'
    plt.savefig(out_path)
    print(f"\nSaved plot to {out_path}")
    
    with open('doc-work/feature_importance_log.md', 'w') as f:
        f.write("# Feature Importance Results\n\n")
        f.write(f"Baseline Validation RMSE: **{baseline_rmse:.4f}**\n\n")
        f.write("| Feature Group | Increase in RMSE | Status |\n")
        f.write("|---|---|---|\n")
        for name, score in sorted_imp[::-1]:
            status = "Strong" if score > 0.5 else "Weak/Noise" if score < 0.1 else "Moderate"
            f.write(f"| {name} | {score:.4f} | {status} |\n")

if __name__ == '__main__':
    permutation_importance()

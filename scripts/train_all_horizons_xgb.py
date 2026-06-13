import numpy as np
import importlib.util
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")

def load_data(version):
    script_path = f'scripts/train_t72_delta_skip_{version}.py'
    spec = importlib.util.spec_from_file_location(f"data_mod_{version}", script_path)
    data_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_mod)
    
    if version == 'v3':
        return data_mod.prep_data_v3()
    elif version == 'v4':
        return data_mod.prep_data_v4()

def run_horizons_for_version(version):
    print(f"\n========================================")
    print(f"XGBoost Multi-Horizon Evaluation ({version.upper()})")
    print(f"========================================")
    
    X_train, y_train, X_valid, y_valid, c_train, c_valid, scaler_x = load_data(version)
    horizons = [1, 6, 12, 24, 48, 72]
    
    results = {}
    
    for h in horizons:
        idx = h - 1
        y_train_h = y_train[:, idx]
        y_valid_h = y_valid[:, idx]
        
        model = xgb.XGBRegressor(
            n_estimators=100, # slightly reduced for speed across 6 horizons
            learning_rate=0.1,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            tree_method='hist',
            device='cuda',
            random_state=42
        )
        
        model.fit(X_train, y_train_h, verbose=False)
        y_pred = model.predict(X_valid)
        rmse = np.sqrt(mean_squared_error(y_valid_h, y_pred))
        
        print(f"T+{h:02d}h | XGBoost RMSE: {rmse:.3f}")
        results[h] = rmse
        
    return results

if __name__ == "__main__":
    try:
        results_v3 = run_horizons_for_version('v3')
        results_v4 = run_horizons_for_version('v4')
        
        print("\n\nFINAL COMBINED RESULTS (RMSE)")
        print(f"{'Horizon':<10} | {'XGB-V3':<10} | {'XGB-V4':<10}")
        print("-" * 35)
        for h in [1, 6, 12, 24, 48, 72]:
            print(f"T+{h:02d}h      | {results_v3[h]:<10.3f} | {results_v4[h]:<10.3f}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

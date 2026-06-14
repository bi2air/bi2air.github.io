import numpy as np
import importlib.util
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import warnings

warnings.filterwarnings("ignore")

def load_data(version):
    if version == 'v3_proxies':
        script_path = 'scripts/train_t72_delta_skip_v3_phase3.py'
        spec = importlib.util.spec_from_file_location("data_mod_v3_proxies", script_path)
        data_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_mod)
        return data_mod.prep_data_phase3()
    elif version == 'v4_proxies':
        script_path = 'scripts/train_v4_pipeline.py'
        spec = importlib.util.spec_from_file_location("data_mod_v4_proxies", script_path)
        data_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_mod)
        return data_mod.prep_data_v4()

def run_horizons_for_version(version):
    print(f"\n========================================")
    print(f"XGBoost Multi-Horizon Evaluation ({version.upper()})")
    print(f"========================================")
    
    X_train, y_train, X_valid, y_valid, c_train, c_valid = load_data(version)
    horizons = [1, 6, 12, 24, 48, 72]
    
    results = {}
    
    for h in horizons:
        idx = h - 1
        y_train_h = y_train[:, idx]
        y_valid_h = y_valid[:, idx]
        
        model = xgb.XGBRegressor(
            n_estimators=100,
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
        results_v3 = run_horizons_for_version('v3_proxies')
        results_v4 = run_horizons_for_version('v4_proxies')
        
        print("\n\nFINAL COMBINED RESULTS (RMSE)")
        print(f"{'Horizon':<10} | {'XGB-V3-Proxies':<20} | {'XGB-V4-Proxies':<20}")
        print("-" * 55)
        for h in [1, 6, 12, 24, 48, 72]:
            print(f"T+{h:02d}h      | {results_v3[h]:<20.3f} | {results_v4[h]:<20.3f}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

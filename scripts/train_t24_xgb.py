import numpy as np
import importlib.util
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb

def load_data(version):
    script_path = f'scripts/train_t72_delta_skip_{version}.py'
    spec = importlib.util.spec_from_file_location(f"data_mod_{version}", script_path)
    data_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_mod)
    
    if version == 'v3':
        return data_mod.prep_data_v3()
    elif version == 'v4':
        return data_mod.prep_data_v4()

def train_eval_xgb(version):
    print(f"\n{'='*40}")
    print(f"Running XGBoost for T+24 with {version.upper()} dataset")
    print(f"{'='*40}")
    
    X_train, y_train, X_valid, y_valid, c_train, c_valid, scaler_x = load_data(version)
    
    # Isolate T+24 (index 23)
    target_idx = 23
    y_train_24 = y_train[:, target_idx]
    y_valid_24 = y_valid[:, target_idx]
    
    print(f"Input dimensions: {X_train.shape[1]}")
    
    # Train XGBoost
    model = xgb.XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method='hist',
        device='cuda',
        random_state=42
    )
    
    print("Training XGBoost...")
    model.fit(
        X_train, y_train_24,
        eval_set=[(X_valid, y_valid_24)],
        verbose=False
    )
    
    print("Evaluating...")
    y_pred = model.predict(X_valid)
    
    rmse = np.sqrt(mean_squared_error(y_valid_24, y_pred))
    r2 = r2_score(y_valid_24, y_pred)
    
    print(f"--- {version.upper()} XGBoost Results (T+24h) ---")
    print(f"RMSE: {rmse:.3f}")
    print(f"R2:   {r2:.3f}")
    
    return rmse

if __name__ == "__main__":
    try:
        rmse_v3 = train_eval_xgb('v3')
        rmse_v4 = train_eval_xgb('v4')
        
        print("\n" + "*"*40)
        print("FINAL COMPARISON: T+24h RMSE")
        print("*"*40)
        print(f"V3 Dataset (1469 dims): {rmse_v3:.3f}")
        print(f"V4 Dataset (1901 dims): {rmse_v4:.3f}")
        if rmse_v4 < rmse_v3:
            print("Winner: V4 (XGBoost handled the wide features!)")
        else:
            print("Winner: V3 (V4 features were still too noisy)")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

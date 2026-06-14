#!/usr/bin/env python3
"""
Run RandomForest on 2018 data to get complete metrics (RMSE, MAE, R²)
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

print("="*60)
print("2018 Hanoi PM2.5 - RandomForest Analysis")
print("="*60)

# Load data
print("\n1. Loading data...")
df = pd.read_csv('data/comb_PM25_wind_Hanoi_2018_v3.csv',
                 parse_dates=['DATE'],
                 index_col=['DATE'])
print(f"   Dataset shape: {df.shape}")

# Drop weakly correlated features
df.drop(columns=['CLDCR', 'v_2m', 'v_50m', 'v_850', 'FRCAN', 'DISPH'], inplace=True)

# Split features and target
X = df.drop('PM2.5', axis=1)
y = df['PM2.5'].copy()

print(f"   Target mean: {y.mean():.2f} µg/m³")

# Preprocessing
def inpute_transform(data=None):
    num_pipeline = Pipeline([
        ('inputer', SimpleImputer(strategy='median')),
        ('std_scaler', StandardScaler()),
    ])
    num_attrs = list(data.columns)
    full_pipeline = ColumnTransformer([
        ('num', num_pipeline, num_attrs)
    ])
    return full_pipeline.fit_transform(data)

print("\n2. Preprocessing data...")
X_scaled = inpute_transform(data=X)

# Split data (matching original: 33% test, random_state=2020)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.33, random_state=2020
)

print(f"   Train set: {len(X_train)} samples")
print(f"   Test set: {len(X_test)} samples")

# Train RandomForest
print("\n3. Training RandomForest...")
rf_reg = RandomForestRegressor(random_state=42, n_jobs=-1)
rf_reg.fit(X_train, y_train)
print("   ✓ Training complete")

# Predictions
rf_pred = rf_reg.predict(X_test)

# Calculate metrics
rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
mae = mean_absolute_error(y_test, rf_pred)
r2 = r2_score(y_test, rf_pred)

print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(f"Random Forest Performance:")
print(f"  RMSE: {rmse:.1f} µg/m³")
print(f"  MAE:  {mae:.1f} µg/m³")
print(f"  R²:   {r2:.3f}")
print("="*60)

# Save results
results = {
    'model': 'Random Forest',
    'rmse': float(rmse),
    'mae': float(mae),
    'r2': float(r2),
    'split': 'random',
    'test_size': 0.33,
    'random_state': 2020
}

import json
with open('rf_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Results saved to: rf_results.json")

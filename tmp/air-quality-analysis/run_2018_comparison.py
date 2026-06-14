#!/usr/bin/env python3
"""
2018 Hanoi PM2.5 Model Comparison
This script reproduces the 2018 model comparison with RandomForest and other models,
ordered by RMSE from worst to best.
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LinearRegression, RidgeCV
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

print("="*60)
print("2018 Hanoi PM2.5 Model Comparison")
print("="*60)

# Load and prepare data
print("\n1. Loading data...")
df = pd.read_csv('data/comb_PM25_wind_Hanoi_2018_v3.csv',
                 parse_dates=['DATE'],
                 index_col=['DATE'])
print(f"   Dataset shape: {df.shape}")

# Drop weakly correlated or redundant features
df.drop(columns=['CLDCR', 'v_2m', 'v_50m', 'v_850', 'FRCAN', 'DISPH'], inplace=True)

# Split features and target
X = df.drop('PM2.5', axis=1)
y = df['PM2.5'].copy()

print(f"   Features: {list(X.columns)}")
print(f"   Target mean: {y.mean():.2f} µg/m³")

# Create preprocessing pipeline
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

# Split data (matching the original notebook's random_state)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.33, random_state=2020
)

print(f"   Train set: {len(X_train)} samples")
print(f"   Test set: {len(X_test)} samples")

# Train and evaluate models
print("\n3. Training models...")

model_results = []

def add_model_result(name, y_true, y_pred):
    model_results.append({
        'model': name,
        'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
        'mae': float(mean_absolute_error(y_true, y_pred)),
        'r2': float(r2_score(y_true, y_pred)),
    })

# Baseline: predict mean
baseline_pred = np.full(len(y_test), y_train.mean())
add_model_result('Mean baseline', y_test, baseline_pred)
print(f"   ✓ Mean baseline: RMSE = {np.sqrt(mean_squared_error(y_test, baseline_pred)):.1f}")

# Linear regression (weather only)
lin_reg = LinearRegression()
lin_reg.fit(X_train, y_train)
lin_pred = lin_reg.predict(X_test)
add_model_result('Linear weather', y_test, lin_pred)
print(f"   ✓ Linear weather: RMSE = {np.sqrt(mean_squared_error(y_test, lin_pred)):.1f}")

# Polynomial Ridge (degree 2)
poly_ridge = make_pipeline(
    PolynomialFeatures(degree=2, include_bias=False),
    RidgeCV(alphas=np.logspace(-2, 4, 20))
)
poly_ridge.fit(X_train, y_train)
poly_pred = poly_ridge.predict(X_test)
add_model_result('Poly2 Ridge', y_test, poly_pred)
print(f"   ✓ Poly2 Ridge: RMSE = {np.sqrt(mean_squared_error(y_test, poly_pred)):.1f}")

# Random Forest
rf_reg = RandomForestRegressor(random_state=42, n_jobs=-1)
rf_reg.fit(X_train, y_train)
rf_pred = rf_reg.predict(X_test)
add_model_result('Random Forest', y_test, rf_pred)
print(f"   ✓ Random Forest: RMSE = {np.sqrt(mean_squared_error(y_test, rf_pred)):.1f}")

# Extra Trees
et_reg = ExtraTreesRegressor(n_estimators=400, random_state=42, n_jobs=-1)
et_reg.fit(X_train, y_train)
et_pred = et_reg.predict(X_test)
add_model_result('Extra Trees', y_test, et_pred)
print(f"   ✓ Extra Trees: RMSE = {np.sqrt(mean_squared_error(y_test, et_pred)):.1f}")

# Histogram Gradient Boosting
hgb_reg = HistGradientBoostingRegressor(random_state=42)
hgb_reg.fit(X_train, y_train)
hgb_pred = hgb_reg.predict(X_test)
add_model_result('HGB weather', y_test, hgb_pred)
print(f"   ✓ HGB weather: RMSE = {np.sqrt(mean_squared_error(y_test, hgb_pred)):.1f}")

# Results summary
print("\n4. Results summary...")
results_df = pd.DataFrame(model_results).sort_values('rmse', ascending=False).reset_index(drop=True)

print("\nModel Performance (sorted worst to best by RMSE):")
print("="*60)
print(results_df.to_string(index=False))

# Create bar chart ordered from worst to best
print("\n5. Creating visualization...")

fig, ax = plt.subplots(figsize=(10, 6))

# Sort from worst to best (descending RMSE)
results_sorted = results_df.sort_values('rmse', ascending=False)

# Create color gradient (red for worst, green for best)
colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.9, len(results_sorted)))

bars = ax.barh(results_sorted['model'], results_sorted['rmse'], color=colors, edgecolor='black', linewidth=0.8)

# Add RMSE values on the bars
for i, (idx, row) in enumerate(results_sorted.iterrows()):
    ax.text(row['rmse'] + 0.5, i, f"{row['rmse']:.1f}",
            va='center', ha='left', fontsize=10, fontweight='bold')

ax.set_xlabel('RMSE (µg/m³)', fontsize=12, fontweight='bold')
ax.set_ylabel('Model', fontsize=12, fontweight='bold')
ax.set_title('Hanoi PM2.5 Model Comparison (2018)\nOrdered by RMSE: Worst to Best',
             fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.set_xlim(0, max(results_sorted['rmse']) * 1.15)

plt.tight_layout()
plt.savefig('img/2018_model_comparison_worst_to_best.png', dpi=300, bbox_inches='tight')
print("   ✓ Chart saved to: img/2018_model_comparison_worst_to_best.png")

# Summary statistics
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
best_idx = results_df['rmse'].idxmin()
worst_idx = results_df['rmse'].idxmax()

print(f"Best model: {results_df.loc[best_idx, 'model']}")
print(f"  RMSE: {results_df.loc[best_idx, 'rmse']:.1f} µg/m³")
print(f"  MAE:  {results_df.loc[best_idx, 'mae']:.1f} µg/m³")
print(f"  R²:   {results_df.loc[best_idx, 'r2']:.3f}")
print(f"\nWorst model: {results_df.loc[worst_idx, 'model']}")
print(f"  RMSE: {results_df.loc[worst_idx, 'rmse']:.1f} µg/m³")
print(f"\nImprovement: {(results_df.loc[worst_idx, 'rmse'] - results_df.loc[best_idx, 'rmse']):.1f} µg/m³ ({100*(results_df.loc[worst_idx, 'rmse'] - results_df.loc[best_idx, 'rmse'])/results_df.loc[worst_idx, 'rmse']:.1f}%)")
print(f"\nDataset: Hanoi 2018 (weather-only features)")
print(f"Test set size: {len(y_test)} samples (33% of data)")
print(f"Random seed: 2020")
print("="*60)

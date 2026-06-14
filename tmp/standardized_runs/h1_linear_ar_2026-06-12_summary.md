## T+1h Summary Table

**Dataset:** `tmp/air-quality-analysis-upstream/data/forecast_ready/hanoi_pm25_open_meteo_forecast_h1_2015_2025.csv`  
**Holdout split:** `DATE < 2024-01-01 train, DATE >= 2024-01-01 valid`

> Note: the current standardized framework uses a single post-2024 holdout block. This table reports holdout-set metrics, not a separate validation-plus-test protocol.

| Method | Fitting Method | Feature Scope | Features | Train N | Holdout N | RMSE | MAE | R² |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Linear AR | LinearRegression | Linear AR subset | 15 | 38648 | 6986 | 14.065 | 7.905 | 0.785 |


---
layout: default
title: Hanoi PM2.5 Forecasting Experiments
parent: PM2.5 Forecasting
grand_parent: "2026"
nav_order: 4
description: "A 2026 single-station forecasting study for Hanoi PM$\_{2.5}$ using XGBoost, Open-Meteo forecasts, MERRA-2 reanalysis, and IGRA radiosonde features."
---

# Hanoi PM$\_{2.5}$ Forecasting Experiments (2026)

![Hanoi PM2.5 forecast short horizons](/assets/images/research/2026-forecast-short-horizon.png)
*Short-horizon forecasts (T+1h, T+12h) vs actual PM$\_{2.5}$, 1–8 March 2025. Bottom panel shows prediction error per hour.*

![Hanoi PM2.5 forecast medium horizons](/assets/images/research/2026-forecast-medium-horizon.png)
*Medium-horizon forecasts (T+24h, T+72h) vs actual. Bottom panel shows how error grows with lead time.*

{: .note }
This page adapts a June 2026 research writeup into site format for local Jekyll publishing. The underlying study evaluates single-station PM$\_{2.5}$ forecasting for Hanoi across six lead times using hourly data from 2015-01-01 through 2025-04-09.

---

## Executive Summary

The best short-horizon model was the T+1h baseline configuration, reaching RMSE 12.70 $\mu g/m^3$, MAE 7.32 $\mu g/m^3$, and $R^2$ 0.825. Longer horizons degraded gradually but still beat persistence across the full range from T+1h to T+72h.

The most useful experimental result was not a dramatic accuracy gain from extra features, but a clearer separation between what helps and what does not:

- `MERRA-2` boundary-layer features added small but repeatable value at `T+24h` to `T+72h`.
- `IGRA` radiosonde inversion features did not improve forecast accuracy in this setup.
- `T+6h` was the most promising horizon for severe-event warning within this dataset.
- Simple temporal flags were not a substitute for recent PM$\_{2.5}$ state and forecast meteorology.

## Best Results by Horizon

| Horizon | RMSE ($\mu g/m^3$) | MAE ($\mu g/m^3$) | R$^2$ | Skill vs Persistence | Best Configuration |
| --- | ---: | ---: | ---: | ---: | --- |
| `T+1h` | 12.70 | 7.32 | 0.825 | +13.6% | Baseline |
| `T+6h` | 19.34 | 12.54 | 0.596 | +30.2% | Baseline |
| `T+12h` | 20.90 | 13.94 | 0.525 | +30.3% | Baseline |
| `T+24h` | 21.76 | 14.68 | 0.464 | +24.0% | `MERRA-2` |
| `T+48h` | 23.40 | 15.87 | 0.385 | +30.2% | `MERRA-2` |
| `T+72h` | 23.69 | 16.33 | 0.400 | +33.6% | `MERRA-2` |

## Data and Modeling Setup

### Data Sources

- **PM$\_{2.5}$ observations**: hourly single-station series for Hanoi, `44,717` observations.
- **Open-Meteo forecasts**: archived forecast fields used as operationally realistic weather inputs.
- **MERRA-2 reanalysis**: boundary-layer and near-surface atmospheric variables, especially `PBLH`.
- **IGRA radiosonde**: twice-daily upper-air soundings converted into inversion and stability features.

### Feature Groups

The experiment compared several feature sets:

- **Baseline (76 features)**: PM$\_{2.5}$ lags, rolling statistics, current state, current weather, forecast weather, and basic temporal fields.
- **Enhanced temporal**: extra flags for rush hour, dry season, and burning season.
- **MERRA-2**: boundary-layer height, wind profile, cloud layers, and derived stability variables.
- **IGRA observed**: inversion strength, inversion base/depth, mixed-layer depth, and related flags.
- **Proxy models**: predicted atmospheric features intended to approximate MERRA-2 or inversion conditions for operations.

### Training Split

- **Training**: `2015-01-01` through `2023-12-31`
- **Validation**: `2024-01-01` through `2025-04-09`
- **Model family**: `XGBoost 3.2.0`
- **Acceleration**: GPU training with CUDA

## Main Results

### 1. Persistence Is Strong, But Beat-able

Persistence remained difficult to beat at `T+1h`, which is expected in air-quality nowcasting. Even so, the baseline model still improved on it by `13.6%`.

At longer lead times the improvement over persistence increased:

- `T+6h`: `+30.2%`
- `T+12h`: `+30.3%`
- `T+24h`: `+24.0%`
- `T+48h`: `+30.2%`
- `T+72h`: `+33.6%`

That pattern matters because it shows the model is doing more than just smoothing the recent PM$\_{2.5}$ signal.

### 2. MERRA-2 Added Small but Real Value

For the medium-range horizons, `MERRA-2` was the only added feature block that consistently helped:

| Horizon | Baseline RMSE | Best `MERRA-2` RMSE | Improvement |
| --- | ---: | ---: | ---: |
| `T+24h` | 22.06 | 21.76 | 1.39% |
| `T+48h` | 23.67 | 23.40 | 1.13% |
| `T+72h` | 24.01 | 23.69 | 1.37% |

The strongest physical interpretation is straightforward: boundary-layer structure affects whether pollutants remain trapped near the surface or disperse.

The most useful variables in this group were:

- `PBLH`
- `wind_speed_10m`
- `stability_index`
- `wind_shear`

### 3. IGRA Inversion Features Did Not Help

The radiosonde-based inversion features were physically motivated, but they did not improve forecast accuracy in practice.

The likely reasons are:

- soundings are available only `2x/day`
- forward-filled upper-air states become stale quickly
- `MERRA-2` already captures much of the same mixing physics with hourly coverage

This is a valuable negative result. It suggests that sparse upper-air observations are not automatically useful for a single-station PM$\_{2.5}$ forecast pipeline.

### 4. Proxy Atmospheric Models Were Not Good Enough

The study also tested whether forecast-time proxy models could replace unavailable reanalysis variables. Those proxies were too noisy to beat using the original weather features directly.

Binary atmospheric-state classifiers performed much better than regression proxies, but they still did not translate into better PM$\_{2.5}$ forecasts in this round of experiments.

### 5. Temporal Patterns Alone Were Not Predictive

Hanoi shows clear seasonal and diurnal PM$\_{2.5}$ structure, but temporal features alone were a poor forecasting model.

At `T+1h`:

| Configuration | RMSE ($\mu g/m^3$) | R$^2$ |
| --- | ---: | ---: |
| Temporal-only | 34.2 | -0.25 |
| Persistence | 14.7 | n/a |
| Baseline | 12.7 | 0.82 |

This is an important modeling lesson: descriptive climatology is not a replacement for recent state plus physical drivers.

## Severe Event Detection

The hard case in this dataset is extreme pollution: PM$\_{2.5}$ > 150 $\mu g/m^3$.

Only about `1.2%` of the hourly records were severe events, so the problem is highly imbalanced. Within this setup:

- `T+6h` was the best horizon for severe-event detection
- recall at `90%` precision was still only `8.2%`
- `T+48h` and `T+72h` effectively failed for this use case

That means the study is useful for continuous forecasting, but not yet reliable enough for high-confidence public alerts.

## Practical Takeaways

### Best Configuration by Use Case

| Use Case | Recommended Horizon | Recommended Feature Set | Reason |
| --- | --- | --- | --- |
| Near-real-time tracking | `T+1h` | Baseline | Best raw accuracy |
| Short warning window | `T+6h` | Baseline | Best severe-event tradeoff in this dataset |
| Daily planning | `T+24h` | `MERRA-2` | Best 24h RMSE |
| Multi-day planning | `T+48h` to `T+72h` | `MERRA-2` | Small but repeatable gain |

### Operational Constraint

`MERRA-2` is reanalysis, not a live forecast product. That makes it useful for retrospective modeling and feature discovery, but not directly deployable for real-time forecasting. A production system would need to replace those inputs with operational boundary-layer forecasts from a live NWP source.

## Limitations

- single monitoring station
- one train/validation split rather than repeated rolling-origin evaluation
- severe events are rare
- `MERRA-2` is not operationally available in real time
- literature comparison is based on reported metrics from heterogeneous studies

## Related Pages

- [PM$\_{2.5}$ Forecasting Literature Review](/docs/research/pm25-forecasting-literature-review.html)
- [Hanoi Forecasting Results vs Literature](/docs/research/hanoi-pm25-forecasting-literature-comparison.html)

## Source Note

This published page was prepared from the local draft set under `tmp/air-quality-analysis-upstream/doc-work/` and condensed for Jekyll site use.

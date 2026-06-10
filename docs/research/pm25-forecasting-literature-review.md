---
layout: default
title: PM$_{2.5}$ Forecasting Literature Review
parent: PM$_{2.5}$ Forecasting
grand_parent: "2026"
nav_order: 1
description: "A practitioner-oriented review of PM$_{2.5}$ forecasting methods, benchmark habits, and cross-study comparison pitfalls."
---

# PM$_{2.5}$ Forecasting Literature Review

{: .note }
This page is a cleaned site version of a June 2026 working review focused on single-station operational forecasting. It emphasizes method families, benchmark discipline, and how to compare published results without overstating cross-region conclusions.

---

## Executive Summary

Three recurring patterns stand out across the reviewed PM$_{2.5}$ forecasting literature:

1. **Gradient-boosted trees and LSTM models are the most credible single-station baselines.**
2. **Persistence is often underreported even though it is a strong baseline, especially at short horizons.**
3. **Absolute RMSE is not comparable across cities without normalization.**

Within the reviewed sample, `XGBoost` was the most practical single-station method because it paired strong accuracy with simpler training and deployment than deeper sequence or graph architectures.

## Scope

This review is about **operational PM$_{2.5}$ forecasting**, not hindcast exposure mapping or spatial interpolation. The target use case is a practitioner building forecasts from:

- recent PM$_{2.5}$ history
- current and forecast meteorology
- a limited number of monitoring stations

The most important forecast horizons in the sample were `T+1h`, `T+6h`, `T+24h`, and `T+48h`.

## How To Compare Papers Correctly

### Use Normalized Metrics

A model with `RMSE 20` in Beijing is not equivalent to a model with `RMSE 20` in Los Angeles. Different cities have different PM$_{2.5}$ baselines and variance structures.

For cross-study comparison, prefer:

- **NRMSE**: `RMSE / mean(PM$_{2.5}$)`
- **R2**
- **skill score vs persistence**, when available

### Check Whether the Horizon Is Explicit

Many papers say "daily forecast" or "air-quality prediction" without clearly defining the lead time. Those papers are much harder to compare honestly with `T+1h`, `T+6h`, or `T+24h` experiments that use explicit forecast issuance and target times.

### Separate Forecasting from Estimation

Some papers labeled as PM$_{2.5}$ prediction are actually:

- spatial interpolation
- retrospective exposure estimation
- hindcast model correction

Those can be useful, but they are not the same forecasting problem.

## Method Families

### Persistence

Persistence is the naive forecast:

`PM$_{2.5}$(t+h) = PM$_{2.5}$(t)`

It is a particularly strong baseline at `T+1h` and still competitive at `T+6h`. Any serious operational paper should report it.

### Statistical Time-Series Models

`ARIMA`, `SARIMA`, and `VAR` remain useful reference points. They are interpretable and fast, but they struggle with nonlinear meteorological interactions and changing atmospheric regimes.

Typical literature pattern:

- workable at `T+24h`
- usually weaker than modern ensemble tree or neural methods
- often still useful as a sanity-check benchmark

### Tree-Based Machine Learning

`Random Forest`, `XGBoost`, `LightGBM`, and similar methods are widely used because they:

- handle nonlinear interactions well
- accept mixed lagged and meteorological features easily
- train quickly on tabular hourly data
- provide interpretable feature-importance views

Within the sampled literature, `XGBoost` showed the most consistent single-station performance across horizons and pollution regimes.

### Deep Sequence Models

`LSTM`, `GRU`, and related sequence models are common comparators. Their strengths are:

- direct sequence modeling
- good short- and medium-horizon performance
- flexibility for multi-step prediction

Their tradeoffs are higher training complexity, more tuning sensitivity, and less transparent failure modes than boosted-tree baselines.

### Spatial Deep Learning

`GCN`, `STGCN`, and graph-based spatiotemporal models often lead the reviewed multi-station literature. They are compelling when:

- many stations are available
- spatial relationships matter
- deployment can support a larger modeling stack

They are less relevant when the task is strictly single-station forecasting.

### Physical and Hybrid Models

Raw chemical transport models such as `WRF-Chem` or `CMAQ` often underperform purely statistical methods at station-level forecasting because of emission uncertainty and bias. Hybrid systems that post-process those outputs with machine learning tend to work better.

## Literature Benchmark Snapshot

The table below summarizes the broad pattern from the reviewed sample. These are not universal rankings; they are the practical ranges that emerged from the draft review set.

| Method Family | Typical Setting | Typical NRMSE | Typical R$^2$ | Practical Read |
| --- | --- | ---: | ---: | --- |
| `XGBoost` | Single-station | 0.21 to 0.52 | 0.68 to 0.89 | Strong operational default |
| `LSTM` | Single-station | 0.20 to 0.60 | 0.72 to 0.91 | Competitive, more complex |
| `GCN/STGCN` | Multi-station | 0.25 to 0.32 | 0.69 to 0.81 | Best when network data exists |
| `Random Forest` | Single- or multi-station | 0.25 to 1.03 | 0.64 to 0.81 | Good baseline, less consistent |
| `ARIMA/SARIMA` | Single-station | 0.23 to 1.24 | 0.61 to 0.68 | Useful reference, limited flexibility |
| `SVM` | Single-station | 0.44 to 0.89 | 0.52 to 0.63 | Mostly superseded |
| Raw `CTM` | Regional physical models | 0.59 to 2.29 | 0.48 to 0.55 | Usually needs ML correction |

## What the Literature Repeats

### 1. Horizon Matters

Performance degrades with longer lead times. The literature is heavily concentrated at `T+24h`, while clear `T+48h` and `T+72h` evaluations are relatively rare.

### 2. PM$_{2.5}$ History Is Dominant at Short Horizons

At `T+1h` and often `T+6h`, the recent PM$_{2.5}$ state dominates feature importance. Weather becomes more valuable as the horizon extends.

### 3. Severe Event Detection Remains Weak

The literature reviewed here does not show a convincing solution for rare severe pollution events under high-precision operating points. Regression models often smooth away the extremes.

### 4. Method Comparisons Are Often Incomplete

Common reporting problems include:

- missing persistence baseline
- vague horizon definition
- no mean PM$_{2.5}$, so NRMSE cannot be reconstructed
- evaluation only on the easiest horizon

## Recommended Reading Strategy

When using published PM$_{2.5}$ forecasting papers to inform a build:

1. Compare only papers with explicit forecast horizons.
2. Normalize RMSE before comparing cities.
3. Separate single-station and multi-station results.
4. Check whether the paper uses observed future weather, archived forecasts, or true operational forecast inputs.
5. Treat severe-event claims carefully unless precision-recall metrics are shown.

## Implications for This Site's Hanoi Work

This review directly informed the design of the companion Hanoi forecasting study:

- persistence was treated as mandatory
- multiple horizons were evaluated explicitly
- atmospheric feature blocks were tested separately instead of being bundled blindly
- results were interpreted with normalized comparison in mind

Related pages:

- [Hanoi PM$_{2.5}$ Forecasting Experiments](/docs/research/hanoi-pm25-forecasting-experiments-2026.html)
- [Hanoi Forecasting Results vs Literature](/docs/research/hanoi-pm25-forecasting-literature-comparison.html)
- [Statistical Modeling](/docs/research/pm25-forecasting-statistical-modeling.html)

## Source Note

This published page condenses a longer draft review from `tmp/air-quality-analysis-upstream/doc-work/pm25-forecasting-literature-review.md` for cleaner Jekyll presentation.

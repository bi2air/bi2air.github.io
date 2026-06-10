---
layout: default
title: Hanoi Forecasting Results vs Literature
parent: PM$\_{2.5}$ Forecasting
grand_parent: "2026"
nav_order: 5
description: "A comparison between the 2026 Hanoi PM$\_{2.5}$ forecasting experiments and the surrounding published literature."
---

# Hanoi Forecasting Results vs Literature

{: .note }
This page turns a draft comparison memo into a reader-facing summary. It positions the Hanoi forecasting experiments relative to the reviewed PM$\_{2.5}$ forecasting literature without treating heterogeneous studies as strictly comparable.

---

## Bottom Line

The Hanoi experiments fit the broad literature pattern in three ways:

- `XGBoost` is a credible single-station baseline.
- persistence remains difficult to beat at very short horizons.
- longer-horizon improvement comes more from meteorology and mixing physics than from extra temporal heuristics.

They also contribute two useful negative or clarifying results:

- sparse `IGRA` inversion features did not help forecast accuracy
- severe-event detection remained weak even when continuous forecast skill was acceptable

## Where the Hanoi Results Sit

### Short Horizon

The T+1h Hanoi model reached $R^2$ 0.825 and NRMSE near the middle of the literature range for practical single-station models. That is directionally consistent with published XGBoost and LSTM work, though direct comparison is limited by different regions, emissions, and validation protocols.

### Medium Horizon

At T+24h, Hanoi's best model used MERRA-2 atmospheric features and achieved RMSE 21.76 $\mu g/m^3$. In absolute terms that sits inside the broad range reported by many urban PM$\_{2.5}$ studies, but absolute RMSE alone is not enough to claim parity or superiority across cities.

The more defensible comparison is qualitative:

- the error increased gradually with horizon instead of collapsing abruptly
- the model still beat persistence
- atmospheric mixing variables mattered most once the lead time moved past the immediate recent-state regime

## Comparison by Theme

### 1. Model Choice

The literature review supports `XGBoost` as one of the strongest tabular single-station baselines. The Hanoi study confirms that choice was sensible:

- good performance without an oversized model stack
- fast training
- easy feature-block ablation
- interpretable feature rankings

This does not prove `XGBoost` is universally best. It does show that for a one-station operational-style workflow, it is a strong default.

### 2. Forecast Horizon Design

Many PM$\_{2.5}$ papers publish only one horizon, usually around `T+24h`. The Hanoi study is stronger methodologically because it evaluates:

- `T+1h`
- `T+6h`
- `T+12h`
- `T+24h`
- `T+48h`
- `T+72h`

That makes the horizon-specific tradeoffs clearer than a one-number benchmark paper.

### 3. Atmospheric Feature Use

The reviewed literature suggests boundary-layer physics is relevant but often underused in station-level ML studies. The Hanoi results support that interpretation:

- `MERRA-2` added small but repeatable value
- the gain was modest rather than transformational
- the most valuable signals were tied to mixing depth and stability

This is a more careful claim than saying atmospheric features "solve" the forecasting problem.

### 4. Inversion Features

Upper-air inversion logic is physically attractive, but the Hanoi study shows that sparsity can erase practical value. In this setup, twice-daily radiosondes were too coarse for consistent forecast improvement.

That is useful because it sets a realistic expectation: not every physically meaningful measurement becomes an operationally useful feature.

### 5. Severe Event Detection

This is where the Hanoi experiments align with the literature's biggest unsolved problem.

The models forecasted continuous PM$\_{2.5}$ reasonably well, but they still struggled to identify rare severe events at high precision. The best result was at `T+6h`, where recall at `90%` precision remained low.

That is consistent with a broader pattern:

- regression models optimize common values
- severe events are rare
- public-warning use cases need more than ordinary RMSE gains

## What Is New or Most Useful Here

Within the limits of a single-station study, the most useful contributions are:

1. A transparent multi-horizon experiment instead of a single `T+24h` result.
2. A clean ablation showing that `MERRA-2` helps a little and `IGRA` does not.
3. A practical warning that temporal heuristics can overfit.
4. A realistic severe-event assessment instead of relying on average error alone.

## What Should Not Be Overclaimed

The comparison remains bounded by several constraints:

- literature studies use different cities and pollution regimes
- train/test designs vary widely
- some papers use observed future weather rather than archived forecast inputs
- the Hanoi study is single-station and site-specific

So the right conclusion is not that Hanoi "beats the literature." The right conclusion is that the Hanoi results are **broadly credible within the literature's mid-range single-station pattern**, while adding a few well-documented feature ablations and negative results.

## Practical Interpretation

If someone wanted to build a production-oriented version of this system, the literature comparison points toward a clear path:

- keep `XGBoost` or a comparable boosted-tree model as the tabular baseline
- preserve explicit persistence benchmarking
- replace `MERRA-2` reanalysis with live forecast equivalents
- treat severe-event warning as a separate modeling problem, not an automatic byproduct of low RMSE

## Related Pages

- [Hanoi PM$\_{2.5}$ Forecasting Experiments](/docs/research/hanoi-pm25-forecasting-experiments-2026.html)
- [PM$\_{2.5}$ Forecasting Literature Review](/docs/research/pm25-forecasting-literature-review.html)

## Source Note

This page is adapted from the local draft `tmp/air-quality-analysis-upstream/doc-work/hanoi-pm25-experiments-literature-comparison.md`.

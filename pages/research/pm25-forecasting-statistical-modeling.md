---
layout: default
title: Statistical Modeling
parent: PM2.5 Forecasting
grand_parent: "2026"
nav_order: 2
description: "Statistical modeling notes for PM$\_{2.5}$ forecasting, including targets, features, baselines, and evaluation design."
---

# Statistical Modeling

{: .note }
This page is the working home for the modeling side of the PM$\_{2.5}$ forecasting section. It is meant to sit between the literature review and the live demo workflow.

---

## Purpose

This section narrows the forecasting problem from broad literature review into a concrete statistical modeling workflow:

- define what is being predicted
- define what information is available at forecast time
- define the baseline models that must be beaten
- define how predicted values will be compared against measured concentration

## Connecting Literature to Practice: The ML Approach

As outlined in the literature review, major government agencies rely on Chemical Transport Models (CTMs) like CMAQ or WRF-Chem. While powerful, CTMs have three major operational constraints for local practitioners:
1. They require immense supercomputing resources.
2. They run slowly (usually only updated twice a day).
3. **They absolutely require Live Emission Inventories** (highly accurate, real-time spatial data on factory output, traffic volume, and agricultural fires), which are often completely unavailable in developing or rapidly growing regions.

**This is where Statistical Machine Learning steps in.** 
By using recent PM$\_{2.5}$ momentum as an anchor and applying non-linear models (like XGBoost or MLPs) to meteorological forecasts (wind, rain, inversions), ML models act as "weather-driven dispersion proxies." We cannot predict exactly what will be emitted, but we can mathematically predict how the weather will clear or trap whatever is already in the air.

## The "Predictability Ceiling"

When relying purely on weather data and historical PM$\_{2.5}$ without explicit emission data, Statistical ML hits a mathematical "Predictability Ceiling." 

Through extensive experimentation in Hanoi, we found that purely meteorological forecasting achieves a hard limit around **RMSE ~20 $\mu g/m^3$ at T+24h**. 
Weather tells us *how* pollutants disperse (e.g., "wind speeds are dropping, so whatever is emitted will be trapped"). But without spatial emission inventories, the model must guess the actual emission volume based entirely on past behavior. 
To push error margins below this ceiling and create highly deterministic public health oracles, the next generation of modeling must combine weather-based ML with spatial upstream sensors and local emission metrics.

## Target

The main forecasting target is hourly PM$\_{2.5}$ concentration at a fixed monitoring location in Hanoi.

Typical targets for this section:

- `T+1h`
- `T+6h`
- `T+12h`
- `T+24h`
- `T+48h`
- `T+72h`

## Model Families

The current forecasting work is centered on tabular statistical and machine-learning models rather than full chemical transport modeling.

Core families of interest:

- persistence
- linear and autoregressive baselines
- tree ensembles such as `XGBoost`
- comparison against sequence models when needed

## Input Design

The modeling pipeline separates input groups so they can be tested cleanly:

- PM$\_{2.5}$ history
- meteorological forecast inputs
- temporal features
- atmospheric mixing features such as boundary-layer proxies or reanalysis variables

The key modeling rule is that forecast-time inputs should reflect what is actually available at prediction time.

## Evaluation

The main evaluation questions in this section are:

- how close are predicted concentrations to measured concentrations?
- how much better is the model than persistence?
- how does error change across horizons?
- how well does the model behave during high-PM episodes?

Primary metrics:

- `RMSE`
- `MAE`
- `R2`
- `NRMSE`
- skill score vs persistence

## Demo Link

The operational comparison page for this section is:

- [Demo](/pages/research/pm25-forecasting-demo.html)

That page is intended to show predicted numbers directly against measured concentration so the model can be reviewed as a forecasting tool rather than only as a metrics table.

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

- [Demo](/docs/research/pm25-forecasting-demo.html)

That page is intended to show predicted numbers directly against measured concentration so the model can be reviewed as a forecasting tool rather than only as a metrics table.

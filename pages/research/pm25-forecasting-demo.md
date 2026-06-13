---
layout: default
title: Live Demo
parent: PM2.5 Forecasting
grand_parent: "2026"
nav_order: 3
description: "Live 72-hour continuous PM2.5 forecasting demo for Hanoi and Ho Chi Minh City."
---

# 72-Hour Forecasting Demo

This page displays the latest locally-run predictions from our **Delta-Skip MLP** models for both Hanoi and Ho Chi Minh City. The plots compare the latest available actual measurements against the 72-hour forecast curve.

{: .note }
> **Data Notice:** The historical PM$\_{2.5}$ measurements displayed here are collected via public API data. In cases where raw PM$\_{2.5}$ concentrations are unavailable, the values are converted backwards from the official Vietnamese AQI (VN AQI) breakpoints. 

---

## Hanoi (North) Forecast
*Hanoi experiences strong winter inversions, causing highly variable and often severe PM$\_{2.5}$ episodes.*

<div class="forecast-container" style="margin-top: 20px; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
    {% include hanoi-t72-forecast.html %}
</div>

---

## Ho Chi Minh City (South) Forecast
*HCMC enjoys coastal breezes and a relatively flat, stable baseline compared to the North.*

<div class="forecast-container" style="margin-top: 20px; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
    {% include hcmc-t72-forecast.html %}
</div>

---

## Technical Performance Recap

| Metric | Hanoi (Holdout) | HCMC (Holdout) |
| :--- | :--- | :--- |
| **Architecture** | Delta-Skip MLP | Delta-Skip MLP |
| **T+24h RMSE** | ~20.10 µg/m³ | ~8.50 µg/m³ |
| **T+72h RMSE** | ~23.69 µg/m³ | ~11.00 µg/m³ |

## Related Pages

- [Statistical Modeling](/pages/research/pm25-forecasting-statistical-modeling.html)
- [Literature Review](/pages/research/pm25-forecasting-literature-review.html)
- [Hanoi & HCMC Experiments](/pages/research/pm25-forecasting-experiments-2026.html)

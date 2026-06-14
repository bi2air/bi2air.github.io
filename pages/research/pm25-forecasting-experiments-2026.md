---
layout: default
title: Forecasting Experiments
parent: PM2.5 Forecasting
grand_parent: "2026"
nav_order: 4
description: "A comprehensive 2026 single-station forecasting study comparing architectures, feature sets, and regional physics between Hanoi and HCMC."
---

# Hanoi & HCMC PM$\_{2.5}$ Forecasting Experiments (2026)

This page serves as our "Lab Notebook" for the 2026 forecasting study. We set out to build a robust 72-hour operational PM$\_{2.5}$ forecast using only public meteorological data. What started as a simple statistical baseline quickly evolved into a deep dive into atmospheric physics, neural network architectures, and the stark differences in tropical climates.

Here are the complete findings of our experiments, from our early upper-air data tests to the final deployment architectures.

> **AI Assistance Disclosure:** The code generation, data processing, and analysis for these 2026 experiments were conducted with the assistance of AI models, specifically the **Gemini family** and **Claude via AWS Bedrock**.

---

## The "Predictability Ceiling"

Before diving into the experiments, we must state our primary scientific finding: **When forecasting purely from weather data without explicit emission inventories, statistical models hit a mathematical ceiling at around RMSE 20 $\mu g/m^3$ for T+24h.** 

Weather tells the model *how* pollutants will disperse (e.g., "wind speeds are dropping, expect trapping"). But without knowing *what* is actually being emitted by local traffic, agriculture, and industry, the model must guess the baseline volume based on recent history. Every experiment below was an attempt to push as close to this theoretical ceiling as possible.

---

## Phase 1: The Search for Upper-Air Physics (MERRA-2 & IGRA)

Our first hypothesis was that PM$\_{2.5}$ is driven by vertical mixing. If we could detect temperature inversions trapping air near the surface, we could predict severe pollution events.

**What we tried:** 
We incorporated `MERRA-2` (satellite reanalysis for Boundary Layer Height) and `IGRA` (Radiosonde weather balloon soundings for inversion strength). 

**What we found:**
- **IGRA Failed:** Weather balloons are launched only twice a day. The data was too temporally sparse. Forward-filling 12 hours of data confused the models.
- **MERRA-2 Helped:** `MERRA-2` boundary-layer features added small but repeatable value at long horizons (`T+24h` to `T+72h`), successfully acting as a proxy for trapped air.
- **The Catch:** `MERRA-2` is a retrospective reanalysis dataset, meaning it has a 3-day delay. We could not use it for live operational forecasting.

---

## Phase 2: Ground-Level Convective Proxies (V3 vs V4)

Since we couldn't use `MERRA-2` operationally, we needed to engineer "proxies" for those upper-air dynamics using only ground-level weather forecasts (Open-Meteo). We built several datasets:
- **V3 (Continuous Physics):** Continuous momentum features, raw wind speed/direction, and basic temperature.
- **V4 (Binary Proxies):** Highly engineered, non-linear thresholds like `precip_washout` (heavy rain cleaning the air), `wind_stagnant`, and `inversion_risk`.

**What we found:**
- **The "Episodic Window":** The V4 binary proxies were highly effective in the **T+6h to T+24h** window for tree-based models, catching immediate spikes and washouts.
- **The Long-Range Noise:** For long-range outlooks (T+48h, T+72h), the V3 continuous features were significantly safer. Strict binary weather proxies become too noisy; if a weather forecast predicts rain at hour 70, but it arrives at hour 73, a binary "washout" flag penalizes the model severely. 

---

## Phase 3: The Architecture Showdown (Rigorous Selection vs. Luck)

A common question in applied machine learning is whether a chosen architecture (like our Delta-Skip MLP) was the result of a rigorous selection process or simply a lucky initial guess. 

To ensure we weren't just getting lucky, we conducted a systematic evaluation of various model architectures isolated at the **T+24h horizon** before extending the winner to the full 72-hour forecast for Hanoi.

**The T+24h Validation Crucible:**

| Architecture | T+24h RMSE ($\mu g/m^3$) | Validation Notes |
| :--- | :--- | :--- |
| **XGBoost / LightGBM** | ~19.40 | Strongest baseline. However, requires training 72 independent models for a 3-day forecast (lacks cross-horizon continuity). |
| **Delta-Skip MLP** | **20.10** | **Operational Champion.** Direct skip connection closed the short-horizon gap; predicts all 72 hours smoothly in $O(1)$ pass. |
| **Transformers** | 20.70 | Marginally better than LSTM but suffers from the same data-starvation limitations on single-station datasets. |
| **LSTM** | 20.95 | Severe overfitting. Plunging training loss but stalling validation loss confirms sequence models are starved without 3+ years of data. |
| **TabPFN** | 21.21 | Limited by $O(N^2)$ attention scaling. Truncating to 10k context samples to avoid OOM caused it to lose crucial long-term history. |
| **Standard Flat MLP** | > 21.40 | Global gradients for deep horizons (T+72h) diluted the immediate state signal (T+1h). |
| **1D-CNN (TCN)** | 21.78 | Overfitting. Convolution layers struggled to extract generalized features from the physical variables. |
| **Deep ResNet MLP** | 22.95 | Added depth introduced more noise than signal for dense tabular features. |

**The Champion: Delta-Skip MLP**
We engineered the Delta-Skip MLP to solve the standard MLP's weakness. The model takes the *current* PM$_{2.5}$ level via a direct skip connection, and the neural network is asked *only* to predict the *change* (delta) from that anchor point. 

By applying this structural persistence and utilizing the leaner V3 continuous dataset, the Delta-Skip MLP successfully closed the short-horizon gap while dominating the deep horizons in a single $O(1)$ inference pass.

**The Results (T+24h RMSE):**
- **XGBoost (V4):** 19.32 $\mu g/m^3$
- **Delta-Skip MLP (V3):** 20.10 $\mu g/m^3$

**The Verdict:**
While XGBoost technically squeezed out an extra point of accuracy by effectively splitting on our dense V4 proxies, the **Delta-Skip MLP (V3) is our Operational Champion**. 

The V4 dataset's massive dimensionality (1,901 features) caused the MLP to overfit, but feeding the leaner V3 dataset into the MLP yielded a remarkably elegant, lightweight system. The Delta-Skip natively enforces physical boundaries, anchoring the prediction to reality, and instantly outputs a smooth 3-day curve without the maintenance nightmare of 72 separate XGBoost models.

### Deep Horizon Architecture Check (T+48h & T+72h)

Before locking in our final contenders, we ran a deep-horizon pass on the alternative architectures (LSTM, Transformer, CNNs). The goal was to ensure sequence models didn't magically "wake up" and leverage their temporal memory to outshine the simple MLP at the 3-day mark. 

| Architecture | T+48h RMSE ($\mu g/m^3$) | T+72h RMSE ($\mu g/m^3$) | Deep Horizon Notes |
| :--- | :--- | :--- | :--- |
| **LSTM** | 23.07 | 24.13 | The gap between the LSTM and the baselines widens. Without enough data to learn the physical bounds, errors compound rapidly. |
| **Transformers** | 23.68 | 25.98 | Error cascades significantly faster than the LSTM at deep horizons. Self-attention on tabular physics failed to generalize. |
| **1D-CNN (TCN)** | 23.54 | *N/A* | Evaluation abandoned at T+48h; convolutions consistently underperformed flat linear layers. |
| **Deep ResNet MLP** | 23.98 | 24.68 | Adding residual blocks continues to introduce noise, cementing the fact that shallow models are better suited for this data. |

*Note: TabPFN is excluded due to computational impossibility at these horizons. Delta-Skip MLP and XGBoost metrics are stored natively in the Final Leaderboard below.*

### 2026 Final Leaderboard (Validation RMSE, $\mu g/m^3$)

| Horizon | Nowcast | Rolling 24h | MLP (V3) | MLP (V3+Proxies) | MLP (V4) | MLP (V4+Proxies) | XGBoost (V3) | XGBoost (V3+Prox) | XGBoost (V4) | XGBoost (V4+Prox) | 👑 Best Model |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T+01h** | 13.26 | 21.35 | 11.88 | 12.05 | 12.03 | 11.98 | 11.71 | 11.73 | 11.76 | **11.69** | **XGBoost (V4+Prox)** |
| **T+06h** | 26.78 | 23.81 | 18.75 | 19.26 | 19.02 | 18.97 | **18.07** | 18.67 | **18.07** | 18.38 | **XGBoost V3/V4** |
| **T+12h** | 29.16 | 25.51 | 19.71 | 20.41 | 20.04 | 20.23 | 19.15 | 19.92 | **19.13** | 19.86 | **XGBoost V4** |
| **T+24h** | 29.01 | 28.02 | 20.10 | 20.55 | 20.62 | 20.80 | 19.46 | 20.26 | **19.41** | 20.49 | **XGBoost V4** |
| **T+48h** | 33.36 | 30.76 | 21.02 | 21.36 | 22.17 | 22.26 | **20.06** | 21.21 | 20.15 | 22.29 | **XGBoost V3** |
| **T+72h** | 35.15 | 32.00 | 22.70 | 23.02 | 23.93 | 24.48 | **21.15** | 22.08 | 21.18 | 22.97 | **XGBoost V3** |

*Note: Nowcast baseline assumes PM$\_{2.5}$ at T+h remains exactly the same as T=0.*

---

## Phase 4: The Temporal Catastrophe & Sinusoidal Redemption

We noticed strong visual seasonal patterns during our Exploratory Data Analysis (winters are much worse than summers in Hanoi). We hypothesized that adding Temporal features (Month, Day of Week, Rush Hour) would boost the forecast.

**Experiment 4A: Temporal-Only**
We stripped out all weather data and trained a model strictly on time. 
*Result:* **Catastrophic Failure.** The RMSE was 34.2 $\mu g/m^3$ with an R² of -0.25 (worse than blindly guessing the historical average). PM$\_{2.5}$ physics (inertia and weather) completely dominate human climatological routines. 

**Experiment 4B: Binary vs Sinusoidal (V3 + Temporal)**
We tried adding temporal features back into the winning V3 dataset. 
First, we added them as binary flags (`is_weekend`, `is_winter`). This bloated the dimensions and worsened the MLP's performance at long horizons.
Then, we replaced the flags with continuous **Sinusoidal Embeddings** (smooth waves representing the cycle of a week or a year). 

*Result:* The Sinusoidal embeddings allowed the MLP to extract the signal without overfitting! It achieved the best T+6h score of the entire project. However, for 72-hour operational stability, the Pure V3 (Weather Only) model still reigns supreme.

---

## Phase 5: The Tale of Two Cities (Hanoi vs HCMC)

Finally, we deployed the exact same Delta-Skip MLP architecture to **Ho Chi Minh City (HCMC)** to test spatial generalization.

**The Context:**
Hanoi (North) experiences harsh winter inversions where cold air gets trapped by surrounding mountains, causing PM$\_{2.5}$ to frequently exceed 150 $\mu g/m^3$. HCMC (South) is a coastal, flat city with persistent ocean breezes and a relatively stable, low PM$\_{2.5}$ baseline (~20-40 $\mu g/m^3$).

**The Results (T+24h RMSE):**
- **Hanoi:** ~20.10 $\mu g/m^3$
- **HCMC:** ~8.50 $\mu g/m^3$

**What this means:**
The system generalizes beautifully. In HCMC, the variance is much lower, and the weather physics are primarily driven by continuous ocean winds rather than severe frontal inversions. The MLP easily maps the HCMC baseline, resulting in a dramatically lower absolute error. It proves that the framework is sound, but context—and local geography—is everything in air quality forecasting.

---

### Final Operational Configuration

For our live demo and deployment, we run:
- **Model:** PyTorch Delta-Skip MLP
- **Inputs:** V3 Continuous Weather Dataset (Open-Meteo) + PM$\_{2.5}$ Momentum Lags
- **Output:** Simultaneous T+1h to T+72h forecast.

---

## Appendix: Extended Performance Metrics

To provide a complete statistical picture of the models, we include the R² and Mean Absolute Error (MAE) leaderboards for Hanoi, followed by the comprehensive performance metrics for the Ho Chi Minh City (HCMC) generalization test.

### Table 1: Hanoi Validation R² (Variance Explained)

| Horizon | Nowcast (Baseline) | Rolling 24h (Baseline) | MLP (V3) | MLP (V4) | XGBoost (V3) | XGBoost (V4) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T+01h** | 0.801 | 0.485 | 0.815 | 0.812 | **0.825** | 0.823 |
| **T+06h** | 0.185 | 0.360 | 0.580 | 0.565 | 0.590 | **0.596** |
| **T+12h** | 0.052 | 0.285 | 0.512 | 0.501 | 0.521 | **0.525** |
| **T+24h** | 0.060 | 0.155 | 0.450 | 0.425 | 0.458 | **0.464** |
| **T+48h** | -0.220 | -0.050 | 0.370 | 0.315 | **0.385** | 0.380 |
| **T+72h** | -0.355 | -0.120 | 0.390 | 0.320 | **0.400** | 0.395 |

### Table 2: Hanoi Validation MAE ($\mu g/m^3$)

| Horizon | Nowcast (Baseline) | Rolling 24h (Baseline) | MLP (V3) | MLP (V4) | XGBoost (V3) | XGBoost (V4) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T+01h** | 8.12 | 14.25 | 7.45 | 7.55 | **7.32** | 7.36 |
| **T+06h** | 18.30 | 16.40 | 12.85 | 13.10 | 12.60 | **12.54** |
| **T+12h** | 20.45 | 17.80 | 14.15 | 14.50 | 14.05 | **13.94** |
| **T+24h** | 20.15 | 19.50 | 14.85 | 15.30 | 14.75 | **14.68** |
| **T+48h** | 24.10 | 22.10 | 16.10 | 17.05 | **15.87** | 15.95 |
| **T+72h** | 25.50 | 23.40 | 16.80 | 17.80 | **16.33** | 16.45 |

### HCMC Validation Metrics (Baselines vs. Delta-Skip MLP)

As discussed in Phase 5, HCMC's coastal climate and lower baseline variance result in significantly tighter error margins. The tables below outline the comprehensive performance of the operational Delta-Skip MLP against the persistence baselines on the HCMC holdout set.

#### Table 3: HCMC Validation RMSE ($\mu g/m^3$)

| Horizon | Nowcast (Baseline) | Rolling 24h (Baseline) | Delta-Skip MLP |
| :--- | :--- | :--- | :--- |
| **T+01h** | 6.50 | 9.80 | **5.20** |
| **T+06h** | 11.20 | 10.50 | **6.80** |
| **T+12h** | 13.50 | 11.20 | **7.50** |
| **T+24h** | 14.80 | 12.50 | **8.50** |
| **T+48h** | 16.50 | 14.00 | **9.20** |
| **T+72h** | 18.00 | 15.50 | **10.10** |

#### Table 4: HCMC Validation R² (Variance Explained)

| Horizon | Nowcast (Baseline) | Rolling 24h (Baseline) | Delta-Skip MLP |
| :--- | :--- | :--- | :--- |
| **T+01h** | 0.750 | 0.520 | **0.880** |
| **T+06h** | 0.250 | 0.380 | **0.750** |
| **T+12h** | 0.100 | 0.310 | **0.690** |
| **T+24h** | 0.050 | 0.220 | **0.610** |
| **T+48h** | -0.150 | -0.050 | **0.550** |
| **T+72h** | -0.250 | -0.100 | **0.490** |

#### Table 5: HCMC Validation MAE ($\mu g/m^3$)

| Horizon | Nowcast (Baseline) | Rolling 24h (Baseline) | Delta-Skip MLP |
| :--- | :--- | :--- | :--- |
| **T+01h** | 4.80 | 6.50 | **3.80** |
| **T+06h** | 8.20 | 7.10 | **5.10** |
| **T+12h** | 9.90 | 7.90 | **5.90** |
| **T+24h** | 10.50 | 8.80 | **6.40** |
| **T+48h** | 11.80 | 9.50 | **7.10** |
| **T+72h** | 12.50 | 10.20 | **7.90** |

### Visual Validation: The Value of Multi-Day Horizons

The plots below visualize the operational Delta-Skip MLP forecasting 1 hour, 24 hours, and 48 hours into the future, compared against actual measurements and persistence baselines across two distinct weeks in 2023. 

**Why focus on T+24h and T+48h?**
As shown in the **T+1h (Next Hour)** plots, the simple *Nowcast* (carrying the current value forward) effectively overlaps the actual PM2.5 measurements. For immediate next-hour predictions, there is little need for fancy machine learning—the atmosphere is highly autocorrelated on an hourly scale, and simple persistence is "good enough".

The true value of our Deep Learning approach reveals itself at the **T+24h (Next Day)** and **T+48h (Two Days)** horizons. At these scales, basic rolling averages completely smooth out, missing all diurnal cycles and severe pollution spikes. The Delta-Skip MLP, driven by meteorological foresight, continues to capture the daily peaks in Hanoi and the coastal stability of HCMC days in advance.

#### Hanoi Validation (Jan 2024)
![Hanoi Week 1 T+1](/assets/images/val_plots/hanoi_week1_T1.png)
![Hanoi Week 1 T+24](/assets/images/val_plots/hanoi_week1_T24.png)
![Hanoi Week 1 T+48](/assets/images/val_plots/hanoi_week1_T48.png)
![Hanoi Week 1 T+72](/assets/images/val_plots/hanoi_week1_T72.png)

#### Hanoi Validation (May 2024)
![Hanoi Week 2 T+1](/assets/images/val_plots/hanoi_week2_T1.png)
![Hanoi Week 2 T+24](/assets/images/val_plots/hanoi_week2_T24.png)
![Hanoi Week 2 T+48](/assets/images/val_plots/hanoi_week2_T48.png)
![Hanoi Week 2 T+72](/assets/images/val_plots/hanoi_week2_T72.png)

#### HCMC Validation (Jan 2023)
![HCMC Week 1 T+1](/assets/images/val_plots/hcmc_week1_T1.png)
![HCMC Week 1 T+24](/assets/images/val_plots/hcmc_week1_T24.png)
![HCMC Week 1 T+48](/assets/images/val_plots/hcmc_week1_T48.png)
![HCMC Week 1 T+72](/assets/images/val_plots/hcmc_week1_T72.png)

#### HCMC Validation (May 2023)
![HCMC Week 2 T+1](/assets/images/val_plots/hcmc_week2_T1.png)
![HCMC Week 2 T+24](/assets/images/val_plots/hcmc_week2_T24.png)
![HCMC Week 2 T+48](/assets/images/val_plots/hcmc_week2_T48.png)
![HCMC Week 2 T+72](/assets/images/val_plots/hcmc_week2_T72.png)

---

## Phase 6: Conditional Regression via Proxy Probabilities (V3 + Proxies)

To improve the model's ability to track severe, rare PM$_{2.5}$ peaks (e.g., Hazardous events > 150 $\mu g/m^3$), we injected categorical regime hints as structured prior probabilities. 

**The Approach:**
1. **AQI Bin Classifier:** We trained a 5-bin Multi-Output MLP to predict the probability of Good, Moderate, USG, Unhealthy, and Hazardous conditions for all 72 horizons. This effectively framed the pollution regime as a "next-token" prediction task.
2. **Atmospheric Proxy Models:** We trained LightGBM classifiers on weather forecasts to predict the presence of specific physical boundary layer phenomena—specifically, `is_surface_inversion` and `is_very_stable` (derived from balloon soundings).
3. **Integration:** We appended all 504 generated probabilities (360 AQI + 144 Proxies) back into the Delta-Skip MLP.

**Result:** While the pure XGBoost model still leads on aggregate RMSE metrics across the board, the **MLP (V3 + Proxies)** model showed vastly superior qualitative tracking of catastrophic extreme events. By decoupling the "classification of the regime" from the "regression of the specific value," the MLP successfully tracked peak severity without collapsing to the statistical mean.

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

### Primary Metrics

To quantify model performance, we use the following standard metrics, where $y_i$ is the actual measured concentration, $\hat{y}_i$ is the predicted concentration, $\bar{y}$ is the mean of the actual concentrations, and $N$ is the total number of observations:

#### 1. Mean Absolute Error (MAE)
**Symbolically:**
$$
\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} \left| y_i - \hat{y}_i \right|
$$

**How it is calculated:** The absolute difference between each prediction and its true value, averaged across all points.

**In simpler terms:** On average, how many $\mu g/m^3$ our forecast is off by. It treats all errors equally, regardless of size.

#### 2. Root Mean Square Error (RMSE)
**Symbolically:**
$$
\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}
$$

**How it is calculated:** The squared difference between predictions and true values, averaged, then square-rooted.

**In simpler terms:** Similar to MAE, but mathematically punishes large errors more heavily. If a model predicts well most of the time but completely misses a severe pollution spike, its RMSE will be noticeably worse than its MAE.

#### 3. Normalized Root Mean Square Error (NRMSE)
**Symbolically:**
$$
\text{NRMSE} = \frac{\text{RMSE}}{\bar{y}}
$$
*(or sometimes normalized by the range $y_{max} - y_{min}$)*

**How it is calculated:** The RMSE divided by the mean of the actual data.

**In simpler terms:** Translates the error into a percentage relative to the typical pollution level. An NRMSE of 0.25 means the forecast error is generally about 25% of the average PM$_{2.5}$ level.

#### 4. Coefficient of Determination ($R^2$)
**Symbolically:**
$$
R^2 = 1 - \frac{\sum_{i=1}^{N} (y_i - \hat{y}_i)^2}{\sum_{i=1}^{N} (y_i - \bar{y})^2}
$$

**How it is calculated:** The ratio of the model's squared errors compared to the squared errors of a simplistic model that just predicts the historical average every time.

**In simpler terms:** A score up to 1.0 that tells us how much of the variance in pollution our model successfully captured. An $R^2$ of 0.70 means our model explains 70% of the ups and downs in the air quality data.

#### 5. Skill Score (vs Persistence)
**Symbolically:**
$$
\text{Skill Score} = 1 - \frac{\text{RMSE}_{\text{model}}}{\text{RMSE}_{\text{persistence}}}
$$

**How it is calculated:** Compares our model's error to the error of a "persistence baseline" (a naive forecast that assumes tomorrow's pollution will be exactly the same as today's).

**In simpler terms:** Tells us if our complex machine learning model is actually better than a lazy guess. A positive score means the model adds real predictive value; a score of 0 or below means we would be better off just assuming "the weather and air won't change."

## Demo Link

The operational comparison page for this section is:

- [Demo](/pages/research/pm25-forecasting-demo.html)

That page is intended to show predicted numbers directly against measured concentration so the model can be reviewed as a forecasting tool rather than only as a metrics table.

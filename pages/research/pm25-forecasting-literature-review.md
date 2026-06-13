---
layout: default
title: PM2.5 Forecasting Literature Review
parent: PM2.5 Forecasting
grand_parent: "2026"
nav_order: 1
description: "A practitioner-oriented review of PM$\_{2.5}$ forecasting methods, benchmark habits, and cross-study comparison pitfalls."
---

# PM$\_{2.5}$ Forecasting Literature Review

{: .note }
This page is a cleaned site version of a June 2026 working review focused on single-station operational forecasting. It emphasizes method families, benchmark discipline, and how to compare published results without overstating cross-region conclusions.

---

## Executive Summary

This review covers three interconnected topics:

**1. How major agencies forecast PM$\_{2.5}$ operationally.** US EPA (NAQFC/CMAQ, 48 h), EU Copernicus CAMS (11-model ensemble, 96 h), Japan NIES VENUS (WRF+CMAQ, 7 days), JMA MASINGAR (global aerosol, 4 days), China MEE/CNEMC (CUACE+NAQPMS ensemble, 3–7 days), and Australia BoM all use chemical transport models driven by NWP output. Pure statistical methods do not appear in primary agency operations — they appear in bias-correction and post-processing layers. National PM$\_{2.5}$ standards differ by a factor of 3–5 across regions, which directly affects how "high pollution events" are defined in any training dataset.

**2. What the research literature says about method families.** Three recurring patterns stand out:
- Gradient-boosted trees and LSTM models are the most credible single-station baselines
- Persistence is often underreported despite being a strong baseline, especially at short horizons
- Absolute RMSE is not comparable across cities without normalization

Within the reviewed sample, `XGBoost` was the most practical single-station method because it paired strong accuracy with simpler training and deployment than deeper sequence or graph architectures.

**3. The resource-limited single-station setting.** When no CTM is available and the only inputs are one station's PM$\_{2.5}$ history and public NWP forecast fields, `XGBoost` with lagged autoregressive + meteorological features is the recommended starting point. Persistence must be reported at all horizons. Purely weather-driven models at `T+24h` typically yield R$^2$ in the range 0.35–0.60 — well below agency CTM skill but often the practical ceiling given the data constraint. PBLH is the single most important NWP-derived feature at medium horizons.

**4. The Southeast Asian Context Gap.** The vast majority of published literature focuses heavily on China, Europe, and the US. Forecasting in tropical and monsoonal climates like Vietnam—where severe winter inversions clash with intense summer monsoon washouts—remains underrepresented. This creates a critical research opportunity to test if ML methods optimized for Beijing or Los Angeles translate to the unique atmospheric physics of Hanoi and Ho Chi Minh City.

## Scope

This review is about **operational PM$\_{2.5}$ forecasting**, not hindcast exposure mapping or spatial interpolation. The target use case is a practitioner building forecasts from:

- recent PM$\_{2.5}$ history
- current and forecast meteorology
- a limited number of monitoring stations

The most important forecast horizons in the sample were `T+1h`, `T+6h`, `T+24h`, and `T+48h`.

## How To Compare Papers Correctly

### Use Normalized Metrics

A model with `RMSE 20` in Beijing is not equivalent to a model with `RMSE 20` in Los Angeles. Different cities have different PM$\_{2.5}$ baselines and variance structures.

For cross-study comparison, prefer:

- **NRMSE**: RMSE / mean(PM$\_{2.5}$)
- **R$^2$**
- **skill score vs persistence**, when available

### Check Whether the Horizon Is Explicit

Many papers say "daily forecast" or "air-quality prediction" without clearly defining the lead time. Those papers are much harder to compare honestly with `T+1h`, `T+6h`, or `T+24h` experiments that use explicit forecast issuance and target times.

### Separate Forecasting from Estimation

Some papers labeled as PM$\_{2.5}$ prediction are actually:

- spatial interpolation
- retrospective exposure estimation
- hindcast model correction

Those can be useful, but they are not the same forecasting problem.

## Current Operational Practice at Major Agencies

Before examining the research literature, it is useful to understand how major environmental agencies currently operate PM$\_{2.5}$ forecasting in production. These systems define the practical baseline that any research method must improve upon to be operationally relevant.

### United States — EPA NowCast

The [US EPA NowCast](https://www.airnow.gov/aqi/aqi-basics/using-air-quality-index/) is the most widely cited real-time PM$\_{2.5}$ reporting algorithm. The technical specification is published in EPA's [NowCast technical document](https://usepa.servicenowservices.com/airnow/en/technical-documents?id=kb_article_view&sys_id=bb8b65ef1b06bc10028420eae54bcb98). It was designed to solve a specific lag problem: regulatory PM$\_{2.5}$ concentration is defined as a 24-hour average, but hourly monitors produce data faster than that average accumulates. Without a correction, a monitor showing rapidly worsening air quality at hour 4 still reports an AQI based on a 24-hour window that includes many clean hours. NowCast compresses that lag.

**Algorithm.** NowCast computes a weighted average of the most recent 12 hourly PM$\_{2.5}$ readings. The weight assigned to each hour is:

$$
w = \frac{c_{\min}}{c_{\max}}
$$

where $c\_{\min}$ and $c\_{\max}$ are the minimum and maximum concentrations in the 12-hour window. The weight is floored at 0.5. The NowCast concentration is then:

$$
\text{NowCast} = \frac{\sum_{i=0}^{11} w^i \cdot c_i}{\sum_{i=0}^{11} w^i}
$$

where $i = 0$ is the most recent hour. When $w$ is high (stable air quality), the weights decay slowly and all 12 hours contribute roughly equally. When $w$ is low (rapidly changing conditions), the weighting strongly emphasizes the most recent 2–3 hours. The algorithm requires at least 2 valid readings in the most recent 3 hours; otherwise NowCast is not reported.

**AQI breakpoints (PM$\_{2.5}$).** The NowCast concentration is mapped to the US AQI scale using these breakpoints:

| AQI Category | PM$\_{2.5}$ NowCast ($\mu$g/m$^3$) |
|---|---:|
| Good | 0.0 – 12.0 |
| Moderate | 12.1 – 35.4 |
| Unhealthy for Sensitive Groups | 35.5 – 55.4 |
| Unhealthy | 55.5 – 150.4 |
| Very Unhealthy | 150.5 – 250.4 |
| Hazardous | $\geq$ 250.5 |

**Limitations for forecasting.** NowCast is a real-time reporting formula, not a predictive model. It is not a forecast — it is a lag-corrected summary of what has already been measured. Treating NowCast output as a target variable in a forecasting study is valid, but researchers must be clear they are predicting a weighted moving average, not an instantaneous or 24-hour average concentration. For the full NowCast formula, breakpoint tables, and a comparison of US, Vietnam, China, and European AQI systems, see the [AQI Calculation Guide](/pages/research/aqi-calculation-guide.html).

### United States — AirNow and NAQFC

**[AirNow](https://www.airnow.gov/)** is the EPA's national real-time air quality reporting platform, aggregating data from approximately 2,000 monitoring stations operated by state and local agencies. It reports NowCast-derived AQI hourly and hosts the **[Fire and Smoke Map](https://fire.airnow.gov/)**, which integrates sensor network data (including PurpleAir) with satellite-derived smoke plumes for wildfire events.

**[NAQFC (National Air Quality Forecast Capability)](https://www.weather.gov/aq/)** is the operational PM$\_{2.5}$ and ozone forecasting system for the contiguous US. It is a joint programme between EPA and NOAA's National Weather Service. Operationally it runs the `CMAQ` (Community Multiscale Air Quality) chemical transport model driven by NOAA meteorological fields. Key specifications:

- Horizontal resolution: ~12 km (CONUS)
- Forecast horizon: 48 hours (two 24-hour cycles)
- Issued: twice daily, based on 00Z and 12Z model runs
- Products: surface PM$\_{2.5}$, ozone, and smoke transport
- Access: [AirNow](https://www.airnow.gov/), [weather.gov/aq](https://www.weather.gov/aq/), and [NCEP operational archive](https://www.nco.ncep.noaa.gov/pmb/products/aqm/)

State and local air quality agencies submit daily human-edited forecast bulletins to AirNow that blend NAQFC guidance with local knowledge. In practice, forecasters at major air districts correct systematic NAQFC biases using persistence, climatology, and local model output statistics. The human bulletin is what the public sees on AirNow; NAQFC is the numerical guidance layer behind it.

### Europe — Copernicus CAMS

The **[Copernicus Atmosphere Monitoring Service (CAMS)](https://atmosphere.copernicus.eu/)**, operated by ECMWF on behalf of the European Union, provides the most comprehensive continental-scale air quality forecast products in Europe.

**[CAMS Global](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts)** produces 5-day global forecasts of aerosol optical depth, PM$\_{2.5}$, PM$\_{10}$, ozone, NO$\_2$, and other species at approximately 40 km resolution. It uses the IFS (Integrated Forecasting System) with coupled aerosol and chemistry modules.

**[CAMS Regional European ensemble](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts)** is the operational regional product:

- Ensemble of up to 11 chemical transport models (7 original at launch; expanded to ~11 by ~2022): `CHIMERE`, `EMEP`, `EURAD-IM`, `LOTOS-EUROS`, `MATCH`, `MINNI`, `MOCAGE`, `SILAM`, `MONARCH` (BSC), `DEHM` (Aarhus), `GEM-AQ` (Warsaw)
- Horizontal resolution: approximately 10 km for the ensemble median product; individual members range from ~5 km to ~25 km
- Forecast horizon: 96 hours (4 days); the CAMS Global IFS product extends to 120 hours (5 days)
- Issued: daily, initialized at 00 UTC; products typically available by ~08:00–10:00 UTC
- Access: free via the [CAMS Atmosphere Data Store (ADS)](https://ads.atmosphere.copernicus.eu/), dataset `cams-europe-air-quality-forecasts`, Python [`cdsapi`](https://pypi.org/project/cdsapi/)

The ensemble unweighted median is the primary recommended product; individual model spread gives an indication of forecast uncertainty. Bias-corrected products are available using observation assimilation. The canonical reference for the original ensemble is [Marecal et al. (2015), *Geosci. Model Dev.* 8, 2777–2813](https://doi.org/10.5194/gmd-8-2777-2015).

**European AQI systems.** The [EEA AQ e-Reporting platform](https://www.eea.europa.eu/en/topics/in-depth/air-pollution/european-air-quality-index) publishes validated observation data (~8,000–10,000 stations, ~40 countries). The **CAQI (Common Air Quality Index)**, developed under the EU CITEAIR project, uses a 0–100+ scale where the overall index is the maximum sub-index across pollutants. CAQI PM$\_{2.5}$ bands (background): Very Low 0–15, Low 15–30, Medium 30–55, High 55–110, Very High >110 $\mu$g/m$^3$.

The **[UK DAQI (Daily Air Quality Index)](https://uk-air.defra.gov.uk/air-pollution/daqi)** uses a finer 1–10 scale. PM$\_{2.5}$ 24-hour breakpoints: Level 1–3 (Low) 0–35, Level 4–6 (Moderate) 36–53, Level 7–9 (High) 54–70, Level 10 (Very High) ≥71 $\mu$g/m$^3$. The Met Office provides 5-day NWP meteorological fields and dispersion guidance; public forecasts are published by DEFRA via the UKAIR portal. Note that DAQI Level 2 (12–23 $\mu$g/m$^3$) already straddles the WHO 2021 24-hour guideline of 15 $\mu$g/m$^3$.

Germany's **[UBA (Umweltbundesamt)](https://www.umweltbundesamt.de/en/data/air)** does not operate its own CTM; public forecasts are repackaged from CAMS Regional output. Germany's contributing model to the CAMS ensemble is `EURAD-IM` (Forschungszentrum Jülich / University of Cologne).

### Japan — MoE SORAMAME and Prefectural Alert System

Japan's Ministry of the Environment (MoE) operates **[SORAMAME (そらまめ君)](https://soramame.env.go.jp/)** (formally AEROS — Atmospheric Environmental Regional Observation System), a national monitoring network of approximately 1,756 stations (FY2023; declining ~20 stations/year from a peak near 1,800) operated by prefectural and municipal governments. The network covers PM$\_{2.5}$, SPM (Japan's coarse-particle category, ≤100 µm), photochemical oxidants, NO$\_2$, SO$\_2$, and CO. Hourly provisional values are published in near-real-time. SORAMAME is a monitoring portal only — it provides no forecast products.

**Standards.** Japan's PM$\_{2.5}$ Environmental Quality Standard (established September 2009, Environmental Basic Law Article 16): 35 $\mu$g/m$^3$ daily average and 15 $\mu$g/m$^3$ annual average. The daily standard is assessed as the annual 98th-percentile of daily averages across stations, not a hard per-day cap. No revision has been made since 2009; both values are more lenient than WHO AQG 2021 (15/5 $\mu$g/m$^3$).

**Alert system.** Prefectural governments (not JMA or the national Ministry) issue non-binding precautionary advisories (注意喚起) using a two-level framework established by the MoE Expert Panel in February 2013:

| Level | Projected daily average | Recommended action |
|---|---|---|
| Level II (advisory) | > 70 $\mu$g/m$^3$ | Reduce outdoor activity; extra precaution for sensitive groups |
| Level I (attention, no advisory) | 35–70 $\mu$g/m$^3$ | Sensitive groups monitor health |

Because a full-day average is not available in the morning, advisories use SORAMAME real-time observations with operational proxy thresholds: early-morning stage (5–7 AM average of the 2nd-largest station in the zone) triggers at **85 µg/m$^3$**; midday stage (5 AM–noon average of the zone maximum) triggers at **80 µg/m$^3$**. Advisories are cancelled if all trigger-stations drop to ≤50 µg/m$^3$ for two consecutive hours.

**Operational forecast systems.** Japan has several national-level systems in production:

- **[VENUS](https://venus.nies.go.jp/)** (大気汚染予測システム VENUS) — operated by NIES under Ministry of Environment funding (from FY2014). Uses `WRF` (upgraded from `RAMS` in Version 3.0, August 2017) as the meteorological engine coupled with `CMAQ`, driven by NCEP/GFS global forecast data. Three nested domains: East Asia at **45 km**, expanded Japan at **15 km**, main Japan at **5 km**. PM$\_{2.5}$ forecasting added May 2013; horizon extended to **7 days** in March 2022. Categorical forecast accuracy was improved by 10.8–21.1 percentage points via statistical guidance post-processing (ERCA project 5MF-2201). Technical specifications: [venus.nies.go.jp/pages/](https://venus.nies.go.jp/pages/).

- **[SPRINTARS](https://sprintars.riam.kyushu-u.ac.jp/indexe.html)** (Spectral Radiation-Transport Model for Aerosol Species) — operated by Kyushu University RIAM, jointly developed with AORI (Univ. Tokyo), NIES, and JAMSTEC. SPRINTARS aerosol module embedded in the MIROC climate model, forced by NCEP GFS. Horizontal resolution ~35 km. Covers global, East Asia, and Asia domains; outputs PM$\_{2.5}$, PM$\_{10}$, and SPM. **7-day forecast**, updated daily around 04:00 JST. Explicitly experimental (no official liability disclaimer). Widely used by Japanese mass media for PM$\_{2.5}$ public communication.

- **[MASINGAR](https://www.data.jma.go.jp/env/kosa/fcst/en/)** — JMA/MRI global aerosol model at ~40 km (TL479L40, 40 vertical layers), fully operational since January 2004. Produces mineral dust (kosa/yellow sand) surface concentration forecasts **up to 96 hours ahead**, updated daily at 12 UTC. **Important caveat:** MASINGAR's public product covers mineral dust only — it is JMA's operational kosa (Asian dust) forecast tool, not a PM$\_{2.5}$ forecast. PM$\_{2.5}$ species (sulfate, black carbon, organic carbon) are simulated internally but not published as a public forecast product. JMA has no formal role in the PM$\_{2.5}$ advisory chain. Reference: [Yumimoto et al. (2018), *JMSJ* 96B, 2018-035](https://doi.org/10.2151/jmsj.2018-035).

- **[NHM-Chem](https://www.mri-jma.go.jp/Dep/glb/nhmchem_model/application_en.html)** — JMA/MRI regional chemistry model coupling the JMA Non-Hydrostatic Model (NHM) with three configurable aerosol representations. Used for operational ozone forecasting and transboundary aerosol studies. References: [Kajino et al. (2019), *JMSJ* 97(2)](https://doi.org/10.2151/jmsj.2019-020) and [Kajino et al. (2021), *Geosci. Model Dev.* 14, 2235](https://doi.org/10.5194/gmd-14-2235-2021).

Japan faces a distinct cross-border transport problem: significant PM$\_{2.5}$ episodes are driven by long-range transport from the Asian continent (particularly spring). MASINGAR and SPRINTARS are the main tools for attribution and 24–96-hour event anticipation.

### China — MEE/CNEMC National System

China has the largest ground-based PM$\_{2.5}$ monitoring network in the world. The **[China National Environmental Monitoring Centre (CNEMC)](https://air.cnemc.cn:18007/)**, under the [Ministry of Ecology and Environment (MEE)](https://www.mee.gov.cn/), operates real-time monitoring across more than 1,600 cities. Data are publicly accessible via the official national platform and third-party aggregators such as [aqicn.org](https://aqicn.org/).

**AQI standard.** China uses its own AQI system (HJ 633-2012), with 6 categories:

| AQI | Category | PM$\_{2.5}$ 24h ($\mu$g/m$^3$) |
|---|---|---:|
| 0–50 | Excellent | 0–35 |
| 51–100 | Good | 35–75 |
| 101–150 | Lightly Polluted | 75–115 |
| 151–200 | Moderately Polluted | 115–150 |
| 201–300 | Heavily Polluted | 150–250 |
| $>$ 300 | Severely Polluted | $>$ 250 |

**National standards (GB 3095-2012, Grade II):** 75 $\mu$g/m$^3$ 24-hour average and 35 $\mu$g/m$^3$ annual average — substantially higher than WHO 2021 guidelines (15/5 $\mu$g/m$^3$).

**Operational forecasting.** The national air quality forecast system uses an ensemble of numerical CTMs: `CUACE` (China Unified Atmospheric Chemistry Environment, developed by CMA), `NAQPMS` (Nested Air Quality Prediction Modeling System, developed by IAP/CAS), and `WRF-Chem`. City-level PM$\_{2.5}$ forecasts are issued for 3–7 days. Major cities such as Beijing, Shanghai, and Chengdu operate additional local ensemble systems with more frequent updates and finer resolution. Pollution alert levels (orange/red) trigger traffic and industrial emission controls.

A large share of the ML-based PM$\_{2.5}$ forecasting literature uses Chinese station data, reflecting the scale of the monitoring network and the severity of pollution events that stress-test model skill.

### Australia — State EPA Systems

Australia has no single national operational PM$\_{2.5}$ forecast system. Air quality monitoring and forecasting is the responsibility of state and territory environment protection authorities (EPAs), with the national standard set by the **[NEPM (National Environment Protection Measure) for Ambient Air Quality](https://www.nepc.gov.au/nepms/ambient-air-quality)**. The current binding standards (as of the 2015 NEPM revision) are 25 $\mu$g/m$^3$ 24-hour average and 8 $\mu$g/m$^3$ annual average.

Australia uses a 5-tier **Air Quality Category** scale — Good / Fair / Poor / Very Poor / Extremely Poor — with no numerical 0–500 score analogous to the US AQI. PM$\_{2.5}$ 24-hour breakpoints vary slightly by state; NSW marks "Poor" at ≥25 $\mu$g/m$^3$ while Victoria marks "Very Poor" beginning at ≥50 $\mu$g/m$^3$.

Major state monitoring platforms:

- **[Air Quality NSW](https://www.airquality.nsw.gov.au/)** (NSW DCCEEW + NSW Health) — daily AQI forecast for Greater Sydney issued at 4 pm
- **[EPA Victoria AirWatch](https://www.epa.vic.gov.au/check-air-and-water-quality)** — hourly data, daily 24-hour regional forecast updated at 5 pm; open [API portal](https://portal.api.epa.vic.gov.au/)
- **[Queensland DETSI Live Air Data](https://apps.des.qld.gov.au/air-quality/)** — real-time and historical data; no dedicated forecast product

**Bureau of Meteorology (BoM) role.** BoM supplies NWP meteorological grids that state EPAs ingest for their own forecast products but does not operate an independent operational PM$\_{2.5}$ forecast service. The research-level **ACCESS-UKCA** system (Unified Model + UKCA chemistry, joint BoM/UK Met Office) was in research-to-operational transition as of 2025. **TAPM** (CSIRO-developed NWP-coupled CTM) was widely used by state EPAs but CSIRO support ended around 2018–2020. Wildfire smoke forecasting during major incidents uses HYSPLIT and CSIRO tools coordinated through AFAC, with BoM NWP as meteorological input. The **[AirRater](https://airater.com.au)** app (ACT Health / ANU) provides smoke health guidance using BoM met and satellite AOD but is a nowcasting tool, not a full forecast system.

### Evaluation Metrics Used by Agencies

Major agencies do not publish RMSE or R$^2$ in the way the ML literature does. Their evaluation culture centres on categorical agreement and public-health thresholds, not continuous regression error. The metrics they use most are:

**Index Agreement (IA).** Willmott's Index of Agreement measures how well forecasts match observations relative to the mean bias:

$$
\text{IA} = 1 - \frac{\sum (O_i - F_i)^2}{\sum (|F_i - \bar{O}| + |O_i - \bar{O}|)^2}
$$

Range 0–1 (1 = perfect). CMAQ/NAQFC performance assessments routinely report IA alongside RMSE and mean bias. EPA's [Model Evaluation Protocol](https://www.epa.gov/air-quality-modeling/meteorological-model-performance-for-annual-2016-wrf-simulations) applies IA as a primary CTM skill metric.

**Categorical Skill (CSI / HSS).** For public-health decision support, agencies translate continuous PM$\_{2.5}$ into AQI categories and measure categorical forecast accuracy. The Critical Success Index (CSI) and Heidke Skill Score (HSS) measure how often the correct AQI category was forecast:

$$
\text{CSI} = \frac{\text{hits}}{\text{hits} + \text{misses} + \text{false alarms}}
$$

$$
\text{HSS} = \frac{\text{correct} - \text{expected correct by chance}}{N - \text{expected correct by chance}}
$$

These are especially relevant for "Unhealthy" or worse categories (US AQI ≥ 101), where false alarms and misses carry asymmetric public-health cost.

**Mean Fractional Bias (MFB) and Mean Fractional Error (MFE).** CAMS and US-EPA CTM evaluation papers typically report MFB and MFE rather than RMSE because they are scale-independent:

$$
\text{MFB} = \frac{2}{N} \sum \frac{F_i - O_i}{F_i + O_i}, \quad
\text{MFE} = \frac{2}{N} \sum \frac{|F_i - O_i|}{F_i + O_i}
$$

EPA's performance benchmark for PM$\_{2.5}$ CTMs: MFB within ±60% and MFE ≤75% ([Boylan & Russell, 2006](https://doi.org/10.1016/j.atmosenv.2006.02.051)).

**Practical implication for statistical models.** When comparing a statistical/ML model against an agency CTM baseline, reporting RMSE and R$^2$ alone is insufficient. Adding IA and at minimum one categorical skill metric (CSI or HSS at the local alert threshold) makes the comparison legible to both ML and agency audiences.

### Cross-Agency Summary

The table below contrasts the principal operational forecasting characteristics across the five regions:

| Agency / System | Primary Model | Horizon | Resolution | 24h PM$\_{2.5}$ Standard |
|---|---|---:|---:|---:|
| US EPA NAQFC | `CMAQ` + NWS met | 48 h | 12 km | 35.4 $\mu$g/m$^3$ |
| EU CAMS Regional | up to 11-model ensemble | 96 h | 10 km | 25 $\mu$g/m$^3$ (WHO 2021) |
| Japan NIES VENUS | `WRF` + `CMAQ` (offline) | 168 h (7 d) | 5–45 km (nested) | 35 $\mu$g/m$^3$ |
| Japan JMA MASINGAR | Global aerosol CTM | 96 h (4 d) | ~40 km | 35 $\mu$g/m$^3$ (dust only^) |
| Japan Kyushu SPRINTARS | `MIROC` + GFS | 168 h (7 d) | ~35 km | 35 $\mu$g/m$^3$ |
| China MEE/CNEMC | `CUACE` + `NAQPMS` ensemble | 72–168 h | ~3–9 km | 75 $\mu$g/m$^3$ |
| Australia state EPAs | `TAPM`/`WRF` + BoM NWP met | 24 h (state-by-state) | varies | 25 $\mu$g/m$^3$ |

Two observations stand out for the research literature context. First, every major agency uses a **CTM driven by NWP output** as its backbone, often supplemented with ensemble spread or human editing. Pure statistical or ML methods are not used in primary agency operations, though they appear in post-processing and bias-correction layers. Second, **national PM$\_{2.5}$ thresholds differ by a factor of 3–5 across regions** (China versus WHO), which directly affects how often "high pollution events" occur in any given training dataset and therefore how well published results transfer across regions.

---

## Forecasting Without a CTM: The Resource-Limited Setting

All of the agency systems above share a common assumption: the operator has access to an NWP-driven chemical transport model, an emissions inventory, and the computational infrastructure to run them. None of those prerequisites exist in the resource-limited setting — a single monitoring station with limited history and access only to public NWP forecast output (temperature, wind, humidity, precipitation) as meteorological input.

This setting is not a niche case. It describes the practical situation of:

- air quality research stations in Southeast Asia, Sub-Saharan Africa, and parts of South America where CAMS or NAQFC coverage is coarse and local CTMs do not exist
- low-cost sensor networks where monitoring density is high but instrument quality is uneven
- post-deployment evaluation of isolated regulatory monitors in developing-economy cities

The key differences from the agency context are summarized below:

| Dimension | Agency CTM approach | Resource-limited approach |
|---|---|---|
| Emission inventory | Required | Not available |
| Meteorological input | Own NWP run or NOAA/ECMWF fields | Public NWP forecast (GFS, ERA5, open-access) |
| Spatial coverage | Regional grid | Single station |
| Training data | Years of gridded reanalysis | Months to ~2 years of station observations |
| Update cycle | Twice-daily full model run | On-demand, lightweight inference |
| Computational budget | HPC cluster | Laptop or small server |

### What Works and What Does Not in This Setting

**Persistence** remains the hardest baseline to beat at `T+1h` and `T+6h`. In resource-limited experiments without lagged PM$\_{2.5}$ autoregression, weather-only features rarely outperform it at short horizons. Any claimed improvement over persistence at `T+1h` using weather features alone should be scrutinized.

**Statistical and ML methods that transfer well:**

- `XGBoost` / `LightGBM` with lagged PM$\_{2.5}$ + NWP forecast features. Consistent performance reported across single-station studies in Southeast Asian and Chinese cities; handles missing data and mixed-resolution feature sets without imputation. [Sayeed et al. (2021)](https://doi.org/10.1021/acs.est.1c02471) demonstrated skill at `T+24h` using only NWP-derived features at US monitoring stations, including for wildfire smoke events.
- `ARIMA`/`SARIMA` with exogenous meteorological regressors (ARIMAX/SARIMAX). A credible interpretable baseline at `T+24h` when 2+ years of data are available to fit seasonal structure. Performance degrades quickly with shorter records.
- Ridge regression and linear models with lag features and interaction terms. Often underrated — can match `XGBoost` when features are well-engineered and the pollution regime is stable. Very fast to retrain and interpretable for operational flagging.

**Methods that require caution in resource-limited settings:**

- `LSTM` and other deep sequence models require longer training histories (typically ≥2 years of hourly data) to regularize well. With short records, they overfit easily, and their apparent R$^2$ improvements over tree methods often disappear when evaluated on held-out seasonal periods not represented in training.
- Graph neural networks (`GCN`, `STGCN`) are irrelevant in a single-station setting by definition. Papers using these methods with good single-station metrics are reporting multi-station architectures applied to one output node — the multi-station data is the key resource.
- Transformer architectures have appeared in recent PM$\_{2.5}$ literature but are even more data-hungry than LSTM. There is no published evidence they outperform `XGBoost` on single-station datasets of less than 3 years.

### Input Features Available Without a CTM

In a setting where the only inputs are public NWP forecast output and local station history, the practical feature set is:

**Autoregressive (from station history):**
- lagged PM$\_{2.5}$: $t-1h$, $t-2h$, $t-3h$, $t-6h$, $t-24h$, $t-48h$
- rolling statistics: 3h mean, 24h mean, 24h max
- previous-day same-hour value (diurnal lag)

**Meteorological (from NWP forecast, valid at target horizon):**
- 2m temperature, relative humidity, dew point
- 10m wind speed and direction (sine/cosine encoded)
- surface pressure, boundary layer height (PBLH)
- precipitation rate or 6h accumulated precipitation
- total cloud cover or downwelling shortwave radiation (proxy for mixing)

**Temporal structure:**
- hour-of-day, day-of-week, month (cyclically encoded)
- weekday vs. weekend indicator (traffic proxy)
- season or meteorological season index

**PBLH is the single most important NWP-derived feature** at `T+6h` and `T+24h`. It captures the dilution capacity of the atmosphere — low PBLH coincides with nighttime/early morning accumulation events and stagnant winter episodes. Not all public NWP products expose PBLH directly; GFS does, ERA5 reanalysis does, and some regional NWP APIs expose it, but it should be explicitly verified before depending on it.

### The Weather-Only Horizon Limit

A consistent finding across published single-station studies is that PM$\_{2.5}$ autoregressive features dominate at short horizons and weather features dominate at longer ones — but "dominate" is relative. At `T+24h` with no lagged PM$\_{2.5}$ inputs (a common operational constraint when today's observations are not yet quality-controlled at forecast issuance time), purely weather-driven models show R$^2$ in the range 0.35–0.60 depending on location and season. This is well below agency CTM performance (IA typically 0.7–0.85 for CMAQ/CAMS) but may be the best achievable given the data constraint.

Two studies that directly address the weather-only horizon:

- [Sayeed et al. (2021), *Environ. Sci. Technol.* 55(8)](https://doi.org/10.1021/acs.est.1c02471) — trained a deep neural network on NWP features alone for US stations; R$^2$ ~0.50–0.65 at `T+24h`, skill drops sharply at `T+48h`.
- [Masih (2019), *Int. J. Environ. Res. Public Health* 16(12)](https://doi.org/10.3390/ijerph16122226) — compared ML methods for PM$\_{2.5}$ prediction under data-limited conditions; concluded that `Random Forest` with meteorological features is a practical minimum-viable model when historical PM$\_{2.5}$ records are short.

### Evaluation Protocol for the Resource-Limited Case

A resource-limited study should report the following minimum set to be comparable with the literature:

1. **Persistence skill score at each horizon** — the single most important baseline
2. **RMSE and NRMSE** (RMSE / mean PM$\_{2.5}$) — for cross-study comparison
3. **R$^2$** — on a holdout set spanning at least one seasonal cycle
4. **Mean bias** — directional error matters for public health communication
5. **CSI or F1 at the local alert threshold** — categorical skill at the operationally relevant cut-off
6. **Explicit statement of what meteorological input is used** — observed at issuance time, or true forecast (if forecast: which NWP product, which issuance time)

Omitting item 6 is the most common methodological gap in published resource-limited studies. A model evaluated with observed meteorology at forecast time is not operational — it is an upper-bound estimate of what a deployed system could achieve.

### Relevance to This Site's Hanoi Work

The Hanoi single-station experiments described on companion pages operate in exactly this resource-limited setting: one station, ~2 years of hourly data, GFS-derived meteorological forecast features, no CTM. The protocol above was used as the evaluation framework, and persistence was treated as a mandatory reported baseline at all horizons.

Related pages:

- [Hanoi PM$\_{2.5}$ Forecasting Experiments](/pages/research/hanoi-pm25-forecasting-experiments-2026.html)
- [Hanoi Forecasting Results vs Literature](/pages/research/hanoi-pm25-forecasting-literature-comparison.html)
- [Statistical Modeling](/pages/research/pm25-forecasting-statistical-modeling.html)

---

## Method Families

### Persistence

Persistence is the naive forecast:

$$
\text{PM}_{2.5}(t+h) = \text{PM}_{2.5}(t)
$$

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

### 2. PM$\_{2.5}$ History Is Dominant at Short Horizons

At `T+1h` and often `T+6h`, the recent PM$\_{2.5}$ state dominates feature importance. Weather becomes more valuable as the horizon extends.

### 3. Severe Event Detection Remains Weak

The literature reviewed here does not show a convincing solution for rare severe pollution events under high-precision operating points. Regression models often smooth away the extremes.

### 4. Method Comparisons Are Often Incomplete

Common reporting problems include:

- missing persistence baseline
- vague horizon definition
- no mean PM$\_{2.5}$, so NRMSE cannot be reconstructed
- evaluation only on the easiest horizon

## Recommended Reading Strategy

When using published PM$\_{2.5}$ forecasting papers to inform a build:

1. Compare only papers with explicit forecast horizons.
2. Normalize RMSE before comparing cities.
3. Separate single-station and multi-station results.
4. Check whether the paper uses observed future weather, archived forecasts, or true operational forecast inputs.
5. Treat severe-event claims carefully unless precision-recall metrics are shown.

## Implications for This Site's Hanoi Work

This review directly informed the design of the companion Hanoi forecasting study:

- persistence was treated as mandatory at all horizons
- multiple horizons were evaluated explicitly (`T+1h`, `T+6h`, `T+24h`, `T+48h`)
- atmospheric feature blocks were tested separately instead of being bundled blindly
- results were interpreted with normalized comparison in mind
- the resource-limited evaluation protocol from the section above was applied: NRMSE, R$^2$, mean bias, persistence skill score, and CSI at the local advisory threshold

---

{: .note }
**About this page.** The agency practice section (US EPA NowCast/NAQFC, EU CAMS, Japan VENUS/SPRINTARS/MASINGAR/NHM-Chem, China MEE/CNEMC, Australia state EPAs) and the resource-limited forecasting section were researched and drafted in June 2026 with the assistance of [Claude Sonnet 4.6](https://www.anthropic.com/claude) (Anthropic). Agency technical specifications were cross-checked against primary sources where accessible (NIES venus.nies.go.jp, CAMS ADS, NEPC nepc.gov.au, Marecal et al. 2015, Kajino et al. 2019/2021, Yumimoto et al. 2018, Boylan & Russell 2006); some figures — particularly for China's ensemble resolution — are best-knowledge estimates that should be verified against current agency publications before citation. AI-assisted content can contain errors. If you spot an inaccuracy, please raise it via the site's contact or open an issue on the [source repository](https://github.com/bi2air/bi2air.github.io).

{% unless jekyll.environment == "production" %}
## Source Note

This published page condenses a longer draft review from `tmp/air-quality-analysis-upstream/doc-work/pm25-forecasting-literature-review.md` for cleaner Jekyll presentation.
{% endunless %}

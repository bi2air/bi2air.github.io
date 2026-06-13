---
layout: default
title: AQI Calculation Guide
parent: "2020"
grand_parent: Research
nav_order: 1
description: "How AQI is calculated from PM$\_{2.5}$ — comparing US EPA, Vietnam, China, and WHO methods with equations and breakpoint tables"
---

# AQI Calculation Guide: From PM$\_{2.5}$ Concentration to Air Quality Index

![AQI color scale for the general public](/assets/images/research/aqi/aqi_kids_index.jpg)
*Courtesy of airnow.gov*

{: .note }
This guide explains how PM$\_{2.5}$ concentration becomes an AQI number. It compares the US EPA breakpoint method, Vietnam's updated (2019) calculation, and why the same AQI number means different PM$\_{2.5}$ levels in different countries.

---

## What is AQI?

AQI (Air Quality Index) is a single number representing outdoor air quality derived from six pollutants: PM$\_{10}$, PM$\_{2.5}$, NO2, CO, SO2, and O3. The reported AQI is the maximum of the individual index values calculated for each pollutant.

Key concepts:
1. **Each country defines its own permissible concentrations** — stricter standards yield higher AQI for the same air
2. **Two calculation approaches exist:** breakpoint interpolation (US EPA, Vietnam post-2019) and linear ratio (Australia, Vietnam pre-2019)
3. **Different averaging periods** produce different numbers from the same raw data — instant, hourly, daily, and NowCast concentrations are all distinct

![PM$\_{2.5}$ size scale](/assets/images/research/aqi/pm2.5_scale.jpg)
*PM$\_{2.5}$ particles are small enough to penetrate deep into the lungs. Courtesy of EPA.*

---

## PM$\_{2.5}$ Standards by Country

| | WHO 2005 | WHO 2021 | US EPA | China | Japan | Australia | Vietnam |
|--|----------|----------|--------|-------|-------|-----------|---------|
| **24-hour mean ($\mu g/m^3$)** | 25 | 15 | 35.4 | 75 | 35 | 25 | 50 |
| **Annual mean ($\mu g/m^3$)** | 10 | 5 | 12 | 35 | 15 | 8 | 25 |

WHO revised its guidelines substantially downward in 2021, roughly halving both thresholds. No major national regulatory standard has yet been updated to match the 2021 values — the US EPA 2024 revision tightened the annual standard to 9 µg/m$^3$ but left the 24-hour standard unchanged. Australia retains the strictest annual standard among national regulators (8 µg/m$^3$). Vietnam's standard is moderate relative to its economic status — stricter than China's for the 24-hour average.

---

## Concentration Types

Before calculating AQI, you need the right concentration value:

| Type | Definition | Use |
|------|-----------|-----|
| **Instant** | Single sensor reading (per second to minute) | Raw data only |
| **Hourly** | Average of all readings in one hour | Real-time display |
| **Daily** | Average of all readings in one calendar day | Comparison to 24-hour standards |
| **NowCast** | Weighted average of last 12 hours | Real-time AQI forecasting |

### NowCast Formula

NowCast gives more weight to recent hours, making it responsive without being noisy:

$$
\mathrm{PM_{2.5}}_{\mathrm{nowcast}} = \frac{\sum_{i=1}^{12} w^{i-1} c_i}{\sum_{i=1}^{12} w^{i-1}}
$$

Where:
- $c_i$ = hourly concentration ($i = 1$ is most recent)
- $w = \max(c_{\min}/c_{\max},\ 0.5)$, where $c_{\min}$ and $c_{\max}$ are the minimum and maximum concentrations in the 12-hour window

The weighting factor $w$ ensures recent hours dominate when air quality is changing rapidly. At least 2 of the 3 most recent hours must be valid for NowCast to be reported.

{: .warning }
**NowCast is not a forecast.** It is a lag-correction applied to already-measured data — a weighted summary of the past 12 hours, not a prediction of future conditions. It is specifically designed to make the AQI display more responsive to rapid deterioration. Using NowCast output as a forecasting target is valid (it is what AirNow displays), but any study doing this must state clearly that the model is predicting a weighted moving average, not an instantaneous or 24-hour concentration. See the [PM$\_{2.5}$ Forecasting Literature Review](/pages/research/pm25-forecasting-literature-review.html) for how this distinction affects operational use.

---

## Calculation Methods

### Method 1: Breakpoint Interpolation (US EPA)

$$
AQI_p = \frac{I_{Hi} - I_{Lo}}{BP_{Hi} - BP_{Lo}} (C_p - BP_{Lo}) + I_{Lo}
$$

Where:
- $C_p$ = pollutant concentration
- $BP_{Hi}, BP_{Lo}$ = concentration breakpoints bounding $C_p$
- $I_{Hi}, I_{Lo}$ = AQI index values corresponding to those breakpoints

![EPA PM$\_{2.5}$ breakpoint table](/assets/images/research/aqi/EPA_breakpoints_PM2.5.png)
*US EPA breakpoints for PM$\_{2.5}$ (24-hour and annual).*

**Example:** PM$\_{2.5}$ = 30 $\mu g/m^3$ (24-hour mean)

Look up: falls in the 12.1-35.4 bracket (AQI 51-100)

$$
AQI = \frac{100 - 51}{35.4 - 12.1} (30 - 12.1) + 51 \approx 88
$$

### Method 2: Linear Ratio (Australia, Vietnam pre-2019)

$$
AQI_p = \frac{C_p}{C_{\mathrm{standard}}} \times 100
$$

Where $C_{\mathrm{standard}}$ is the permissible concentration for that pollutant.

This is simpler: AQI 50 means the concentration is half the standard. But it produces a purely linear scale with no breakpoints.

**Example:** PM$\_{2.5}$ = 25 $\mu g/m^3$ in Vietnam (C_standard = 50)

$$
AQI = \frac{25}{50} \times 100 = 50
$$

Same concentration in Australia ($C_{\mathrm{standard}} = 25$):

$$
AQI = \frac{25}{25} \times 100 = 100
$$

---

## Vietnam's 2019 Update

In November 2019 (Decision 1459/QD-TCMT), Vietnam switched from Method 2 to Method 1 — adopting breakpoint interpolation similar to the US EPA approach. This makes the calculation identical in structure, though the breakpoints differ due to different permissible concentrations.

## China AQI (HJ 633-2012)

China uses its own AQI system defined in standard HJ 633-2012. The structure is also breakpoint interpolation (same as US EPA), but the PM$\_{2.5}$ thresholds are much higher, reflecting China's current 24-hour standard of 75 µg/m$^3$:

| AQI | Category | PM$\_{2.5}$ 24h ($\mu$g/m$^3$) | Health guidance |
|---|---|---:|---|
| 0–50 | Excellent | 0–35 | No restriction |
| 51–100 | Good | 35–75 | General population: no restriction |
| 101–150 | Lightly Polluted | 75–115 | Sensitive groups: reduce outdoor activity |
| 151–200 | Moderately Polluted | 115–150 | Sensitive groups: avoid outdoor activity |
| 201–300 | Heavily Polluted | 150–250 | General population: reduce outdoor activity |
| >300 | Severely Polluted | >250 | All outdoor activity suspended |

The top category (Severely Polluted, AQI >300) corresponds to PM$\_{2.5}$ levels that would be mapped to a US AQI of approximately 400–500 (Hazardous range). This means a Chinese "Good" reading (AQI 51–100, PM$\_{2.5}$ up to 75 µg/m$^3$) would be classified US "Unhealthy for Sensitive Groups" or higher. The two indices are not directly comparable and should never be reported on the same axis without labelling.

## Other Regional AQI Systems

**European CAQI.** The EU Common Air Quality Index uses a 0–100+ scale. PM$\_{2.5}$ background bands: Very Low 0–15, Low 15–30, Medium 30–55, High 55–110, Very High >110 µg/m$^3$. The overall CAQI is the maximum sub-index across pollutants. Adopted by ~20 European countries; displayed on the [EEA European Air Quality Index](https://www.eea.europa.eu/en/topics/in-depth/air-pollution/european-air-quality-index) viewer.

**UK DAQI.** The Daily Air Quality Index uses a 1–10 scale grouped into four named bands. PM$\_{2.5}$ 24-hour breakpoints:

| DAQI Level | Band | PM$\_{2.5}$ ($\mu$g/m$^3$) |
|---|---|---:|
| 1–3 | Low | 0–35 |
| 4–6 | Moderate | 36–53 |
| 7–9 | High | 54–70 |
| 10 | Very High | ≥71 |

Health advice escalates from Level 4 onward for sensitive groups and from Level 10 for the general population. Note that DAQI Level 2 (up to 23 µg/m$^3$) already exceeds the WHO 2021 24-hour guideline of 15 µg/m$^3$.

**Japan prefectural advisory.** Japan does not use a named AQI scale for PM$\_{2.5}$. Instead, prefectural governments issue advisories when a forecast daily average is expected to exceed **70 µg/m$^3$** — the public communication threshold, not an index. Real-time monitoring data are available via the national [SORAMAME (そらまめ君)](https://soramame.env.go.jp/) network.

---

## Comparing US and Vietnam AQI

![AQI comparison table: US vs Vietnam](/assets/images/research/aqi/AQI_bio.info_2019.png)
*Same AQI category, different PM$\_{2.5}$ thresholds: "Good" in Vietnam allows higher PM$\_{2.5}$ than "Good" in the US.*

![AQI conversion charts](/assets/images/research/aqi/AQI_bioinfo_sm.png)

![AQI vs concentration curves](/assets/images/research/aqi/AQI_bioinfo_lg.png)
*Converting PM$\_{2.5}$ concentration to AQI by both standards. The US EPA curve is steeper at lower concentrations — stricter for "Good" and "Moderate" categories.*

Key differences:
- For Good/Moderate categories, the same AQI number corresponds to **lower PM$\_{2.5}$** under US EPA (stricter)
- For Unhealthy/Hazardous categories, Vietnam's standard triggers at **lower PM$\_{2.5}$** (stricter at the high end)
- After the 2019 update, the structural calculation is identical — only the breakpoint values differ

---

## AQI Health Scale

![AQI categories and health effects](/assets/images/research/aqi/ScooterBlog_AQI.png)
*Standard AQI color bands used by most reporting systems.*

---

## Takeaways

- AQI is country-specific — the same air can have different AQI values depending on which standard is applied
- Two calculation methods: breakpoint interpolation (flexible, non-linear) and linear ratio (simple)
- Vietnam adopted the US EPA breakpoint method in November 2019
- For lower AQI categories (Good, Moderate), the US standard is stricter
- When comparing AQI numbers, always check which standard was used
- WHO 2021 guidelines are roughly half the 2005 values; no major national standard has yet matched them
- NowCast is a reporting formula, not a forecast

## Further Reading

The companion forecasting literature review covers how AQI systems connect to operational PM$\_{2.5}$ forecasting, including how agencies convert continuous model output into AQI categories for public communication:

- [PM$\_{2.5}$ Forecasting Literature Review](/pages/research/pm25-forecasting-literature-review.html) — agency systems (US NAQFC, EU CAMS, Japan VENUS/SPRINTARS/MASINGAR, China MEE, Australia BoM), evaluation metrics (IA, CSI, MFB), and the resource-limited single-station forecasting problem
- [Hanoi PM$\_{2.5}$ Forecasting Experiments](/pages/research/hanoi-pm25-forecasting-experiments-2026.html)
- [Statistical Modeling](/pages/research/pm25-forecasting-statistical-modeling.html)

---

## References

1. Decision 1459/QD-TCMT (Nov 12, 2019) — Vietnam AQI calculation guidance
2. MONRE Handbook for AQI Calculation (2015)
3. US EPA Technical Assistance Document for AQI Reporting (2018)
4. WHO Ambient Air Quality Guidelines
5. QCVN 05:2013/BTNMT — Vietnam National Technical Regulation on Ambient Air Quality
6. Evaluation of the Chinese New Air Quality Index (GB3095-2012), Fanyu Gao

---

*Originally published on b-io.info, updated January 2020.*

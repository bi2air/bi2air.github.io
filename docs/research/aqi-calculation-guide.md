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

| | WHO | US EPA | China | Australia | Vietnam |
|--|-----|--------|-------|-----------|---------|
| **24-hour mean ($\mu$g/m$^3$)** | 25 | 35 | 75 | 25 | 50 |
| **Annual mean ($\mu$g/m$^3$)** | 10 | 12 | 35 | 8 | 25 |

Australia adopted the strictest annual standard (8 $\mu$g/m$^3$). Vietnam's standard is moderate relative to its economic status — stricter than China's.

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
\mathrm{PM$\_{2.5}$}_{\mathrm{nowcast}} = \frac{\sum_{i=1}^{12} w^{i-1} c_i}{\sum_{i=1}^{12} w^{i-1}}
$$

Where:
- $c_i$ = hourly concentration ($i = 1$ is most recent)
- $w = \max(c_{\min}/c_{\max}, 0.5)$

The weighting factor w ensures recent hours dominate. At least 2 of the 3 most recent hours must be valid.

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

**Example:** PM$\_{2.5}$ = 30 $\mu$g/m$^3$ (24-hour mean)

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

**Example:** PM$\_{2.5}$ = 25 $\mu$g/m$^3$ in Vietnam (C_standard = 50)

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

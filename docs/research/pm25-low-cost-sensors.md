---
layout: default
title: Low-Cost PM$_{2.5}$ Sensors
parent: "2019"
grand_parent: Research
nav_order: 1
description: "Calibration and comparison of SDS011 and PMS7003 low-cost sensors against a FEM reference station in Hanoi, Vietnam"
---

# Low-Cost PM$_{2.5}$ Sensors: Calibration Data for SDS011 and PMS7003

![Low-cost PM$_{2.5}$ sensors: SDS011 and PMS7003](/assets/images/research/sensors/low_cost_sensors.jpg)

{: .note }
This study was conducted in Hanoi, Vietnam during the first half of 2019, in collaboration with the SPARC lab at Hanoi University of Science and Technology. The reference station was the US Embassy MetOne BAM-1020.

---

## Abstract

Low-cost particulate sensors offer two distinct advantages: affordability and continuous, near-real-time readings with minimal setup. Their main drawback is dependence on laboratory-grade instruments for calibration.

This study compares three sensors measuring fine particulate matter (PM$_{2.5}$): the SDS011, PMS7003, and HPMA115S0. Sensor readings were compared with a reference station using a Federal Equivalent Method (FEM) monitor (MetOne BAM-1020). The goodness-of-fit (R$^2$) ranged from 0.51 to 0.66, indicating moderate agreement between low-cost sensors and the reference. Despite limited accuracy, the fractional cost of these sensors enables dense air-quality monitoring networks that would be impractical with FEM instruments alone.

---

## Sensor Specifications

| Parameter | PMS7003 | SDS011 | HPMA115S0 | Dylos DC1100 Pro |
|-----------|---------|--------|-----------|-----------------|
| Price | ~$13 | ~$19 | ~$19 | ~$290 |
| Range ($\mu$g/m$^3$) | 0-500 (1000 max) | 0-999 | 0-1000 | N/A |
| Stated error | 10%, +/-10 $\mu$g/m$^3$ | 15%, +/-10 $\mu$g/m$^3$ | 15%, +/-10 $\mu$g/m$^3$ | N/A |
| Lifespan | 8,000 h | 8,000 h | 20,000 h | Several years |
| Communication | Serial, 9600 baud | Serial, 9600 baud | Serial, 9600 baud | Proprietary |
| Output | PM1, PM$_{2.5}$, PM$_{10}$ + 6 size bins | PM$_{2.5}$, PM$_{10}$ (float) | PM$_{2.5}$, PM$_{10}$ (int) | Small (>0.5um), Large (>2.5um) |

All three low-cost sensors use laser light scattering to estimate particle concentration. The measurement principle relies on Mie scattering theory: a laser beam illuminates particles drawn through a chamber, and a photodetector measures scattered light intensity to infer particle count and size distribution.

![SDS011 and PMS7003 sensors](/assets/images/research/sensors/SDSPMS.png)

On specifications alone, the PMS7003 stands out for its low cost, small footprint, and rich output (6 size bins from 0.3 um). The SDS011 offers a sampling hose for remote air intake. The HPMA115S0 benefits from Honeywell's industrial documentation.

---

## Literature: Collocation Studies

Published collocation studies comparing these sensors with FEM instruments:

| Study | PMS7003 | SDS011 | HPMA115S0 | DC1100 Pro |
|-------|---------|--------|-----------|------------|
| US EPA | -- | -- | -- | R$^2$ = 0.5-0.6 |
| AQ-SPEC | R$^2$ = 0.85-0.97 (PMS5003 variants) | -- | -- | R$^2$ = 0.81 |
| Johnston (2019), UK | rho = 0.88 | -- | rho = 0.85 | -- |
| Badura (2018), Poland | R$^2$ = 0.73-0.75 | R$^2$ = 0.66-0.70 | -- | -- |
| Liu (2018), Norway | -- | R$^2$ = 0.71-0.80 | -- | -- |

Consensus from 10+ reports: SDS011 and PMS7003 overestimate PM$_{2.5}$ relative to FEM devices, with field-test R$^2$ values typically in the 0.6-0.8 range.

---

## Method

### Setup

- **Sensors:** PMS7003 (from SPARC/AirSENSE kit) and SDS011 (purchased independently)
- **Reference:** US Embassy Hanoi, MetOne BAM-1020 (FEM)
- **Distance:** Sensor site was 5.3 km southwest of the reference station

![Sensor and reference station locations in Hanoi](/assets/images/research/sensors/map.jpg)

- **Duration:** ~60 days of continuous hourly data
- **Data collection:** Raspberry Pi with Python scripts; also tested with ESP8266/ESP32 using Arduino libraries
- **Software:** Custom Python library for PMS7003 (supports simultaneous reading of 4 sensors)

### Data Cleaning

Raw data was filtered to remove single-peak anomalies exceeding 300 $\mu$g/m$^3$. PMS7003 produced more anomalous peaks than SDS011. After cleaning, 1,451 valid hourly observations remained for analysis.

![60 days of continuous PM$_{2.5}$ data](/assets/images/research/sensors/60days_data.png)

---

## Results

### Correlation with Reference Station

| Pair | R$^2$ | Slope |
|------|-----|-------|
| PMS7003 vs. BAM | 0.66 | 0.66 |
| SDS011 vs. BAM | 0.51 | 0.77 |
| SDS011 vs. PMS7003 | 0.84 | 0.81 |

Both sensors overestimated PM$_{2.5}$ relative to the BAM reference. The PMS7003 showed greater overestimation (slope 0.66 implies BAM reads ~66% of PMS7003 values) but better correlation. The strong R$^2$ of 0.84 between the two low-cost sensors suggests the 5.3 km distance from the reference station accounts for some of the lower R$^2$ values against BAM.

![Scatter plot: SDS011 vs PMS7003 vs BAM reference](/assets/images/research/sensors/plot_sds_pms_bam.png)

![Calibration correction factors](/assets/images/research/sensors/calibrate_sensor_ad.png)

### Key Observations

- At low concentrations, correlation between sensors and reference is high
- At higher PM$_{2.5}$, both sensors systematically overestimate relative to BAM
- After applying correction factors from Table 3, adjusted sensor values track the reference well
- Results are consistent with published literature (Table 2)

---

## Summary

- SDS011 overestimated PM$_{2.5}$ by ~30% relative to BAM
- PMS7003 overestimated PM$_{2.5}$ by ~52% relative to BAM
- R$^2$ values (0.51-0.66) are lower than other published studies, likely due to the 5.3 km separation and northeast wind patterns during winter/spring in Hanoi
- The strong inter-sensor correlation (R$^2$ = 0.84) supports the hypothesis that distance, not sensor quality, is the primary source of disagreement with the reference
- Either sensor is suitable for low-cost PM$_{2.5}$ monitoring with appropriate calibration against a local reference

---

## References

- US EPA sensor evaluation reports
- AQ-SPEC (South Coast AQMD) sensor testing program
- Johnston et al. (2019), UK field evaluation
- Badura et al. (2018), Poland collocation study
- Liu et al. (2018), Norway SDS011 evaluation

---

*Originally published on b-io.info, 2019. Data collected in collaboration with SPARC Lab, Hanoi University of Science and Technology.*

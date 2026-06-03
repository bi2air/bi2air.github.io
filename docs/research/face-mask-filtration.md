---
layout: default
title: Face Mask Filtration
parent: Research
grand_parent: Documentation
nav_order: 2
description: "PM2.5 and PM10 removal efficiency of fabric, surgical, air masks, and particulate respirators tested with low-cost sensors in Hanoi"
---

# Face Mask Filtration: PM2.5 and PM10 Removal Efficiency

![Masks tested in this study](/assets/images/research/masks/mask_gallery.jpg)

{: .note }
This study evaluated 11 masks over 55 days using an improvised testing apparatus with PMS7003 sensors. It measures material filtration efficiency only; face-seal fit was not evaluated.

---

## Abstract

Four types of face masks were evaluated for particulate matter removal efficiency (RE): fabric, surgical, "air masks" (marketed for pollution), and brand-name particulate respirators. Masks were mounted on a 6 cm PVC pipe, and air was drawn through by a variable-speed fan. PM2.5 and PM10 were measured upstream and downstream using Plantower PMS7003 sensors.

**Results by mask type:**

| Type | PM2.5 Removal | PM10 Removal |
|------|--------------|--------------|
| Fabric | 8-14% | 8-14% |
| Surgical | 29-39% | 29-39% |
| Air mask (marketed) | 0-41% (inconsistent) | 0-41% |
| 3M respirator (KN90/FFP3) | 47-62% | 52-62% |
| AQBlue / Airphin | 90-95% | 92-94% |

A negative correlation between airflow rate and RE (-0.76 to -0.89 for surgical and air masks) confirmed that higher flow reduces filtration. The 3M Aura showed a weaker correlation (-0.51), indicating design improvements that maintain RE at higher airflow.

---

## Background

Hanoi's 6 million motorbikes (10x the number of passenger cars) expose commuters to high PM2.5 levels. By observation, 60-80% of riders wear masks, with fabric masks dominant. Yet fabric offers minimal protection against fine particles.

Previous work (Shakya et al., 2016) found fabric mask efficiency of 15-57% with diesel exhaust, while N95 respirators showed only marginal improvement over surgical masks for PM2.5 specifically. The WHO reports 4.3 million annual deaths from indoor and 3.7 million from outdoor air pollution, with higher mortality in developing countries.

Analysis of US Embassy monitoring data (2016-2019) shows Hanoi meets Vietnam's daily PM2.5 standard ("good" level) only 26% of the time. By the WHO's stricter 25 ug/m3 daily limit (50% lower than Vietnam's standard), the situation is worse.

---

## Method

### Apparatus

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/masks/mask_location.jpg" alt="Annotated apparatus showing PVC pipe, clear plastic boxes, and PMS7003 sensors">
    <figcaption>Annotated test setup with the PVC pipe, testing box, and background monitoring box.</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/masks/mask_on_pipe.jpg" alt="Mask mounted on the PVC pipe during the filtration experiment">
    <figcaption>Mask mounted on the PVC pipe during a filtration run.</figcaption>
  </figure>
</div>

- Mask mounted flat on a 6 cm PVC pipe
- Fan with variable duty cycle (surrogate for airflow rate)
- Two PMS7003 sensors: one downstream of mask (filtered air), one measuring ambient background
- Location: 10th floor balcony, light ground-level traffic
- Each mask tested 2-6 days with 1-minute sampling interval

### Data Processing

Over 45 days, ~65,000 data points collected per sensor. Cleaning steps:
- Removed single anomalous peaks (10 iterative rounds)
- 3.4% of mask data removed; 1.7% of background data removed
- Each experiment segmented into 90-120 min crosscheck (both sensors exposed to same air) followed by filtration period

![Data cleaning: before and after anomaly removal](/assets/images/research/masks/cleaning.png)

### Removal Efficiency Calculation

RE = (Background PM - Filtered PM) / Background PM

Crosscheck periods confirmed sensor agreement (RE near zero when no mask mounted), validating the apparatus.

| ![Background vs filtered PM2.5](/assets/images/research/masks/bg_rm.png) | ![PM2.5 removal efficiency](/assets/images/research/masks/pm2.5_rm.png) | ![PM10 removal efficiency](/assets/images/research/masks/pm10_rm.png) |
|:---:|:---:|:---:|
| Background vs filtered | PM2.5 removal | PM10 removal |

---

## Results

### All Masks

| Group | Mask ID | PM2.5 RE | PM10 RE | Fan Duty |
|-------|---------|----------|---------|----------|
| Fabric | FU1 | 0.13 +/- 0.07 | 0.14 +/- 0.08 | 0.58 |
| Fabric | FU2 (#1) | 0.09 +/- 0.06 | 0.08 +/- 0.05 | 0.63 |
| Fabric | FU2 (#2) | 0.15 +/- 0.09 | 0.12 +/- 0.01 | 0.51 |
| Fabric | FN | 0.11 +/- 0.06 | 0.12 +/- 0.07 | 0.53 |
| Surgical | S1 | 0.29 +/- 0.12 | 0.29 +/- 0.13 | 0.58 |
| Surgical | S2 (#1) | 0.29 +/- 0.13 | 0.34 +/- 0.14 | 0.51 |
| Surgical | S2 (#2) | 0.33 +/- 0.06 | 0.33 +/- 0.08 | 0.55 |
| Surgical | S3 | 0.37 +/- 0.13 | 0.39 +/- 0.10 | 0.62 |
| Air mask | A1 | 0.03 +/- 0.06 | 0.03 +/- 0.08 | 0.53 |
| Air mask | A2N | 0.41 +/- 0.09 | 0.40 +/- 0.10 | 0.58 |
| Air mask | A2U | 0.37 +/- 0.10 | 0.39 +/- 0.11 | 0.61 |
| 3M | 3M1 (KN90) | 0.47 +/- 0.08 | 0.52 +/- 0.07 | 0.56 |
| 3M | 3M2 Aura (#1) | 0.57 +/- 0.09 | 0.59 +/- 0.09 | 0.60 |
| 3M | 3M2 Aura (#2) | 0.56 +/- 0.09 | 0.62 +/- 0.07 | 0.62 |
| 3M | 3M (old) | 0.51 +/- 0.09 | 0.52 +/- 0.09 | 0.56 |
| AQBlue | AQ1 | 0.94 +/- 0.04 | 0.94 +/- 0.04 | 0.60 |
| AQBlue | AQ2 | 0.92 +/- 0.05 | 0.92 +/- 0.04 | 0.62 |

### Microscopy Observations

USB microscope images of mask construction revealed:

| ![Fabric mask layers](/assets/images/research/masks/fabric.jpg) | ![Surgical mask layers](/assets/images/research/masks/surgical.jpg) |
|:---:|:---:|
| Fabric: 3 layers, loose polyester middle | Surgical: 4-5 tightly packed layers |

| ![Air mask construction](/assets/images/research/masks/airmask.jpg) | ![3M respirator layers](/assets/images/research/masks/3m.jpg) |
|:---:|:---:|
| Air mask: varies by model | 3M respirator: 5 layers, thick middle |

| ![AQBlue filter](/assets/images/research/masks/AQBlue.jpg) |
|:---:|
| AQBlue: highest filtration (90-95%) |

- **Fabric:** 3 layers (cotton outer, loose polyester middle, support inner). Middle layer loosely packed — visibly porous relative to PM2.5 particle size.
- **Surgical:** 4-5 tightly packed layers. One middle layer composed of dense, fine fibers.
- **Air mask A1:** Single layer of randomly woven polyester. Pore size comparable to a human hair (~60-70 um) — roughly 30x larger than PM2.5. No effective filtration.
- **Air mask A2:** 5 layers with fine fiber middle layer. Effective.
- **3M respirators:** 5 layers. The Aura model features a thick, pillow-like middle layer; the 9001 has two fine-fiber middle layers.

### Airflow vs. Removal Efficiency

| Mask Type | Correlation (fan duty vs. RE) | Interpretation |
|-----------|-------------------------------|----------------|
| Fabric | Near zero | Too porous for meaningful filtration at any flow |
| Surgical | -0.76 to -0.89 | Strong negative: higher flow degrades RE significantly |
| Air mask | -0.76 to -0.89 | Same pattern as surgical |
| 3M Aura | -0.51 | Moderate negative: design allows higher airflow with less RE loss |

| ![Fan vs RE: Fabric](/assets/images/research/masks/fan_fabric.png) | ![Fan vs RE: Surgical](/assets/images/research/masks/fan_surgical.png) |
|:---:|:---:|
| Fabric: no correlation (already porous) | Surgical: strong negative correlation |

| ![Fan vs RE: 3M](/assets/images/research/masks/fan_3m.png) | ![Fan vs PM2.5 RE all masks](/assets/images/research/masks/fan_pm2_5.png) |
|:---:|:---:|
| 3M Aura: moderate correlation | All masks: PM2.5 removal vs fan duty |

---

## Limitations

1. **No face-seal test.** Masks were mounted flat on a pipe. Real-world leakage around the nose and cheeks reduces effective RE. Results represent maximum material filtration efficiency only.

2. **Form factor varies by type.** Surgical masks are not designed to seal around the face. Fabric masks conform better but use inadequate materials. Even a well-designed mask depends on individual facial geometry.

3. **Not comparable to manufacturer ratings.** Standard certification (NIOSH 42 CFR 84, EN 149, GB 2626) uses controlled aerosols and calibrated equipment. This study used ambient air and low-cost sensors, simulating on-road conditions rather than laboratory conditions.

4. **Ambient testing location.** A 10th-floor balcony with light ground traffic is an approximation of street-level exposure.

---

## Conclusions

![Overview: PM2.5 removal efficiency across all masks](/assets/images/research/masks/removal_overview_allmasks.png)

- **Fabric masks** (dominant on Hanoi streets) provide negligible PM2.5 protection (8-14% RE)
- **Surgical masks** offer moderate filtration (29-39%) but poor face seal makes real-world benefit uncertain
- **"Air masks"** marketed for pollution are inconsistent — one model showed 0-3% RE, another 37-41%
- **3M particulate respirators** (KN90/FFP3) achieved 47-62% material RE, with design features that resist degradation at higher airflow
- **AQBlue** respirators showed the highest RE at 90-95%
- Higher airflow consistently reduces RE, except for fabric masks (already too porous to filter)
- Choosing a certified brand-name mask and wearing it properly is the single most practical recommendation

---

## Acknowledgements

Thanks to Dr. Han Huy-Dung for lending PMS7003 sensors, and to the SPARC lab at Hanoi University of Science and Technology for collaboration on sensor evaluation.

---

*Originally published on b-io.info, 2019. 14 tests on 11 masks over a 55-day period.*

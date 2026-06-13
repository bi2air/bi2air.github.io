---
layout: default
title: Used Mask Filtration
parent: "2019"
grand_parent: Research
nav_order: 5
description: "PM$\_{2.5}$ removal efficiency of used and washed face masks (AQBlue, Airphin) — follow-up to the new mask filtration study"
---

# Used Mask Filtration: Can You Wash and Reuse PM$\_{2.5}$ Masks?

![Used masks tested in this study](/assets/images/research/used-masks/used_masks.jpg)

{: .note }
Follow-up to the [face mask filtration study](/pages/research/face-mask-filtration.html). Used masks retain 74% removal efficiency; washed masks achieve 82%. Both are acceptable alternatives to disposal after single use.

---

## Abstract

In the [previous study](/pages/research/face-mask-filtration.html), new particulate respirator masks (AQBlue, Airphin) achieved ~90% PM$\_{2.5}$ removal efficiency (RE). However, at 35-50k VND per mask (US$1.50-2.20), weekly replacement is expensive for low-to-medium income commuters.

This study tested whether used and washed masks retain acceptable filtration:

| Condition | PM$\_{2.5}$ Removal Efficiency |
|-----------|-------------------------|
| New | ~90% |
| Used (2-3 weeks daily commute) | 74% +/- 10% |
| Washed (tap water, air dried) | 82% +/- 12% |

Washing and reusing dedicated PM$\_{2.5}$ masks 1-2 times is a viable cost-saving strategy with only moderate loss in filtration.

---

## Background

Fabric masks dominate in Vietnam due to low cost and washability — many users have been washing and reusing the same fabric mask for 2+ years. When dedicated PM$\_{2.5}$ masks (like AQBlue) are available, the habit of washing and reusing carries over naturally.

A 2005 study in Vietnam found that hospital staff preferred reusable masks due to institutional budget constraints. If brand-name PM$\_{2.5}$ masks can survive one wash with reasonable RE, the effective cost per use drops by half.

---

## Method

- **Setup:** Identical to the [original mask study](/pages/research/face-mask-filtration.html) — two PMS7003 sensors (background and filtered), mask mounted on PVC pipe with variable-speed fan
- **Masks tested:** 3 AQBlue masks, 1 Airphin mask
- **Conditions:** New, used (2-3 weeks daily commute), washed (tap water, hang-dried)
- **Fan duty:** Automated cycling through 25%, 50%, 75%, 100% using a NodeMCU microcontroller, 3 hours per level
- **Duration:** ~2 days per test

---

## Results

### Overall Removal Efficiency

![RE of used and washed masks](/assets/images/research/used-masks/removal_wash_used_all.png)
*Fig. 1: Average PM$\_{2.5}$ removal efficiency. Cross-check periods (both sensors measuring same air) confirm near-zero RE baseline. Error bars = 2 standard deviations.*

Key findings:
- **Used masks:** 74 +/- 10% RE
- **Washed masks:** 82 +/- 12% RE
- Both are 10-20% lower than new masks (~90%)

### Effect of Fan Speed (Airflow) on RE

![RE by mask condition across fan speeds](/assets/images/research/used-masks/pm25_removal_fan_condition.png)
*Fig. 2: RE vs fan duty by condition (new, used, washed). Higher flow slightly improves RE within each condition.*

### RE vs PM$\_{2.5}$ Concentration

![RE of AQBlue masks by condition](/assets/images/research/used-masks/pm25_removal_aqblue.png)
*Fig. 3: New masks consistently outperform used and washed across the PM$\_{2.5}$ range (0-200 $\mu g/m^3$).*

### Brand Comparison (Used Condition)

![AQBlue vs Airphin used masks](/assets/images/research/used-masks/pm25_removal_fan_used_brand.png)
*Fig. 4: AQBlue showed wider RE range; Airphin was more consistent. Overlapping performance with limited sample size (3 AQBlue, 2 Airphin).*

---

## Limitations

- Small sample size (4 masks total)
- Only 1 wash cycle tested — multiple washes likely degrade RE further
- Fan-driven airflow does not replicate human breathing rhythm (~12 breaths/min, 0.5L each)
- No sanitization assessment — washing removes PM but may not eliminate biological contamination
- These masks are not designed for reuse; the manufacturer recommends single use

---

## Conclusions

- **Used masks (2-3 weeks)** retain ~74% PM$\_{2.5}$ removal efficiency — acceptable for continued use
- **One wash** recovers some performance to ~82%, possibly by removing accumulated particles from the filter layers
- **Recommendation:** Dedicated PM$\_{2.5}$ masks can be used for 2-3 weeks and washed once before disposal, reducing cost by roughly half
- For commuters who cannot afford frequent replacement, reuse with a single wash is a practical compromise between cost and protection

---

*Originally published on b-io.info, 2019. Follow-up study to the face mask filtration evaluation.*

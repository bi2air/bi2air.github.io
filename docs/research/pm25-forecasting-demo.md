---
layout: default
title: Demo
parent: PM$\_{2.5}$ Forecasting
grand_parent: "2026"
nav_order: 3
description: "Demo page for comparing predicted PM$\_{2.5}$ values against measured concentration."
---

# Demo

{: .warning }
This page is currently a scaffold for the local forecasting demo. The next step is to wire model output and measured concentration into a reader-facing comparison.

---

## Goal

This page will be used to compare:

- predicted `PM$\_{2.5}$` concentration
- measured `PM$\_{2.5}$` concentration

for a shared set of timestamps and forecast horizons.

## Planned Demo Contents

### Predicted vs Measured Table

A compact table or CSV-backed excerpt showing:

- timestamp
- forecast horizon
- predicted concentration
- measured concentration
- error

### Plot

A simple chart comparing predicted and measured concentration over time for one selected horizon at a time.

### Episode Review

A focused section for visually checking:

- high-PM events
- sudden rises
- overnight accumulation periods
- misses during severe episodes

## Review Questions

This page is meant to answer practical review questions:

1. Does the predicted curve track the measured curve closely enough to be useful?
2. Where does the model systematically underpredict or overpredict?
3. Does the model capture peaks, or does it smooth them away?
4. How does performance differ by forecast horizon?

## Related Pages

- [Statistical Modeling](/docs/research/pm25-forecasting-statistical-modeling.html)
- [Literature Review](/docs/research/pm25-forecasting-literature-review.html)
- [Hanoi Forecasting Experiments](/docs/research/hanoi-pm25-forecasting-experiments-2026.html)

---
layout: default
title: Solar Irradiance Meter
parent: Hardware Notes
grand_parent: Research
nav_order: 4
description: "DIY solar irradiance meter using a mini solar cell and INA219 current sensor — measuring sun power for under $10"
---

# Solar Irradiance Meter

A simple setup to measure solar power density using a mini photovoltaic cell as the sensing element. Total cost: under $10.

---

## How It Works

![Solar meter schematic](/assets/images/hardware/solar_meter_schematic.jpg)
*INA219 current sensor reads voltage (V) and current (I) across a 1-ohm load connected to a mini solar cell.*

The INA219 measures current (mA) and voltage (V) through a fixed load resistor. Solar power density:

```
P (W/m²) = (I × V) / area_of_solar_cell
```

The solar cell converts photon energy into electrical energy. By measuring the electrical output across a known load, we infer the irradiance hitting the cell.

---

## Parts

| Component | Purpose | Cost |
|-----------|---------|------|
| Mini solar cell | Photon-to-electron conversion | ~$2 |
| INA219 breakout | Measures V and I via I2C | ~$3 |
| 1-ohm precision resistor | Fixed load | ~$0.50 |
| ESP8266/Arduino | ADC + data logging | ~$3 |

<div class="image-grid">
  <figure>
    <img src="/assets/images/hardware/solar_cell.jpg" alt="Solar cell">
    <figcaption>Mini solar cell as irradiance sensor</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/hardware/resistor.jpg" alt="Load resistor">
    <figcaption>1-ohm precision resistor as load</figcaption>
  </figure>
</div>

---

## Energy Conversion Chain

From photon hitting the solar cell to usable stored energy, losses occur at every stage:

| Stage | Typical efficiency | Notes |
|-------|-------------------|-------|
| Photon → electron (PV cell) | 20-25% (commercial) | Lab records >40% (NREL). My mini cell likely 15-18% |
| DC → regulated DC (charge controller) | 85-95% | MPPT is optimal; PWM loses more |
| Wiring + connectors | 95-99% | Minimize wire length and joints |
| Battery charging | 90-95% | Internal resistance → heat loss |
| Temperature derating | -0.3%/°C above 25°C | Black cells in direct sun get hot |
| Tilt angle | Varies | Optimal angle ≈ latitude for annual max |

---

## Design Choices

**Why a fixed 1-ohm resistor instead of a real battery?**

The 1-ohm approximates battery internal resistance, giving a repeatable, temperature-stable load. A real battery's internal resistance changes with charge state, age, and temperature — making the measurement harder to interpret.

**Location matters:**

My setup faces west — direct sunlight from noon to afternoon, diffused morning light only. The measurement represents direct normal irradiance (DNI) during afternoon and global horizontal irradiance (GHI) in the morning.

**Calibration:**

Without a reference pyranometer, absolute accuracy is limited. But relative measurements (today vs yesterday, morning vs afternoon, clear vs overcast) are reliable and useful for:
- Solar panel site evaluation
- Cloud cover detection
- Light-driven control triggers (turn on irrigation when >X W/m²)

---

## Data Interpretation

| Reading | Condition | Typical output |
|---------|-----------|---------------|
| 800-1000 W/m² | Direct midday sun, clear sky | Maximum — close to solar constant |
| 200-500 W/m² | Overcast or angled | Diffused radiation only |
| 50-100 W/m² | Heavy cloud or dawn/dusk | Minimal useful power |
| 0 | Night | Baseline noise check |

Hanoi has ~1,500-1,700 sunshine hours/year (lower than tropical average due to winter drizzle). Peak irradiance occurs March-September.

---

*Built as part of a weather station project, September 2020.*

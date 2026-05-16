---
layout: default
title: Temperature
parent: Hardware Notes
grand_parent: Documentation
nav_order: 2
description: "Temperature measurement pitfalls — direct sunlight artifacts, self-heating, sensor types, and practical corrections"
---

# Temperature: Shaded vs Direct Sunlight

Measuring air temperature sounds trivial — until your sensor reads 45°C on a 32°C day because the sun hit the enclosure. These are practical observations from running an outdoor weather station on a west-facing balcony in Hanoi.

---

## The Problem

![Reference temperature from timeanddate.com](/assets/images/hardware/info_temp_2.png)
*Reference: official temperature data shows smooth, symmetrical daily curves centered around solar noon.*

Under clear skies, air temperature rises symmetrically with solar radiation, peaking near noon. Clouds shift and dampen the peak. This is what a properly shaded thermometer produces.

My weather station, however, showed something different:

![Weather station with afternoon spike](/assets/images/hardware/info_temp_1.png)
*My station: needle-shaped spikes at 3-4 PM when direct afternoon sun hits the west-facing sensors.*

The west-facing balcony receives direct sunlight from approximately 3-4 PM. The enclosure heats up, and the sensors record enclosure temperature rather than ambient air temperature.

---

## Proving the Cause

Is it really sunlight? Or sensor drift, or electrical noise?

![Light intensity correlating with temperature spike](/assets/images/hardware/info_temp_3.png)
*Light sensor (LDR) data confirms: peak light intensity directly precedes the temperature spike, with a thermal lag from heating the enclosure.*

The delay between light peak and temperature peak is physical — it takes time to heat the box, and longer to cool it. On cloudy days (Oct 13 in the graph), the spike is absent and the curve is symmetrical.

---

## Self-Heating

Beyond sunlight, sensors themselves generate heat during operation:

| Source | Magnitude | Mitigation |
|--------|-----------|-----------|
| ESP8266 operation | Minimal (deep sleep mode) | Deep sleep between readings |
| Li-ion charging | Detectable by sensors | Separate charging circuit from sensor compartment |
| Sensor excitation current | ~0.1-0.5°C | Duty-cycle readings, don't leave powered continuously |

In the data, a 1.5-hour battery charging event produced a visible temperature bump — the charging heat propagated to nearby sensor probes.

---

## Sensor Types Used

| Sensor | Principle | Accuracy | Self-heating |
|--------|-----------|----------|-------------|
| DS18B20 (x2) | Direct-to-digital (Dallas patent) | ±0.5°C | Minimal |
| DHT22 | Thermistor + ADC | ±0.5°C | Low |
| SHT21 | Silicon bandgap | ±0.3°C | Low |
| BME280 | MEMS | ±0.5°C | Moderate (internal heater for pressure) |

My station averages 4 independent sensors (2x DS18B20, DHT22, SHT21) to reduce individual bias and detect outliers.

---

## Practical Guidelines

1. **Shade the sensors** — a radiation shield or north-facing mount eliminates the biggest error source
2. **Use deep sleep** — minimize self-heating from the MCU
3. **Separate power circuits** — battery charging generates enough heat to bias nearby sensors
4. **Average multiple sensors** — 3-4 independent sensors catch drift and identify outliers
5. **Log light intensity alongside temperature** — makes artifacts identifiable in post-processing
6. **Accept imperfection** — even with these precautions, a balcony station will never match an official shaded instrument shelter

---

*Observations from a west-facing 10th-floor weather station in Hanoi, 2018.*

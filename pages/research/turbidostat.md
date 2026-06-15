---
layout: default
title: Turbidostat Build
parent: "2016"
grand_parent: Research
nav_order: 1
description: "Open-source turbidostat for microalgae cultivation — &#36;200 Arduino-based turbidity monitor and control system, published in Algal Research"
---

# Turbidostat: Open-Source Biomass Density Control for Microalgae

![Turbidostat system overview](/assets/images/turbidostat/turbidostat_1.jpg)

{: .note }
This system was developed at the Biodesign Swette Center for Environmental Biotechnology, Arizona State University. The scientific contribution was published in [Algal Research (2018)](https://doi.org/10.1016/j.algal.2018.03.013). Total hardware cost: ~&#36;200 (excluding the lab-grade peristaltic pump).

---

## What is a Turbidostat?

A turbidostat maintains microalgae culture at a constant density by continuously monitoring turbidity (optical density) and diluting with fresh medium when the culture grows too dense. Think of it as a thermostat, but for biomass concentration instead of temperature.

Commercial turbidostat systems cost &#36;10,000+. This open-source build achieves the same function for ~&#36;200 using a &#36;15 turbidity sensor and an Arduino.

---

## The Problem

Measuring microalgae biomass typically requires a laboratory spectrophotometer — expensive, manual, and limited to one sample at a time. For continuous cultivation experiments (days to weeks), an automated, low-cost system that monitors and controls density in real-time is essential.

The target organism was *Synechocystis* sp. PCC 6803, a sub-micron cyanobacterium that converts light energy and CO$_2$ into biomass. The challenge: finding an affordable sensor that works with these very small cells.

---

## Design

### Concept

![Design concept](/assets/images/turbidostat/turbidostat_2.jpg)
*Core concept: turbidity sensor reads culture density → Arduino compares to setpoint → activates dilution pump when density exceeds threshold.*

### Key Components

| Part | Purpose | Cost |
|------|---------|------|
| TSD-10 turbidity sensor (Amphenol) | Infrared light transmission through culture | ~&#36;15 |
| Arduino Mega | Sensor reading, control logic, pump switching | ~&#36;20 |
| Op-amp breakout | Amplify sensor signal | ~&#36;5 |
| Precision potentiometer (10-turn) | Set target density | ~&#36;5 |
| OLED display (SSD1306) | Real-time readout | ~&#36;5 |
| 2-channel relay board | Switch pumps on/off | ~&#36;5 |
| Peristaltic pump (12V) | Dilution delivery | ~&#36;30 |
| Yun Shield or Raspberry Pi | Timestamp + data logging | ~&#36;35 |
| Three-position switches (x2) | Manual override control | ~&#36;5 |

### Schematic

![Circuit schematic](/assets/images/turbidostat/turbidostat_8.jpg)
*Wiring: turbidity sensor → op-amp → Arduino ADC. Arduino drives relay board controlling pumps. Potentiometer sets density threshold.*

### Control Logic

![Flowchart](/assets/images/turbidostat/turbidostat_6.jpg)
*Execution sequence: wait interval → flush sampling line → read sensor → compare to setpoint → pump on/off → log data.*

---

## Sensor Performance

![Sensor internal structure](/assets/images/turbidostat/turbidostat_1.3.png)
*TSD-10 uses infrared LED emission and a photodetector. Designed for washing machines, but works well for microalgae in the OD 0.1-2.0 range.*

![Calibration: voltage to optical density](/assets/images/turbidostat/turbidostat_11.jpg)
*Conversion of raw voltage readout to optical density (OD$\_{730}$ and NTU). Higher voltage = less light absorbed = lower density.*

![Turbidostat in action](/assets/images/turbidostat/turbidostat_12.jpg)
*Working system: culture density (green) tracks the setpoint (red). Pump status shows dilution events triggered when density exceeds threshold.*

---

## Data Logging

Two options were implemented:

### Option 1: Yun Shield (Linux on Arduino)

The Yun Shield provides WiFi, USB, and SD card storage with a Linux timestamp. Data logged to microSD in CSV format.

![Control box with Yun Shield](/assets/images/turbidostat/turbidostat_9.jpg)
*Version 1.0: Yun Shield + Arduino Mega + op-amp in a project box.*

![Raw data from SD card](/assets/images/turbidostat/turbidostat_19.png)
*CSV data: timestamp, turbidity reading, setpoint, pump status.*

### Option 2: Raspberry Pi

Arduino sends `Serial.print()` data over USB; a Python script on the Pi captures, timestamps, and saves to file.

![RPi logging concept](/assets/images/turbidostat/turbidostat_5.jpg)
*Simplified data path: Arduino → USB serial → Python script → timestamped CSV.*

```c
// Arduino sends this every 60 seconds:
String dataString = "";
averageRead = round((read25+read35+read45+read55)/4);
dataString += String(averageRead) + "," + String(setValue) + "," + String(_pumpON);
Serial.println(dataString);
```

---

## Hardware Photos

<div class="image-grid">
  <figure>
    <img src="/assets/images/turbidostat/turbidostat_4.jpg" alt="Relay box">
    <figcaption>Relay board for pump switching</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/turbidostat/turbidostat_10.jpg" alt="Control box v1">
    <figcaption>Control box (Version 1.0)</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/turbidostat/turbidostat_17.jpg" alt="Sensor installed on reactor">
    <figcaption>Turbidity sensor sampling from reactor</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/turbidostat/turbidostat_13.jpg" alt="Sensor with foil wrap">
    <figcaption>Sensor wrapped in foil to block ambient light</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/turbidostat/turbidostat_16.jpg" alt="Full photobioreactor setup">
    <figcaption>Complete photobioreactor with turbidostat</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/turbidostat/turbidostat_15.jpg" alt="Algae harvest">
    <figcaption>Harvested microalgae from hold-up tank</figcaption>
  </figure>
</div>

---

## Publication

This turbidostat is one of three open-hardware units developed for an advanced photobioreactor system. The scientific contribution — demonstrating that a &#36;200 system can replace &#36;10,000+ commercial alternatives for continuous microalgae cultivation — was published in:

> **Algal Research** (2018)
> DOI: [10.1016/j.algal.2018.03.013](https://doi.org/10.1016/j.algal.2018.03.013)

![Publication screenshot](/assets/images/turbidostat/turbidostat_14.png)

The paper covers:
- Validation of low-cost turbidity sensing against laboratory spectrophotometer
- Long-term continuous cultivation results
- Open hardware design enabling reproducibility
- Cost comparison with commercial systems

---

## Source Code

- **Arduino (Yun Shield):** [Turbidity_logdat_YunShield_2018](https://github.com/binh-bk/advanced-bioreactor/tree/master/Turbidity_logdat_YunShield_2018)
- **Arduino (RPi logging):** [Turbidity_log_python](https://github.com/binh-bk/advanced-bioreactor/blob/master/Turbidity_log_python/Turbidity_log_python.ino)
- **Python data capture:** [serial_logger.py](https://gist.github.com/binh-bk/dd8160d3226a355f00ead3cd73c92898)

---

## Key Takeaways

- A &#36;15 washing-machine turbidity sensor works for microalgae optical density measurement
- Total system cost ~&#36;200 vs &#36;10,000+ for commercial alternatives
- Arduino + relay + peristaltic pump = automated density control
- Two data logging options: embedded Linux (Yun Shield) or Raspberry Pi with Python
- Published validation in peer-reviewed journal confirms scientific utility

---

## Original Reference

First published on Instructables:

- [A Simple Turbidity Monitor and Control System for Microalgae](https://www.instructables.com/A-Simple-Turbidity-Monitor-and-Control-System-for-/)

---

*Developed at Biodesign Swette Center for Environmental Biotechnology, Arizona State University. Published 2018.*

---
layout: default
title: IoT Build Patterns
parent: Hardware Notes
grand_parent: Research
nav_order: 5
description: "Common hardware and software patterns across IoT sensor projects — MCU selection, data transport, power, logging"
---

# IoT Build Patterns

Recurring design patterns from building weather stations, air quality monitors, bioreactors, and motion sensors over 3 years.

---

## Architecture Overview

```
Sensor → MCU → Transport → Storage → Visualization
```

Every project follows this pipeline. The specific choices at each layer depend on power budget, data rate, and whether the device is always-on or battery-operated.

---

## Layer-by-Layer

### Microcontroller

| MCU | WiFi | ADC Pins | Use case |
|-----|------|----------|----------|
| ESP8266 (NodeMCU) | Yes | 1 (10-bit) | WiFi sensor nodes, deep sleep |
| ESP32 | Yes + BLE | 18 (12-bit) | Multi-sensor, Bluetooth |
| Arduino Mega | No | 16 (10-bit) | Many analog sensors, lab equipment |
| Arduino Nano | No | 8 (10-bit) | Compact, dedicated controller |

**When to use which:**
- Need WiFi + battery → ESP8266 with deep sleep
- Need many analog inputs → Arduino Mega
- Need both → ESP32
- Need Linux + GPIO → Raspberry Pi (not really an MCU, but fills the gap)

### Data Transport

| Method | Latency | Power | Complexity |
|--------|---------|-------|-----------|
| MQTT → home server | Real-time | WiFi always on | Moderate (broker setup) |
| USB serial → RPi | Real-time | Wired power | Low |
| SD card logging | None (offline) | Minimal | Lowest |
| HTTP POST → cloud | Near real-time | WiFi burst | API key management |

**MQTT** is the workhorse for always-on sensors. Publish readings to topics; subscribe from dashboards or logging scripts. Mosquitto broker runs on any Linux box.

**USB serial → Python script** is simplest for lab setups. Arduino prints CSV; Python timestamps and saves. No WiFi, no protocol overhead.

### Power

| Strategy | Battery life | Use case |
|----------|-------------|----------|
| USB powered (always on) | N/A | Indoor, lab, home server |
| 18650 Li-ion + deep sleep | 2-6 months | Outdoor weather station |
| 4S LiPo pack | 3-7 days | Mobile sampling kit |
| Solar + battery | Indefinite | Remote, unattended |

**Deep sleep pattern (ESP8266):**
1. Wake → connect WiFi (~2-3s)
2. Read sensors (~100ms)
3. Publish via MQTT (~500ms)
4. Deep sleep for 5-15 minutes
5. Total active time: ~4 seconds per cycle

### Logging & Storage

| Approach | Pros | Cons |
|----------|------|------|
| Python on RPi → CSV/TXT | Simple, timestamp from Linux clock | Need RPi running |
| Yun Shield → SD card | Self-contained with Arduino | Limited storage, no remote access |
| InfluxDB on home server | Time-series optimized, Grafana-ready | Server setup overhead |
| Google Sheets API | Free, remote access | Rate limits, API complexity |

### Visualization

| Tool | Type | Use case |
|------|------|----------|
| Matplotlib | Offline plots | Analysis, publications |
| Highcharts | Web dashboard | Live display on b-io.info |
| Grafana | Time-series dashboard | Home server monitoring |
| Serial plotter (Arduino IDE) | Real-time debug | Development only |

---

## Sensor Integration Patterns

### Averaging Multiple Sensors

Run 2-4 sensors measuring the same parameter. Discard outliers, average the rest. Catches drift and identifies failures without manual inspection.

```python
readings = [sensor1.read(), sensor2.read(), sensor3.read(), sensor4.read()]
filtered = [r for r in readings if abs(r - median(readings)) < threshold]
value = mean(filtered)
```

### Anomaly Filtering

Single-peak spikes (>300 $\mu g/m^3$ for PM, or >50°C for temperature) are usually electrical noise, not real. Remove iteratively:

1. Calculate rolling median
2. Flag points > 3x deviation from median
3. Repeat 5-10 rounds (early rounds remove extreme outliers, enabling better median estimation)

### Cross-Check Periods

Before measuring, expose all sensors to the same condition (both PM sensors in ambient air, no filter). Confirms inter-sensor agreement. If the cross-check shows >5% difference, investigate before trusting filtered readings.

---

## Enclosure Patterns

| Type | Cost | Weather-proof | Thermal |
|------|------|--------------|---------|
| PVC pipe segments | &#36;2-5 | Good (sealed) | Moderate |
| 3D-printed | &#36;5-15 | Fair (needs sealing) | Poor (PLA warps) |
| Project box (ABS) | &#36;5-10 | Good | Fair |
| Aluminum foil wrap | &#36;0 | No | Excellent light shielding |

**For PM sensors:** air intake via tube or open bottom; avoid direct rain entry. PVC pipe with downward-facing opening works well.

**For temperature:** radiation shield essential. North-facing or fully shaded. Never place in direct sun unless measuring solar effects intentionally.

---

## Lessons Learned

1. **WiFi reconnection is the #1 failure mode** — implement retry with backoff, and log locally as fallback
2. **Duplicate sensors are cheap insurance** — a &#36;3 extra DHT22 saves hours of debugging drift
3. **Time synchronization matters** — NTP on boot for WiFi devices; RTC module for offline loggers
4. **Label everything** — sensor IDs, cable colors, pin assignments. Future-you will not remember
5. **Power first, features second** — a dead battery means zero data, regardless of how many sensors you have

---

*Patterns from 7+ IoT projects built in Hanoi, 2017-2020. See [Instructables profile](https://www.instructables.com/member/binova/instructables/) for step-by-step build guides.*

---
layout: default
title: Humidity
parent: Hardware Notes
grand_parent: Research
nav_order: 3
description: "Relative humidity explained — dew point, heat index, capacitive sensor selection, and accuracy limits in tropical climate"
---

# Humidity: What It Means and How to Measure It

---

## Concepts

### Relative Humidity (RH)

The ratio of current water vapor mass to the saturation capacity at that temperature. Expressed as a percentage.

![Vapor holding capacity vs temperature](/assets/images/hardware/relative_humidity.png)
*Warmer air holds more water. Same absolute moisture → lower RH at higher temperature.*

**Key insight:** RH is calculated relative to temperature. When temperature rises and absolute vapor stays constant, RH drops because the air *could* hold more. This is why temperature and RH curves mirror each other:

![Temperature and RH inverse relationship](/assets/images/hardware/info_humid_2.png)
*My weather station: temperature up → RH down, and vice versa. Not coincidence — it's the definition.*

### Dew Point

The temperature at which air becomes saturated (RH reaches 100%) and condensation begins.

| Air condition | Dew point |
|--------------|-----------|
| 30°C, 70% RH | ~24°C |
| 30°C, 20% RH | ~4°C |

### Heat Index

Perceived temperature combining air temperature and humidity:

| Temperature | RH | Feels like |
|-------------|-----|-----------|
| 24°C | 0% | 21°C |
| 24°C | 50% | 24°C |
| 24°C | 100% | 27°C |
| 35°C | 70% | 46°C |

**Why it matters:** High humidity blocks sweat evaporation — the body's primary cooling mechanism. In Hanoi summers (35°C, 80% RH), heat stress is a real risk.

Conversely, very dry air causes cracked skin, nosebleeds, and respiratory irritation by drawing moisture from exposed tissue.

---

## Sensor Selection

![Humidity sensor comparison chart](/assets/images/hardware/many_sensors.jpg)
*Capacitive sensor comparison by Robert Kandrsmith. Accurate range: ±3% within 10-80% RH. Above 80%, accuracy degrades significantly.*

### Sensors Tested

| Sensor | Type | Interface | Accuracy | Price |
|--------|------|-----------|----------|-------|
| SHT3x (Sensirion) | Capacitive | I2C | ±2% RH, ±0.2°C | ~&#36;5 |
| BME280 (Bosch) | Capacitive | I2C/SPI | ±3% RH | ~&#36;4 |
| HDC1080 (TI) | Capacitive | I2C | ±2% RH | ~&#36;4 |
| Si7021 | Capacitive | I2C (0x40) | ±3% RH | ~&#36;3 |
| DHT22 / AM2302 | Resistive | One-wire | ±2-5% RH | ~&#36;3 |

### Measurement Principles

- **Capacitive:** polymer film absorbs water vapor, changing dielectric constant → capacitance change. Most modern sensors use this.
- **Resistive:** ceramic substrate changes resistance with moisture absorption. Older technology, less accurate.
- **Gravimetric:** (reference only) weigh absorbed water directly.

---

## Practical Notes from Hanoi

**Problem:** Hanoi regularly hits 80-90% RH. Most sensors are specified for ±3% accuracy in the 10-80% range. Above 80%, readings drift unpredictably.

**I2C address conflicts:** Si7021 and HTU21D both use 0x40 with no option to change. Cannot use both on the same bus. Discovered this after ordering both — always check the address table first.

**Duplicate sensors help:** Running Si7021 + DHT22 on the same station reveals when one drifts. Average them for a better estimate.

**Power supply matters:** MCP1700 LDO provides clean 3.3V. Noisy supply → noisy readings, especially for the ADC-based DHT22.

**Condensation kills readings:** At 100% RH (dew point = air temp), condensation forms on the sensor element. Some sensors have built-in heaters to prevent this. The BME280's internal heater is meant for this purpose.

---

## Application: When Does Humidity Matter?

| Context | Why RH matters |
|---------|---------------|
| Air quality (PM sensors) | High RH inflates light-scattering readings — particles appear larger |
| Weather station | Core measurement for comfort index, dew point alerting |
| Electronics enclosure | Condensation at >95% RH can short circuits |
| Gravimetric analysis | Must account for water content in weighed samples |
| Agriculture | Crop disease risk correlates with leaf wetness (high RH + temperature) |

---

*Notes from operating weather stations in Hanoi, 2018-2019.*

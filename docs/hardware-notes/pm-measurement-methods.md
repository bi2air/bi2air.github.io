---
layout: default
title: PM Measurement Methods
parent: Hardware Notes
grand_parent: Research
nav_order: 1
description: "Particulate matter measurement methods — from gravimetric reference to low-cost laser scattering sensors"
---

# PM Measurement Methods

![Particle size chart by source](/assets/images/hardware/sizes.png)
*EPA Report Fig. 2.4: Particle size ranges by origin. Construction dust → PM100, combustion soot → PM$_{2.5}$, secondary aerosols → ultrafine.*

---

## Sources of Particulate Matter

| Source | Mechanism | Resulting PM |
|--------|-----------|-------------|
| Construction sites | Wind sweeps fine sand/dust | PM$_{10}$-PM100 |
| Diesel engines | Carbon soot (incomplete combustion) | PM$_{2.5}$, ultrafine |
| Gasoline engines | Secondary Organic Aerosol (SOA) | PM$_{2.5}$ (5x more than primary) |
| Coal combustion | SO2 → sulfate conversion | PM$_{2.5}$ |
| Agricultural burning | Direct emission | PM$_{2.5}$ |
| Fertilizer volatilization | NH3 + NOx → ammonium nitrate | PM$_{2.5}$ |

---

## Measurement Techniques

### 1. Gravimetric (Reference Method)

Weigh a filter before and after drawing ambient air through it for a fixed period. The gold standard — all other methods are validated against this.

### 2. Beta Attenuation Monitor (BAM)

Measures the loss of beta particles (electrons from 14C source) passing through a loaded filter vs a blank. Used by the US Embassy in Hanoi (MetOne BAM-1020). Federal Equivalent Method (FEM) certified for continuous hourly monitoring.

### 3. Tapered Oscillating Element Microbalance (TEOM)

Particles collected on a filter change the oscillation frequency of a tapered element. Frequency shift → mass calculation. Continuous measurement.

### 4. Piezoelectric Microbalance

Quartz crystal resonance frequency changes with deposited mass. Compare loaded crystal vs control crystal.

### 5. Pressure Drop Sampler

Dust on a filter increases headloss. Measure pressure differential over time.

### 6. Light Scattering (Nephelometer)

Illuminates particles with a light beam; measures scattered light intensity in all directions. Basis for many ambient monitoring networks.

### 7. Optical Particle Counter

Counts and sizes individual particles by the light pulse each produces. This is how low-cost sensors (PMS7003, SDS011) work — a laser illuminates particles in a chamber, and a photodetector counts scattered pulses.

### 8. Condensation Nuclei Counter

For ultrafine particles too small for optical detection: grow them by condensation (alcohol vapor), then count by scattering.

### 9. Aerodynamic Particle Sizer

Combines light scattering with time-of-flight measurement to determine both particle count and aerodynamic diameter.

### 10. LIDAR (Light Detection and Ranging)

Pulsed laser sent upward; backscattered light measured by a co-located receiver. Provides vertical column profile of aerosol loading.

---

## Effect of Humidity on Light Scattering

![RH effect on scattering coefficient](/assets/images/hardware/RH_light_scattering.png)
*EPA Report Fig. 4.8: High relative humidity inflates light-scattering readings. This is why low-cost sensors overestimate PM in humid conditions (Hanoi: 80-90% RH typical).*

Water vapor condenses on particle surfaces, increasing their apparent size and scattering cross-section. Sensors without a heated inlet or RH correction systematically overread in tropical climates.

---

## Regulatory Standards

### Vietnam

- **QCVN 05:2013/BTNMT** — National Technical Regulation on Ambient Air Quality
- Sampling methods: TCVN 5067:1995 (gravimetric), TCVN 9469:2012 (BAM)
- Vietnam updated AQI calculation to breakpoint method in Nov 2019 (Decision 1459/QD-TCMT)

### United States

- **CFR § 50.7** — defines reference and equivalent methods for PM$_{2.5}$
- **FRM** (Federal Reference Method) — gravimetric, 24-hour integrated
- **FEM** (Federal Equivalent Method) — BAM, TEOM for continuous monitoring
- Method 201A: determination of PM$_{10}$/PM$_{2.5}$ from stationary sources

---

## Monitoring Equipment in Hanoi

![PM monitoring devices overview](/assets/images/hardware/pm-device.jpg)
*Range of instruments: research-grade stationary monitors to $13 laser-scattering sensors.*

| Station | Equipment | Method | Data |
|---------|-----------|--------|------|
| Chi Cuc (VN MONRE) | Environment SA MP101M | Regulatory multi-pollutant | Limited public access |
| US Embassy | MetOne BAM-1020 | FEM, hourly PM$_{2.5}$ | Public via AirNow |
| SPARC Lab (HUST) | Various low-cost | Research collocation | Academic |
| My projects | PMS7003, SDS011 | Laser scattering | [See study](/docs/research/pm25-low-cost-sensors.html) |

### Low-Cost Sensors

| Sensor | Price | Output | Lifespan | Notes |
|--------|-------|--------|----------|-------|
| PMS7003 (Plantower) | ~$13 | PM1/2.5/10 + 6 size bins | 8,000h | Best value, small, rich data |
| SDS011 (Nova Fitness) | ~$19 | PM$_{2.5}$, PM$_{10}$ (float) | 8,000h | Remote air intake via hose |
| HPMA115S0 (Honeywell) | ~$19 | PM$_{2.5}$, PM$_{10}$ (int) | 20,000h | Best documentation |
| Dylos DC1100 Pro | ~$290 | Particle count (2 bins) | Years | Reference for hobbyists |

---

*Notes from building air quality monitoring systems, 2018-2019.*

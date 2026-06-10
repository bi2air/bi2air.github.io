---
layout: default
title: PM$\_{2.5}$ Sensor Collocation Campaign
parent: "2022"
grand_parent: Research
nav_order: 1
description: "Draft reconstruction of a long-running PM$\_{2.5}$ co-location campaign in Hanoi using an mlab unit, nearby anchor monitors, and BAM-linked comparison fits"
---

# PM$\_{2.5}$ Sensor Collocation Campaign Draft

{: .warning }
This page is a **draft reconstruction** for local review in Jekyll. The overall campaign structure is now much clearer, but some file-to-sensor assignments are still being verified.

{: .note }
This page reconstructs an **archived long-running field campaign** in Hanoi, Vietnam. The original `dynamic-correlate` framing is no longer appropriate because the live service is gone. What still matters is the study design: an **`mlab` co-location unit** operating several low-cost PM sensors, with **nearby anchor devices** such as `Dylos DC1100 Pro`, `Dylos DC1700`, and `IQAir AirVisual Node Pro`, plus an attempt to tie the field comparisons back to earlier **BAM-referenced calibration work**.

---

## Working campaign model

Based on the recovered CSV exports and archived notes, the campaign now appears to have had three layers:

1. A dedicated **`mlab` co-location unit** that housed the main low-cost PM sensor setup.
2. Several **larger nearby monitors** sitting outside but close to that unit, including `Dylos DC1100 Pro`, `Dylos DC1700`, and `IQAir AirVisual Pro/Node`.
3. Additional **device-specific logging streams** and side experiments that were related to the broader measurement effort but not always part of the same physical enclosure.

That distinction matters. One CSV file in the recovered database is often best interpreted as a **sensor/setup/script stream**, not simply a single instrument.

---

## What this campaign was trying to do

Most low-cost PM$\_{2.5}$ writeups appear months after the field work ends. That lag weakens the connection between the measurement campaign and what readers can actually inspect. The original `dynamic-correlate` post tried to shorten that gap by publishing rolling comparison plots while the experiment was still active.

That framing is no longer appropriate because the live charts are gone. The more durable story is this:

- A set of **low-cost optical PM sensors** were run side by side in ambient Hanoi air within the **`mlab` co-location unit**.
- A **Dylos DC1100 Pro** was used as a more established **mid-tier anchor device** for day-to-day comparison.
- The campaign also leaned on a separate earlier study that compared **PMS7003** and **SDS011** against a **MetOne BAM-1020** reference station.
- The practical question was not whether a cheap sensor could become a BAM, but whether a cheap sensor could **track real variation consistently enough** to be useful after local adjustment.

The preserved figures from this phase focus on three direct pairings:

- **Dylos DC1100 Pro vs Honeywell HPMA115S0**
- **Dylos DC1100 Pro vs Plantower PMS7003**
- **Dylos DC1100 Pro vs Nova Fitness SDS011**

The broader campaign notes also mention adjacent observations with **Dylos DC1700** and **IQAir AirVisual Node Pro**, but the archived static figures that survive for this post are centered on the **DC1100 Pro**.

---

## Recovered data streams

The current reconstruction groups the recovered CSV exports as follows.

### Core co-location unit

- `mlab_p1.csv`
- `mlab_p2.csv`
- `mlab_p3.csv`
- `mlab_pms5003.csv`

These appear to be the strongest candidates for the **main co-location box / platform logs**.

### Nearby anchor devices

- `dylos.csv`
- `dc1700.csv`
- `airvisual.csv`

These are interpreted as **larger nearby monitors** that sat outside but close to the co-location unit.

### Device-specific streams related to the broader campaign

- `honeywell.csv`
- `hpma_01.csv`, `hpma_02.csv`, `hpma_03.csv`
- `sds011_08db.csv`, `sds011_75ee.csv`, `sds011_a307.csv`, `sds011_a30b.csv`, `sds011_a327.csv`
- `zh03b_001.csv`, `zh03b_01.csv`, `zh03b_02.csv`, `zh03b_03.csv`

These are likely **sensor-specific logs** produced by the same broader measurement effort, but not necessarily all inside the same enclosure at the same time.

### Separate experiments or context streams

- `mask_exp.csv`, `mask_one.csv` — mask filtration experiment
- `hepa_filter.csv` — indoor HEPA experiment
- `mh_z19.csv`, `mh_z19_two.csv` — CO$_2$ monitoring
- `solcast_actual.csv`, `solcast_forecast.csv` — solar/energy context
- `dust_work.csv` — unresolved and needs additional inspection

This classification is provisional, but it is already strong enough to prevent the co-location post from mixing unrelated experiments into the main narrative.

---

## Recovered Data Summary

Before rebuilding any correlation plots, it helps to keep one explicit manifest of what survives in the archive. The table below summarizes the current working interpretation of each CSV export.

| File | Working sensor/setup name | Type | Start | End | Rows |
| --- | --- | --- | --- | --- | ---: |
| `mlab_p1.csv` | Mobile lab channel P1 | Co-location unit / low-cost PM stream | 2019-01-27 19:11:38 | 2022-05-25 01:35:40 | 1050761 |
| `mlab_p2.csv` | Mobile lab channel P2 | Co-location unit / low-cost PM stream | 2019-01-27 19:34:10 | 2019-07-06 17:20:24 | 228699 |
| `mlab_p3.csv` | Mobile lab channel P3 | Co-location unit / low-cost PM stream | 2019-01-27 22:01:17 | 2022-05-07 00:50:54 | 986695 |
| `mlab_pms5003.csv` | Mobile lab PMS5003 | Plantower PMS5003 / PM sensor stream | 2019-04-11 09:59:15 | 2022-05-25 01:35:17 | 967241 |
| `dylos.csv` | Dylos DC1100 Pro | Mid-tier particle counter anchor | 2019-05-28 17:02:57 | 2022-07-31 07:30:18 | 1536806 |
| `dc1700.csv` | Dylos DC1700 | Mid-tier particle counter anchor | 2019-08-10 10:32:49 | 2022-07-31 07:30:13 | 1454874 |
| `airvisual.csv` | IQAir AirVisual Node/Pro | Consumer finished monitor anchor | 2019-08-25 11:36:53 | 2022-08-28 07:41:47 | 137419 |
| `honeywell.csv` | Honeywell HPMA115S0 | Low-cost PM sensor stream | 2019-06-05 15:36:24 | 2020-03-17 14:28:42 | 381142 |
| `hpma_01.csv` | Honeywell HPMA #01 | Low-cost PM sensor stream | 2020-03-18 11:37:21 | 2020-08-03 16:07:04 | 131296 |
| `hpma_02.csv` | Honeywell HPMA #02 | Low-cost PM sensor stream | 2020-03-18 11:37:24 | 2020-08-17 10:01:33 | 131639 |
| `hpma_03.csv` | Honeywell HPMA #03 | Low-cost PM sensor stream | 2020-03-18 11:37:28 | 2020-05-10 12:11:13 | 47823 |
| `sds011_a327.csv` | Nova SDS011 a327 | Low-cost PM sensor stream | 2020-03-01 22:34:55 | 2021-05-20 14:47:21 | 189020 |
| `sds011_a30b.csv` | Nova SDS011 a30b | Low-cost PM sensor stream | 2020-03-01 22:57:02 | 2020-12-22 16:08:01 | 111240 |
| `sds011_a307.csv` | Nova SDS011 a307 | Low-cost PM sensor stream | 2020-03-01 22:59:27 | 2021-05-20 14:47:49 | 164578 |
| `sds011_08db.csv` | Nova SDS011 08db | Low-cost PM sensor stream | 2020-03-17 17:22:44 | 2021-05-20 14:49:40 | 199826 |
| `sds011_75ee.csv` | Nova SDS011 75ee | Low-cost PM sensor stream | 2020-03-17 17:22:48 | 2020-11-08 22:05:14 | 119578 |
| `zh03b_001.csv` | Winsen ZH03B 001 | Low-cost PM sensor stream | 2020-03-17 20:31:15 | 2020-03-17 22:46:23 | 98 |
| `zh03b_01.csv` | Winsen ZH03B 01 | Low-cost PM sensor stream | 2020-03-17 22:51:54 | 2021-05-20 11:17:27 | 216791 |
| `zh03b_02.csv` | Winsen ZH03B 02 | Low-cost PM sensor stream | 2020-03-17 22:56:49 | 2021-05-20 11:19:08 | 217725 |
| `zh03b_03.csv` | Winsen ZH03B 03 | Low-cost PM sensor stream | 2020-03-17 22:56:53 | 2021-05-20 11:19:25 | 216040 |
| `mask_exp.csv` | Mask experiment summary | Separate mask study | 2019-04-11 19:50:00 | 2019-10-11 02:50:00 | 23152 |
| `mask_one.csv` | Mask apparatus sensor log | Separate mask study | 2019-04-11 13:58:13 | 2021-04-16 09:09:54 | 258017 |
| `hepa_filter.csv` | HEPA filter indoor log | Separate indoor filter study | 2019-05-27 16:37:29 | 2020-04-02 15:40:44 | 42553 |
| `mh_z19.csv` | MH-Z19 CO$_2$ logger | CO$_2$ context stream | 2019-06-05 15:33:14 | 2022-07-24 07:11:56 | 915014 |
| `mh_z19_two.csv` | MH-Z19 CO$_2$ logger #2 | CO$_2$ context stream | 2019-07-08 08:06:13 | 2020-04-25 02:49:56 | 299829 |
| `solcast_actual.csv` | Solcast actual | Solar/energy context stream | 2021-04-08 23:30:00 | 2021-06-16 09:30:00 | 5501 |
| `solcast_forecast.csv` | Solcast forecast | Solar/energy context stream | 2021-04-15 23:30:00 | 2021-06-23 10:00:00 | 102144 |
| `dust_work.csv` | Dust work log | Unresolved PM/environment stream | 1970-01-01 08:01:00 | 2022-09-03 20:56:28 | 927916 |
| `nova_sds011.csv` | Nova SDS011 legacy | Earlier PM sensor stream | 2018-11-07 09:15:37 | 2020-03-17 14:37:47 | 131898 |
| `nova_sds011_two.csv` | Nova SDS011 legacy #2 | Earlier PM sensor stream | 2019-04-26 11:50:07 | 2020-03-17 14:36:04 | 143690 |
| `nova_sds018.csv` | Nova SDS018 legacy | Earlier PM sensor stream | 2019-04-06 10:22:57 | 2019-06-04 18:04:13 | 24777 |
| `mlab_onboard.csv` | Mobile lab onboard | Empty export / unresolved | n/a | n/a | 0 |

Two caution flags are already visible in this manifest:

- `dust_work.csv` has a clearly bad earliest timestamp and should be filtered before being used in campaign-level analysis.
- `mlab_onboard.csv` is currently an empty export rather than a usable sensor stream.

---

## Mid-Tier Sensor Time Coverage and Correlation

As a first reconstruction target, I aligned the three surviving mid-tier monitors:

- `Dylos DC1100 Pro` from `dylos.csv`
- `Dylos DC1700` from `dc1700.csv`
- `IQAir AirVisual` from `airvisual.csv`

### Shared coverage

Using `15-minute` bins, the common three-way overlap window is:

- `2019-08-25 11:30:00` to `2022-07-31 03:00:00`
- `89,055` aligned bins

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/mid_tier_coverage.svg" alt="Time coverage of DC1100, DC1700, and AirVisual sensor streams">
    <figcaption>Shared time coverage of the three mid-tier streams recovered from the archive.</figcaption>
  </figure>
</div>

### Exploratory correlation approach

The three devices do not expose identical fields, so this first-pass comparison uses a pragmatic alignment:

- DC1100: fitted PM$\_{2.5}$-like field already present in `dylos.csv` as `pm2_5_f`
- DC1700: exploratory PM$\_{2.5}$ proxy using the same simple Dylos-family heuristic, `(small - large) / 100`
- `AirVisual`: direct `pm25` field from the device export

This is good enough for a first behavioral comparison, but it should still be treated as **exploratory**, especially on the `DC1700` side where we are deriving a proxy rather than reading a native PM$\_{2.5}$ field.

### Pairwise correlation

| Pair | Pearson r |
| --- | ---: |
| `DC1100 fit` vs `DC1700 proxy` | 0.9313 |
| DC1100 fit vs AirVisual PM$\_{2.5}$ | 0.8457 |
| DC1700 proxy vs AirVisual PM$\_{2.5}$ | 0.8897 |

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/mid_tier_correlation.svg" alt="Pairwise exploratory correlation plots for DC1100, DC1700, and AirVisual">
    <figcaption>Pairwise exploratory correlation for the three mid-tier devices using aligned 15-minute bins.</figcaption>
  </figure>
</div>

The immediate takeaway is that the three mid-tier devices appear to move together strongly over the shared long-term window, even before any deeper calibration or event-level filtering.

### Day-Level QC Trimming

A practical cleaning rule for these three long-running devices is to evaluate **day-level agreement** rather than trying to infer every maintenance event by memory alone. I implemented that idea as follows:

- first resample the three streams to **1-hour bins**
- compute daily pairwise correlations for days with at least `18` hourly bins
- estimate each pair's **typical lower bound** as the **5th percentile** of its historical daily-correlation distribution
- flag a day when **at least 2 of the 3 pairwise daily correlations** fall below their own 5th-percentile thresholds

The resulting thresholds were:

- `DC1100 vs DC1700`: `0.7047`
- `DC1100 vs AirVisual`: `0.2990`
- `DC1700 vs AirVisual`: `0.5727`

This flagged `44` low-agreement days. Removing those days trimmed the aligned `15-minute` dataset from `89,055` bins to `84,848` bins.

| Pair | Raw r | Cleaned r |
| --- | ---: | ---: |
| `DC1100 fit` vs `DC1700 proxy` | 0.9313 | 0.9337 |
| DC1100 fit vs AirVisual PM$\_{2.5}$ | 0.8457 | 0.8501 |
| DC1700 proxy vs AirVisual PM$\_{2.5}$ | 0.8897 | 0.8919 |

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/mid_tier_daily_qc.svg" alt="Daily QC correlation grid for DC1100, DC1700, and AirVisual">
    <figcaption>Daily QC grid. Red-outlined rows are days where at least two pairwise daily correlations fell below their bottom-5% historical thresholds.</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mid_tier_correlation_cleaned.svg" alt="Cleaned pairwise correlation plots for DC1100, DC1700, and AirVisual after day-level trimming">
    <figcaption>Pairwise correlation after dropping flagged low-agreement days.</figcaption>
  </figure>
</div>

This trim does **not** radically change the headline results, which is useful in itself: the three-device relationship is fairly robust overall. But it does give a cleaner baseline before any more detailed event-level or calibration-style analysis.

### Hour-of-Day Stability and Clean Data Format

To avoid over-trimming, I treated **hour-of-day stability** as a diagnostic rather than an automatic exclusion rule. For each hour `00:00` through `23:00`, I pooled the full campaign and recomputed the three pairwise correlations.

The result is reassuring: **no hour-of-day bucket fell below `r = 0.2`** for any pair. In other words, there is no evidence here for a permanently bad nightly or daytime operating window that should be dropped wholesale.

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/mid_tier_hourly_stability.svg" alt="Hour-of-day stability grid for DC1100, DC1700, and AirVisual">
    <figcaption>Hour-of-day stability across the full campaign. Under the `r < 0.2` rule, no hour block is globally abnormal.</figcaption>
  </figure>
</div>

That leads to a cleaner final data contract before deeper analysis:

- `mid_tier_15min_with_qc.csv`: full aligned `15-minute` dataset with QC labels retained
- `mid_tier_15min_analysis_clean.csv`: analysis-ready subset after dropping only `day_flagged` periods
- `mid_tier_daily_qc.csv`: day-level diagnostic table used for trimming
- `mid_tier_hour_of_day.csv`: hour-of-day stability table

This keeps the workflow honest:

- **drop** only days that look operationally abnormal by the multi-pair daily QC rule
- **label as suspect** any rows attached to a day with `min daily r < 0.2`
- **do not drop** hours of day wholesale unless a real hour-level failure pattern emerges later

### What the deeper diagnostics show

The global correlation hides several important behaviors that are more useful than the single `r` values alone.

#### 1. No meaningful lag at 15-minute resolution

Scanning lags from `-120` to `+120` minutes showed that all three pairs peak at **0-minute lag**. In other words, at the campaign time scale used here, none of the three mid-tier devices appears to be consistently delayed relative to the others.

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/mid_tier_lag.svg" alt="Lag scan for DC1100, DC1700, and AirVisual pairings">
    <figcaption>Lag scan across `15-minute` bins. All three pairings peak at zero lag within the tested `±120 minute` window.</figcaption>
  </figure>
</div>

#### 2. Agreement is not equally stable month to month

Monthly correlation is mostly strong, but not uniform. A few examples stand out:

- `2019-08` starts very strong: `DC1100` vs `AirVisual` reaches `0.9368`
- `2021-04` is also very strong, with `DC1100` vs `AirVisual` at `0.9257`
- `2021-09` weakens noticeably: `DC1100` vs `AirVisual` drops to `0.6786`
- `2022-06` and `2022-07` degrade sharply for `DC1100` against the others, suggesting a late-period drift, setup change, or data-quality issue rather than a stable three-device relationship
- `2022-02` should not be overread because only `20` aligned bins survived that month

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/mid_tier_monthly_heatmap.svg" alt="Monthly correlation stability heatmap for DC1100, DC1700, and AirVisual">
    <figcaption>Monthly correlation stability for the three mid-tier devices. Most months are strong, but the late 2022 period deserves separate inspection.</figcaption>
  </figure>
</div>

#### 3. Agreement is stronger in dirty-air periods than in cleaner air

Splitting the aligned data by AirVisual PM$\_{2.5}$ tertiles shows a clear pattern:

- **Low regime** `0.0` to `23.0`: `DC1100` vs `AirVisual` is `0.5294`
- **Mid regime** `23.5` to `51.0`: `DC1100` vs `AirVisual` is `0.4610`
- **High regime** `51.05` to `564.2`: `DC1100` vs `AirVisual` rises to `0.6722`

The same pattern holds for `DC1700` and `AirVisual`, where agreement improves from `0.5245` in the low regime to `0.7910` in the high regime. That is typical of PM sensors: they often agree more clearly when pollution events dominate the signal and less clearly near cleaner-background conditions.

#### 4. `DC1100` and `DC1700` are the tightest pair

Across the full aligned dataset, the strongest relationship remains `DC1100` versus `DC1700` at `0.9313`, and that relationship stays high across most months and concentration regimes. That supports the idea that the two Dylos-family devices are behaving as a coherent pair, even if one still needs a better PM conversion model.

### What to do with this

For the three mid-tier devices, the next truly useful products are not more global scatter plots. They are:

- a **late-period quality check** focused on `2022-05` to `2022-07`
- an **event-based comparison** using high-PM episodes only
- a **better DC1700 conversion** than the simple `(small - large) / 100` proxy

That would move the analysis from “these sensors correlate” to “when and why they agree or diverge.”

---

## Available overlap windows

The archived watermarked plots were probably **cumulative correlation views up to the stamped date**, not the full extent of the surviving dataset. The recovered CSV archive suggests that a much broader correlation range should be possible.

### Long overlap windows already visible in metadata

- `mlab_p1.csv`, `mlab_p3.csv`, and `mlab_pms5003.csv` overlap with `dylos.csv` from **2019-05-28 to 2022-05-25**.
- Those same `mlab_*` streams overlap with `dc1700.csv` from **2019-08-10 to 2022-05-25**.
- They overlap with `airvisual.csv` from **2019-08-25 to 2022-05-25**.
- A dense multi-sensor block exists from **2020-03-17 to 2021-05-20**, where `mlab_*`, multiple `SDS011` streams, multiple `ZH03B` streams, and nearby anchor devices are all present.

That means the August 2019 archived figures are probably only one visible slice of a larger campaign rather than the natural limit of the data.

### Why this matters

For reconstruction, it is reasonable to treat the surviving images as **campaign snapshots**, while the CSV archive should make it possible to build:

- longer correlation windows for `mlab` versus `dylos`
- longer correlation windows for `mlab` versus `dc1700`
- longer correlation windows for `mlab` versus `airvisual`
- multi-sensor overlap studies during the March 2020 to May 2021 deployment block

---

## Likely parallel streams, not simple duplicates

Some file groups have names that differ only by a few hexadecimal-like digits, especially the `SDS011` and `ZH03B` files. At first glance they could be mistaken for duplicate exports. The recovered timing and value patterns suggest something else: they are more likely **parallel devices of the same sensor family**.

### SDS011 observations

- `sds011_a327.csv`, `sds011_a30b.csv`, and `sds011_a307.csv` all begin on **2020-03-01**, but not at the exact same time.
- `sds011_08db.csv` and `sds011_75ee.csv` begin on **2020-03-17**, again only a few seconds apart.
- The `a3xx` files have roughly **63-64 second cadence** in the sampled rows.
- The `08db` and `75ee` files have roughly **143-145 second cadence** in the sampled rows.
- When paired within tight time windows, the readings are **similar but not identical**, which argues against them being duplicate dumps of one sensor stream.

In other words, the differing suffixes are best read as **device identifiers or logger-specific stream names**, not just accidental copies.

### ZH03B observations

- `zh03b_01.csv`, `zh03b_02.csv`, and `zh03b_03.csv` run in nearly the same overall window.
- `zh03b_02.csv` and `zh03b_03.csv` often start within seconds of each other and can match on some rows, but they also diverge often enough to look like separate sensors exposed to the same air rather than the same file saved twice.

This is useful because it supports a richer reconstruction: the archive may preserve not just one representative low-cost PM sensor per family, but several **same-model devices running in parallel**.

---

## Mobile Lab Photo Review

`mlab` here stands for **mobile lab**. I found a set of recovered apparatus and deployment photos, but I have not yet pinned which ones are the best canonical images for the page. To keep the review concrete, the full candidate set is exposed below in the local Jekyll build.

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_01.jpg" alt="Recovered mlab photo 01">
    <figcaption>`mlab_01.jpg` from `54230731_10211334662121835_928482035729694720_n.jpg`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_02.jpg" alt="Recovered mlab photo 02">
    <figcaption>`mlab_02.jpg` from `55916103_10211419375359613_5193094491451424768_n.jpg`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_03.jpg" alt="Recovered mlab photo 03">
    <figcaption>`mlab_03.jpg` from `IMG_2780.HEIC`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_04.jpg" alt="Recovered mlab photo 04">
    <figcaption>`mlab_04.jpg` from `IMG_2803.HEIC`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_05.jpg" alt="Recovered mlab photo 05">
    <figcaption>`mlab_05.jpg` from `IMG_3932.HEIC`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_06.jpg" alt="Recovered mlab photo 06">
    <figcaption>`mlab_06.jpg` from `IMG_3933.HEIC`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_07.jpg" alt="Recovered mlab photo 07">
    <figcaption>`mlab_07.jpg` from `IMG_3934.HEIC`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_08.jpg" alt="Recovered mlab photo 08">
    <figcaption>`mlab_08.jpg` from `IMG_3943.HEIC`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_09.jpg" alt="Recovered mlab photo 09">
    <figcaption>`mlab_09.jpg` from `IMG_4260.JPG`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_10.jpg" alt="Recovered mlab photo 10">
    <figcaption>`mlab_10.jpg` from `Pasted image (2).png`</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/mlab/mlab_11.jpg" alt="Recovered mlab photo 11">
    <figcaption>`mlab_11.jpg` from `Pasted image.png`</figcaption>
  </figure>
</div>

Once the strongest photos are chosen, this review block should be collapsed into a much smaller apparatus section with proper captions.

---

## Devices involved

| Tier | Device | Role in the campaign |
|------|--------|----------------------|
| Low-cost | Plantower PMS7003 | Optical PM sensor with PM1 / PM$\_{2.5}$ / PM$\_{10}$ output and size bins |
| Low-cost | Nova Fitness SDS011 | Optical PM sensor with PM$\_{2.5}$ / PM$\_{10}$ output; some deployments appear to have used a custom Python driver |
| Low-cost | Honeywell HPMA115S0 | Optical PM sensor with industrial-style documentation |
| Mid-tier | Dylos DC1100 Pro | Particle counter used as a practical comparison anchor |
| Mid-tier / adjacent | Dylos DC1700 | Nearby comparison monitor in the broader campaign |
| Consumer finished device / adjacent | IQAir AirVisual Node Pro | Nearby comparison monitor in the broader campaign |
| Reference | MetOne BAM-1020 | Earlier FEM-grade station used for calibration attempts |

---

## Why use Dylos as an anchor?

The Dylos DC1100 Pro sits in an interesting middle ground. It is much more expensive than hobby sensors like PMS7003 or SDS011, but still far below laboratory-grade reference instruments. It also reports **particle counts** rather than a directly standardized PM$\_{2.5}$ mass concentration, so part of the campaign was devoted to exploring how those counts might be converted into PM$\_{2.5}$-like values.

That makes Dylos useful for two separate reasons:

1. It is a **stable, self-contained field device** that can run for long periods and capture variation in particle counts.
2. It provides a **bridge** between cheap raw optical sensors and the more formal BAM-based calibration work.

The same logic likely applied to `DC1700` and `AirVisual` in the broader campaign: they were not BAM instruments, but they provided more operationally complete reference points than bare UART PM modules alone.

---

## SDS011 software note

The campaign also appears to have relied on customized software around some of the low-cost sensors. A useful lead is the `bi2air/SDS011` Python project, described as a **Python interface for the Nova Fitness SDS011 sensor** with support for **running multiple sensors at once**. That is consistent with a campaign architecture where several SDS011 devices were logged in parallel rather than as a single one-off bench setup.

---

## Converting Dylos counts to PM$\_{2.5}$

The archived campaign preserved five approaches for converting Dylos small-particle counts into PM$\_{2.5}$ estimates. The author ultimately chose the **GRIMM-based fit** for the rolling charting, but the page documented the alternatives explicitly.

![Five approaches to calculate PM$\_{2.5}$ from Dylos particle counts](/assets/images/research/collocation/dylos_conversion_methods.png)
*Five preserved conversion approaches for Dylos DC1100 Pro particle counts. The original live page used the GRIMM-based fit for charting.*

### 1. Particle density and representative size assumption

Assume particle density:

$$
\rho = 1.65 \times 10^{12}\ \mu g/m^3
$$

Assume representative particle radius:

$$
r = 0.44\ \mu m
$$

Mass of one particle:

$$
m = \rho \times \frac{4}{3}\pi r^3
$$

which gives approximately:

$$
m \approx 5.89 \times 10^{-7}\ \mu g
$$

Dylos reports small and large counts per `0.01 ft^3`, so the fine-particle count estimate is:

$$
\#p = (\text{small} - \text{large}) \times 3531
$$

and the implied PM$\_{2.5}$ mass estimate becomes:

$$
PM_{2.5} = (\text{small} - \text{large}) \times 2.08 \times 10^{-3}\ \mu g/m^3
$$

This is physically interpretable but rests on strong assumptions about density and representative size.

### 2. Beijing AQI fit

The archived notes also preserved a polynomial fit associated with the Beijing Dylos-to-AQI workflow:

$$
AQI_{US} = 3.31\times10^{-22}x^5 - 1.04\times10^{-16}x^4 + 1.19\times10^{-11}x^3 - 5.85\times10^{-7}x^2 + 0.016x + 9.43
$$

This approach maps raw Dylos counts to AQI first, then back-calculates PM$\_{2.5}$ from AQI breakpoints.

### 3. Simple estimation

A simpler field heuristic used in the original post was:

$$
PM_{2.5} = \frac{\text{small} - \text{large}}{100}
$$

The archived notes explicitly say this was hard to verify independently.

### 4. GRIMM EDM-180 fit

The AQ-SPEC / GRIMM-based fitting used in the original charting was:

$$
PM_{2.5} = -8\times10^{-12}x^2 + 5\times10^{-5}x + 3.98
$$

with archived goodness-of-fit:

$$
R^2 = 0.815
$$

### 5. MetOne BAM-1020 fit

The BAM-based fit preserved in the notes was:

$$
PM_{2.5} = -1\times10^{-11}x^2 + 4\times10^{-5}x + 4.17
$$

with archived goodness-of-fit:

$$
R^2 = 0.632
$$

This matters because it ties the Dylos-centered campaign back to the earlier **BAM comparison work**, even though the Dylos itself was not a reference instrument.

---

## Static correlation snapshots from the campaign

The original page was meant to update continuously. What survives are static monthly snapshots from the August 2019 run.

### Raw pairwise count relationships

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/dc1100_hpma_counts.png" alt="DC1100 versus Honeywell HPMA115S0 particle count correlation">
    <figcaption>Dylos DC1100 Pro versus Honeywell HPMA115S0.</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/dc1100_pms7003_counts.png" alt="DC1100 versus Plantower PMS7003 particle count correlation">
    <figcaption>Dylos DC1100 Pro versus Plantower PMS7003.</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/dc1100_sds011_counts.png" alt="DC1100 versus Nova Fitness SDS011 particle count correlation">
    <figcaption>Dylos DC1100 Pro versus Nova Fitness SDS011.</figcaption>
  </figure>
</div>

### PM$\_{2.5}$-adjusted pairwise comparisons

In the original post, the `-ad` plots indicated PM$\_{2.5}$ values adjusted using coefficients from the BAM-linked calibration work.

<div class="image-grid">
  <figure>
    <img src="/assets/images/research/collocation/pm25_dc1100_hpma.png" alt="PM$\_{2.5}$-adjusted comparison of DC1100 and Honeywell HPMA115S0">
    <figcaption>Adjusted PM$\_{2.5}$ comparison: Dylos DC1100 Pro and Honeywell HPMA115S0.</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/pm25_dc1100_pms7003.png" alt="PM$\_{2.5}$-adjusted comparison of DC1100 and Plantower PMS7003">
    <figcaption>Adjusted PM$\_{2.5}$ comparison: Dylos DC1100 Pro and Plantower PMS7003.</figcaption>
  </figure>
  <figure>
    <img src="/assets/images/research/collocation/pm25_dc1100_sds011.png" alt="PM$\_{2.5}$-adjusted comparison of DC1100 and Nova Fitness SDS011">
    <figcaption>Adjusted PM$\_{2.5}$ comparison: Dylos DC1100 Pro and Nova Fitness SDS011.</figcaption>
  </figure>
</div>

---

## What this campaign adds beyond the BAM page

The earlier [Low-Cost PM$\_{2.5}$ Sensors](/docs/research/pm25-low-cost-sensors.html) page is the better place for the strict **reference-station calibration** story. That page compares PMS7003 and SDS011 directly with the **US Embassy Hanoi MetOne BAM-1020** over about 60 days.

This campaign adds a different layer:

- **More sensors operating together in the same broader field effort**
- A dedicated **co-location unit** rather than only one-off sensor checks
- A **mid-tier field device** used as an operational anchor
- A practical attempt to answer whether the cheap sensors **move with the same air**, even when absolute PM$\_{2.5}$ remains uncertain
- A preserved example of how one might build **rolling co-location comparisons** before formal publication

In other words, the BAM page answers: *How far are these sensors from a reference?*

This page answers: *When multiple optical sensors are placed into the same field campaign, do they move together well enough to support interpretation?*

---

## Limits of the archived material

- The original page used a **live iframe/dashboard** that no longer exists, so this reconstruction is necessarily **static**.
- The current write-up combines **archived posts**, **CSV export metadata**, and **memory-based campaign reconstruction**, so some sensor pinning still needs verification.
- The preserved figures emphasize **DC1100-centered pairwise comparisons**, not a full synchronized matrix including DC1700 and IQAir.
- The Dylos-to-PM$\_{2.5}$ conversion methods are **attempts and fits**, not universal physical truth.
- The BAM comparison for Dylos was indirect in this reconstructed page; the strictest BAM work is still better represented in the earlier calibration study.
- At least one recovered file, `dust_work.csv`, contains obviously bad early timestamps and should not be treated as clean campaign data without further filtering.

---

## Takeaways

- This was a **real long-running field campaign**, not just a one-day gadget comparison.
- The campaign was valuable because it combined a dedicated **co-location unit**, **nearby anchor devices**, and an attempt to stay connected to a **reference-station calibration**.
- The original “dynamic” framing is historical; the durable value now is the **co-location design** and the preserved **static correlation figures**.
- The strongest next step is to verify the remaining file-to-sensor mappings and rebuild the campaign as a reproducible data article rather than a live dashboard.

---

## Related pages

- [Low-Cost PM$\_{2.5}$ Sensors](/docs/research/pm25-low-cost-sensors.html) — BAM-based calibration of PMS7003 and SDS011
- [AQI Calculation Guide](/docs/research/aqi-calculation-guide.html) — AQI breakpoints and PM$\_{2.5}$ conversion context

---

## References

- AQ-SPEC / South Coast AQMD field evaluation for Dylos DC1100 Pro
- MetOne BAM-1020 reference station material
- `fijnstofmeter.com` Dylos validation notes
- myhealthbeijing Dylos AQI conversion spreadsheet
- `bi2air/SDS011` Python interface for Nova Fitness SDS011 sensors
- Original archived `dynamic-correlate` and `dust-sensor` notes from b-io.info

---

*Draft reconstructed from archived 2019-2022 material. Live charting removed; campaign structure and preserved static figures retained.*

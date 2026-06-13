---
layout: default
title: Data
parent: Docs
has_children: false
permalink: /data/
---

# Data

Datasets and analysis resources from my environmental monitoring projects.

---

## Available Data

| Dataset | Source | Format | Repository |
|---------|--------|--------|-----------|
| PM2.5 sensor readings (Hanoi) | Low-cost sensor network | CSV | [air-quality-analysis](https://github.com/bi2air/air-quality-analysis) |
| Weather station logs | ESP8266 + DHT22 | SQL/CSV | [weatherstation](https://github.com/bi2air/weatherstation) |
| Bioreactor growth data | pH/temp/turbidity sensors | CSV | [advanced-bioreactor](https://github.com/bi2air/advanced-bioreactor) |

---

## Using the Data

```python
import pandas as pd

# Load PM2.5 data directly from GitHub
url = "https://raw.githubusercontent.com/bi2air/air-quality-analysis/main/data/sample.csv"
df = pd.read_csv(url)
print(df.describe())
```

See the [Jupyter notebooks](https://github.com/bi2air/air-quality-analysis/tree/main/notebooks) for full analysis examples.

---
layout: default
title: Code
parent: Docs
has_children: false
permalink: /code/
---

# Code

Repositories and code examples across my projects.

---

## Repositories

| Repository | Language | Description |
|-----------|----------|-------------|
| [air-quality-analysis](https://github.com/bi2air/air-quality-analysis) | Python | PM2.5 data processing, Jupyter notebooks |
| [advanced-bioreactor](https://github.com/bi2air/advanced-bioreactor) | C++, Python | pH/temp monitoring, growth simulation |
| [weatherstation](https://github.com/bi2air/weatherstation) | C++, SQL | ESP8266 IoT station, Flask dashboard |
| [arduinos](https://github.com/bi2air/arduinos) | C++ | LED, PIR, power meter projects |

---

## Example: PM2.5 Analysis (Python)

```python
import pandas as pd
import matplotlib.pyplot as plt

def analyze_pm25(data_file):
    df = pd.read_csv(data_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    daily_avg = df.groupby(df['timestamp'].dt.date)['pm25'].mean()

    plt.figure(figsize=(12, 6))
    plt.plot(daily_avg.index, daily_avg.values)
    plt.axhline(y=25, color='r', linestyle='--', label='WHO limit')
    plt.ylabel('PM2.5 (ug/m3)')
    plt.legend()
    plt.tight_layout()
    plt.savefig('pm25_daily.png', dpi=150)
```

[Full notebooks on GitHub](https://github.com/bi2air/air-quality-analysis/tree/main/notebooks)

---

## Example: ESP8266 MQTT (C++)

```cpp
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

void publishSensorData() {
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();
  String payload = "{\"temperature\":" + String(temp) +
                   ",\"humidity\":" + String(humidity) + "}";
  client.publish("weather/station/data", payload.c_str());
}
```

[Full source on GitHub](https://github.com/bi2air/weatherstation)

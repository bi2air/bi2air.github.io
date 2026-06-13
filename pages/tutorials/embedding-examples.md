---
layout: default
title: Embedding Code
parent: Tutorials
nav_order: 5
---

# Embedding Code from GitHub

How to reference and display code from your repositories in Jekyll pages.

---

## Link to a file

```markdown
[View the Arduino code](https://github.com/bi2air/advanced-bioreactor/blob/main/bioreactor.ino)
```

Link to a specific line: append `#L42` or a range `#L10-L20`.

---

## Embed a code snippet

Copy relevant sections and attribute the source:

```cpp
// Source: https://github.com/bi2air/advanced-bioreactor
float readPH() {
  int sensorValue = analogRead(PH_PIN);
  float voltage = sensorValue * (5.0 / 1024.0);
  float pH = 3.5 * voltage + CALIBRATION_OFFSET;
  return pH;
}
```

---

## Raw file URLs (for downloads)

Format: `https://raw.githubusercontent.com/USER/REPO/BRANCH/path/to/file`

```markdown
[Download dataset](https://raw.githubusercontent.com/bi2air/air-quality-analysis/main/data/sample.csv)
```

Works for CSV, JSON, images, or any file you want users to download directly.

---

## Link to Jupyter notebooks

```markdown
[PM$\_{2.5}$ Analysis](https://github.com/bi2air/air-quality-analysis/blob/main/notebooks/pm25_analysis.ipynb)
```

For rendered viewing: use [nbviewer.org](https://nbviewer.org/) prefix.

---

## Quick reference

| Target | URL pattern |
|--------|------------|
| File | `github.com/USER/REPO/blob/BRANCH/path` |
| Raw file | `raw.githubusercontent.com/USER/REPO/BRANCH/path` |
| Line | append `#L42` |
| Line range | append `#L10-L20` |
| Repository | `github.com/USER/REPO` |

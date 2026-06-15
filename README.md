# Bi2Air — Projects & Research Notes

This repository contains the source code for the personal documentation and research site of **Binh Nguyen** (Bi2Air). 

The site serves as a public notebook and portfolio detailing work across:
- **Environmental Monitoring:** Advanced PM2.5 forecasting using machine learning (Delta-Skip architectures), low-cost sensor calibration networks, and filtration efficiency studies.
- **Hardware & IoT:** Custom sensor system builds, microalgae turbidostats, ESP8266/ESP32 data loggers, and hardware integration.
- **Home Lab Infrastructure:** eGPU configurations, mini-PC builds, and self-hosted services.

You can view the live site at: **[bi2air.github.io](https://bi2air.github.io)**

---

## 📂 Repository Structure

This repository is built using [Jekyll](https://jekyllrb.com/) and the [Just the Docs](https://just-the-docs.com/) theme. 

- `index.md` — The site's homepage
- `pages/` — Core research documents, lab notebooks, and project pages
- `docs/` — Internal logs tracking site updates and maintenance
- `blog/` — Archive of long-form posts (English and Vietnamese)
- `assets/` — Images, generated charts, and PDFs 

*(Note: The standalone PM2.5 forecasting codebase and datasets are maintained in a separate repository to keep this site lightweight.)*

---

## 🛠 Local Development

If you need to build or modify the site locally:

1. Clone this repository
2. Ensure you have Ruby and Bundler installed
3. Install the required gem dependencies:
   ```bash
   bundle install
   ```
4. Run the local Jekyll server using the helper script:
   ```bash
   scripts/local-jekyll-test.zsh
   ```
5. View the site at `http://localhost:4000`

---

## 📄 License

This site's source code and content are available under the MIT License unless otherwise noted on specific research pages.

# My Documentation Site

A Jekyll-based documentation site using the Just the Docs theme.

## Local Development

### Prerequisites
- Miniconda installed at `$HOME/miniconda3`
- Ruby and Bundler installed into that Miniconda base environment
- Network access on first build so `jekyll-remote-theme` can fetch `just-the-docs`

### Setup

1. Clone this repository
2. Install Ruby and the local build toolchain into Miniconda:
   ```bash
   $HOME/miniconda3/bin/conda install -y -c conda-forge ruby c-compiler cxx-compiler make pkg-config
   ```
3. Install gem dependencies:
   ```bash
   export PATH="$HOME/miniconda3/bin:$PATH"
   bundle install
   ```
4. Run the local server:
   ```bash
   scripts/local-jekyll-test.zsh
   ```

5. Open your browser and visit: `http://localhost:4000`

## Project Structure

```
.
├── _config.yml          # Site configuration
├── index.md             # Homepage
├── docs/                # Documentation pages
├── code/                # Code examples
├── data/                # Data resources
└── Gemfile              # Ruby dependencies
```

## Data Policy

- Large external source data is kept out of GitHub. This includes regenerated data under `data/external/`, Open-Meteo source exports, and IGRA/radiosonde source products.
- For notebook demos, keep the smaller 2018 example datasets versioned, matching the original lightweight demo approach instead of pushing full multi-year source archives.

## Deployment

This site is designed to be deployed on GitHub Pages:

1. Create a GitHub repository
2. Push this code to the repository
3. Enable GitHub Pages in repository settings
4. Your site will be live at `https://username.github.io/repository-name`

## Customization

- Edit `_config.yml` to change site settings
- Modify the color scheme in `_config.yml`
- Add new pages by creating `.md` files
- Organize content using front matter navigation

## Theme Documentation

This site uses [Just the Docs](https://just-the-docs.com/) theme.

## License

MIT License

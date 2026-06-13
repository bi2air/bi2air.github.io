#!/usr/bin/env zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

MINICONDA_HOME="${MINICONDA_HOME:-$HOME/miniconda3}"
RUBY_BIN="$MINICONDA_HOME/bin/ruby"
BUNDLE_BIN="$MINICONDA_HOME/bin/bundle"
BUNDLE_USER_HOME="${BUNDLE_USER_HOME:-/tmp/bundler}"
HOST="${HOST:-127.0.0.1}"
if [[ "$HOST" == "$(hostname)" || "$HOST" == "$(hostname -s 2>/dev/null)" ]]; then
  HOST="127.0.0.1"
fi
PORT="${PORT:-4000}"

if [[ ! -x "$RUBY_BIN" || ! -x "$BUNDLE_BIN" ]]; then
  echo "Missing Ruby or Bundler binary under $MINICONDA_HOME/bin" >&2
  exit 1
fi

export PATH="$MINICONDA_HOME/bin:$PATH"
export BUNDLE_USER_HOME

echo "==> Building Jekyll site"
"$RUBY_BIN" -S "$BUNDLE_BIN" exec jekyll build --config _config.yml,_config.local.yml

echo "==> Serving at http://$HOST:$PORT/"
"$RUBY_BIN" -S "$BUNDLE_BIN" exec jekyll serve --config _config.yml,_config.local.yml --host "$HOST" --port "$PORT"

#!/bin/bash
# Fix scientific terms to use MathJax-compatible formatting across all markdown files
# Key principle: each expression must be a SINGLE $...$ block, not fragmented.
# Also escape underscores (\_{}) so kramdown doesn't treat _ as emphasis.

set -e

echo "Fixing scientific terms to MathJax format..."

# Find all markdown files in docs/
find docs/ -name "*.md" -type f | while read -r file; do
    echo "Processing: $file"

    # PM2.5 → PM$\_{2.5}$ (escaped underscore for kramdown)
    sed -i 's/\bPM2\.5\b/PM$\\_{2.5}$/g' "$file"

    # PM10 → PM$\_{10}$
    sed -i 's/\bPM10\b/PM$\\_{10}$/g' "$file"

    # ug/m3 → $\mu g/m^3$ (single expression, not fragmented)
    sed -i 's/ug\/m3/$\\mu g\/m^3$/g' "$file"
    sed -i 's/µg\/m³/$\\mu g\/m^3$/g' "$file"

    # CO2 → CO$\_2$ (but not in URLs or filenames)
    sed -i 's/\bCO2\b/CO$\\_2$/g' "$file"

    # R2 → $R^2$ (single expression)
    sed -i 's/\bR2 /$R^2$ /g' "$file"
    sed -i 's/\bR2$/$R^2$/g' "$file"
    sed -i 's/\bR2)/$R^2$)/g' "$file"
    sed -i 's/\bR2,/$R^2$,/g' "$file"
    sed -i 's/| R2 |/| $R^2$ |/g' "$file"
done

echo "Done! Check changes with: git diff docs/"
echo ""
echo "IMPORTANT: Do NOT put MathJax expressions inside backticks (\`...\`)."
echo "Backticks create <code> tags which MathJax skips."

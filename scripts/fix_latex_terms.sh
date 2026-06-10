#!/bin/bash
# Fix scientific terms to use LaTeX formatting across all markdown files

set -e

echo "Fixing scientific terms to LaTeX format..."

# Find all markdown files in docs/
find docs/ -name "*.md" -type f | while read -r file; do
    echo "Processing: $file"

    # PM2.5 → PM$_{2.5}$ (but not if already formatted)
    sed -i 's/\bPM2\.5\b/PM$_{2.5}$/g' "$file"

    # PM10 → PM$_{10}$
    sed -i 's/\bPM10\b/PM$_{10}$/g' "$file"

    # ug/m3 → $\mu$g/m$^3$
    sed -i 's/ug\/m3/\$\\mu\$g\/m\$\^3\$/g' "$file"
    sed -i 's/µg\/m³/\$\\mu\$g\/m\$\^3\$/g' "$file"

    # CO2 → CO$_2$ (but not in URLs or filenames)
    sed -i 's/\bCO2\b/CO$_2$/g' "$file"

    # R2 → R$^2$ (but not R2 in context like "R2 = 0.5")
    sed -i 's/\bR2 /R$^2$ /g' "$file"
    sed -i 's/\bR2$/R$^2$/g' "$file"
    sed -i 's/\bR2)/R$^2$)/g' "$file"
    sed -i 's/\bR2,/R$^2$,/g' "$file"
    sed -i 's/| R2 |/| R$^2$ |/g' "$file"
done

echo "Done! Check changes with: git diff docs/"

#!/bin/bash
# HKP Dashboard — Refresh Script
# Double-click this file to update the website with new data

SITE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SITE_DIR"

echo "======================================"
echo "  HKP Dashboard — Data Refresh"
echo "======================================"
echo ""

echo "[1/3] Generating data.json from Excel files..."
python3 generate_data.py
if [ $? -ne 0 ]; then
    echo "❌  Error generating data. Check Excel file paths."
    read -p "Press Enter to close..."
    exit 1
fi

echo ""
echo "[2/3] Committing to git..."
git add data.json
git commit -m "data: refresh $(date '+%Y-%m-%d %H:%M')"

echo ""
echo "[3/3] Pushing to GitHub Pages..."
git push origin main
if [ $? -ne 0 ]; then
    git push origin master
fi

echo ""
echo "======================================"
echo "  ✅  Done! Website will update in ~1 min"
echo "  🌐  https://krit-the-creator.github.io/hkp-dashboard/"
echo "======================================"
echo ""
read -p "Press Enter to close..."

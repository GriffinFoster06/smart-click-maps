#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing Python dependencies"
python3 -m pip install -r requirements.txt

echo "==> Installing Node dependencies"
npm install

echo "==> Setup complete. Run 'npm run dev' to start."

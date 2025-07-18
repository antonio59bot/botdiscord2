#!/bin/bash
echo "===== INSTALLING DEPENDENCIES ====="
pip uninstall -y discord discord.py || true
pip install py-cord==2.
pip install -r requirements.txt

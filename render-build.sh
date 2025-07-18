#!/usr/bin/env bash

# Installer les dépendances
pip install -r requirements.txt

# Supprimer d'éventuels paquets indésirables
pip uninstall -y discord discord.py

# Réinstaller py-cord
pip install py-cord==2.4.0

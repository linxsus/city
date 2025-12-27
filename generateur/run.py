#!/usr/bin/env python3
"""Script de lancement du Générateur de Classes."""

import sys
from pathlib import Path

# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generateur.main import run

if __name__ == "__main__":
    run()

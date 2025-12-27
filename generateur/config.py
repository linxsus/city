"""Configuration du générateur de classes."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemins de base
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

# Chemins du générateur
UPLOAD_DIR = BASE_DIR / "uploads"
GENERATED_DIR = BASE_DIR / "genere"
TEMPLATES_OUTPUT_DIR = GENERATED_DIR / "templates"
SESSIONS_DIR = BASE_DIR / "sessions"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Chemins du framework existant
FRAMEWORK_ETATS_DIR = PROJECT_ROOT / "manoirs" / "etats"
FRAMEWORK_CHEMINS_DIR = PROJECT_ROOT / "manoirs" / "chemins"
FRAMEWORK_TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Créer les dossiers nécessaires
for dir_path in [UPLOAD_DIR, GENERATED_DIR, TEMPLATES_OUTPUT_DIR, SESSIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Configuration serveur
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Configuration Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "2048"))
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT", "30"))

# Configuration détection
DEFAULT_THRESHOLD = 0.8
MIN_THRESHOLD = 0.5
MAX_THRESHOLD = 1.0
DUPLICATE_THRESHOLD = 0.90

# Configuration OCR
OCR_LANG = "fra"

# Priorités par défaut
POPUP_PRIORITY = 80
NORMAL_PRIORITY = 0

# Délais par défaut
DEFAULT_DELAY_AFTER = 0.1


def is_claude_available() -> bool:
    """Vérifie si l'API Claude est configurée."""
    return bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY.startswith("sk-ant-"))


def get_existing_groups() -> list[str]:
    """Récupère les groupes existants depuis le framework."""
    groups = set()

    # Lire les états existants pour extraire les groupes
    if FRAMEWORK_ETATS_DIR.exists():
        for file in FRAMEWORK_ETATS_DIR.glob("*.py"):
            if file.name.startswith("__"):
                continue
            try:
                content = file.read_text(encoding="utf-8")
                # Chercher les groupes définis
                import re
                match = re.search(r'groupes\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if match:
                    group_str = match.group(1)
                    for g in re.findall(r'["\']([^"\']+)["\']', group_str):
                        groups.add(g)
            except Exception:
                pass

    return sorted(groups)


def get_existing_states() -> list[str]:
    """Récupère les noms des états existants."""
    states = []

    if FRAMEWORK_ETATS_DIR.exists():
        for file in FRAMEWORK_ETATS_DIR.glob("*.py"):
            if file.name.startswith("__"):
                continue
            try:
                content = file.read_text(encoding="utf-8")
                import re
                match = re.search(r'nom\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    states.append(match.group(1))
            except Exception:
                pass

    return sorted(states)

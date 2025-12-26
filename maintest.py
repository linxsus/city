# -*- coding: utf-8 -*-
"""Test du système avec simulation du lancement BlueStacks

Ce script permet de tester le flow complet du système sans avoir
BlueStacks installé. Il simule :
- Le lancement réussi de l'application
- La détection de fenêtre
- Les transitions d'état (non_lance -> chargement -> ville)

Usage:
    python maintest.py              # Test avec simulation complète
    python maintest.py --scenario ville    # Démarre directement en ville
    python maintest.py --scenario popup    # Démarre avec un popup
"""
import sys
import time
import argparse
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import threading

# Ajouter le dossier au path
sys.path.insert(0, str(Path(__file__).parent))

# Importer numpy pour les mocks
import numpy as np


class SimulateurBlueStacks:
    """Simule le comportement de BlueStacks pour les tests"""

    def __init__(self, scenario='lancement'):
        """
        Args:
            scenario: 'lancement' | 'ville' | 'popup' | 'chargement'
        """
        self.scenario = scenario
        self._etat_simule = self._etat_initial()
        self._fenetre_visible = scenario != 'lancement'
        self._hwnd_simule = 12345 if self._fenetre_visible else None
        self._temps_lancement = None
        self._temps_init_termine = None  # Initialisé ici aussi
        self._delai_chargement = 3  # secondes simulées

    def _etat_initial(self):
        """Retourne l'état initial selon le scénario"""
        return {
            'lancement': 'non_lance',
            'chargement': 'chargement',
            'ville': 'ville',
            'popup': 'popup_rapport',
        }.get(self.scenario, 'non_lance')

    def simuler_lancement(self):
        """Simule le lancement de BlueStacks"""
        print("[SIMULATION] Lancement de BlueStacks simulé")
        self._temps_lancement = time.time()
        self._temps_init_termine = None  # Sera défini quand on entre en chargement
        self._fenetre_visible = True
        self._hwnd_simule = 12345
        self._etat_simule = 'chargement'
        return True

    def marquer_init_termine(self):
        """Marque que temps_initialisation est terminé"""
        if self._temps_init_termine is None:
            self._temps_init_termine = time.time()
            print(f"[SIMULATION] temps_init terminé, chargement pendant {self._delai_chargement}s...", flush=True)

    def get_etat_actuel(self):
        """Retourne l'état actuel simulé"""
        # Si en chargement, vérifier si le délai est passé APRÈS temps_init
        if self._etat_simule == 'chargement' and self._temps_init_termine:
            if time.time() - self._temps_init_termine > self._delai_chargement:
                self._etat_simule = 'ville'
                print("[SIMULATION] Chargement terminé -> ville", flush=True)
        return self._etat_simule

    def get_hwnd(self):
        """Retourne le handle de fenêtre simulé"""
        return self._hwnd_simule

    def is_fenetre_visible(self):
        """Retourne si la fenêtre est visible"""
        return self._fenetre_visible


# Instance globale du simulateur
_simulateur = None


def get_simulateur():
    global _simulateur
    return _simulateur


def mock_find_window(self):
    """Mock pour ManoirBase.find_window()"""
    sim = get_simulateur()
    if sim and sim.is_fenetre_visible():
        return sim.get_hwnd()
    return None


def mock_subprocess_run(cmd, *args, **kwargs):
    """Mock pour subprocess.run() - simule le lancement BlueStacks"""
    sim = get_simulateur()
    # Vérifier si c'est une commande BlueStacks
    cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
    if 'HD-Player' in cmd_str or 'BlueStacks' in cmd_str:
        print("[SIMULATION] Lancement BlueStacks intercepté (run)")
        if sim:
            sim.simuler_lancement()
        # Retourner un mock de CompletedProcess
        result = MagicMock()
        result.returncode = 0
        result.stdout = b''
        result.stderr = b''
        return result
    # Fallback - ne pas exécuter les autres commandes non plus en mode test
    result = MagicMock()
    result.returncode = 0
    return result


class MockPopen:
    """Mock pour subprocess.Popen - simule un processus en cours"""

    def __init__(self, cmd, *args, **kwargs):
        self.cmd = cmd
        self.pid = 99999
        self._returncode = None
        self._started = False

        # Vérifier si c'est une commande BlueStacks
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
        if 'HD-Player' in cmd_str or 'BlueStacks' in cmd_str:
            print("[SIMULATION] Lancement BlueStacks intercepté (Popen)")
            sim = get_simulateur()
            if sim:
                sim.simuler_lancement()
            self._started = True

    def poll(self):
        """Retourne None si le processus est en cours, sinon le code retour"""
        if self._started:
            return None  # Processus en cours
        return 0

    def communicate(self, input=None, timeout=None):
        """Retourne (stdout, stderr)"""
        return (b'', b'')

    def wait(self, timeout=None):
        """Attend la fin du processus"""
        return 0


def mock_determiner_etat_actuel(self, manoir, liste_etats=None):
    """Mock pour GestionnaireEtats.determiner_etat_actuel()"""
    sim = get_simulateur()
    if sim:
        # Si on est en chargement, marquer que temps_init est terminé
        if sim._etat_simule == 'chargement':
            sim.marquer_init_termine()

        # Obtenir l'état actuel simulé
        etat_nom = sim.get_etat_actuel()
        print(f"[SIMULATION] État déterminé: {etat_nom}", flush=True)

        # Retourner l'instance d'état correspondante
        try:
            return self.obtenir_etat(etat_nom)
        except Exception:
            # Fallback si l'état n'existe pas
            for etat in self._etats.values():
                if etat.nom == etat_nom:
                    return etat
            # Retourner le premier état inconnu
            for etat in self._etats.values():
                if hasattr(etat, 'etats_possibles'):
                    return etat

    # Appeler la méthode originale si pas de simulateur
    return self._original_determiner_etat_actuel(manoir, liste_etats)


def mock_capture(self, force=False):
    """Mock pour ManoirBase.capture()"""
    # Retourner une image noire simulée
    self._last_capture = np.zeros((720, 1280, 3), dtype=np.uint8)
    self._capture_time = time.time()
    return self._last_capture


def mock_last_capture_getter(self):
    """Mock pour la propriété _last_capture"""
    if not hasattr(self, '_mock_capture'):
        self._mock_capture = np.zeros((720, 1280, 3), dtype=np.uint8)
    return self._mock_capture


def mock_detect_image(self, image_path, *args, **kwargs):
    """Mock pour ManoirBase.detect_image()"""
    # Simuler la détection selon l'état
    sim = get_simulateur()
    if sim:
        etat = sim.get_etat_actuel()
        # Simuler les détections selon l'état
        if 'loading' in str(image_path).lower() or 'chargement' in str(image_path).lower():
            return etat == 'chargement'
        if 'ville' in str(image_path).lower() or 'city' in str(image_path).lower():
            return etat == 'ville'
    return False


def main_test():
    """Fonction principale de test"""
    global _simulateur

    parser = argparse.ArgumentParser(description="Test du système avec simulation")
    parser.add_argument(
        '--scenario', '-s',
        choices=['lancement', 'ville', 'popup', 'chargement'],
        default='lancement',
        help='Scénario de test (default: lancement)'
    )
    parser.add_argument(
        '--duree', '-d',
        type=int,
        default=30,
        help='Durée du test en secondes (default: 30)'
    )
    parser.add_argument(
        '--delai-chargement',
        type=int,
        default=3,
        help='Délai simulé pour le chargement en secondes (default: 3)'
    )
    parser.add_argument(
        '--temps-init',
        type=int,
        default=5,
        help='Temps d\'initialisation BlueStacks en secondes (default: 5, prod: 300)'
    )
    args = parser.parse_args()

    # Nettoyer sys.argv pour que main.py ne voie pas nos arguments
    sys.argv = [sys.argv[0]]

    # Créer le simulateur
    _simulateur = SimulateurBlueStacks(scenario=args.scenario)
    _simulateur._delai_chargement = args.delai_chargement

    print("=" * 60)
    print(" TEST DU SYSTÈME AVEC SIMULATION")
    print("=" * 60)
    print(f"Scénario: {args.scenario}")
    print(f"Durée: {args.duree}s")
    print(f"Délai chargement: {args.delai_chargement}s")
    print(f"Temps init BlueStacks: {args.temps_init}s")
    print("=" * 60)
    print()

    # Patcher la config pour réduire temps_initialisation
    import manoirs.config_manoirs as config_module
    for manoir_config in config_module.MANOIRS_CONFIG.values():
        if "temps_initialisation" in manoir_config:
            manoir_config["temps_initialisation"] = args.temps_init

    # Importer le module qui utilise subprocess pour le patcher correctement
    import actions.bluestacks.action_lancer_raccourci as action_module
    from core.gestionnaire_etats import GestionnaireEtats

    # Sauvegarder la méthode originale
    GestionnaireEtats._original_determiner_etat_actuel = GestionnaireEtats.determiner_etat_actuel

    # Appliquer tous les mocks
    with patch.object(action_module, 'subprocess') as mock_subproc, \
         patch('manoirs.manoir_base.ManoirBase.find_window', mock_find_window), \
         patch('manoirs.manoir_base.ManoirBase.capture', mock_capture), \
         patch('manoirs.manoir_base.ManoirBase.detect_image', mock_detect_image), \
         patch.object(GestionnaireEtats, 'determiner_etat_actuel', mock_determiner_etat_actuel):

        # Configurer le mock de subprocess
        mock_subproc.run = mock_subprocess_run
        mock_subproc.Popen = MockPopen
        mock_subproc.PIPE = subprocess.PIPE

        # Timer pour arrêter automatiquement après la durée
        def auto_stop():
            time.sleep(args.duree)
            print(f"\n[TEST] Durée de {args.duree}s atteinte, arrêt...")
            import os
            import signal
            os.kill(os.getpid(), signal.SIGINT)

        timer_thread = threading.Thread(target=auto_stop, daemon=True)
        timer_thread.start()

        # Lancer le main
        import main
        return main.main()


if __name__ == "__main__":
    sys.exit(main_test())

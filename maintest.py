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
from pathlib import Path
from unittest.mock import patch, MagicMock
import threading

# Ajouter le dossier au path
sys.path.insert(0, str(Path(__file__).parent))


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
        self._fenetre_visible = True
        self._hwnd_simule = 12345
        self._etat_simule = 'chargement'
        return True

    def get_etat_actuel(self):
        """Retourne l'état actuel simulé"""
        # Si en chargement, vérifier si le délai est passé
        if self._etat_simule == 'chargement' and self._temps_lancement:
            if time.time() - self._temps_lancement > self._delai_chargement:
                self._etat_simule = 'ville'
                print("[SIMULATION] Chargement terminé -> ville")
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
    if sim:
        # Vérifier si c'est une commande BlueStacks
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
        if 'HD-Player' in cmd_str or 'BlueStacks' in cmd_str:
            sim.simuler_lancement()
            # Retourner un mock de CompletedProcess
            result = MagicMock()
            result.returncode = 0
            result.stdout = b''
            result.stderr = b''
            return result
    # Fallback au comportement normal pour les autres commandes
    import subprocess
    return subprocess._original_run(cmd, *args, **kwargs)


def mock_etat_verif_non_lance(self, manoir):
    """Mock pour EtatNonLance.verif()"""
    sim = get_simulateur()
    if sim:
        return sim.get_etat_actuel() == 'non_lance'
    return True


def mock_etat_verif_chargement(self, manoir):
    """Mock pour EtatChargement.verif()"""
    sim = get_simulateur()
    if sim:
        return sim.get_etat_actuel() == 'chargement'
    return False


def mock_etat_verif_ville(self, manoir):
    """Mock pour EtatVille.verif()"""
    sim = get_simulateur()
    if sim:
        return sim.get_etat_actuel() == 'ville'
    return False


def mock_capture(self, force=False):
    """Mock pour ManoirBase.capture()"""
    # Retourner une image noire simulée
    import numpy as np
    self._last_capture = np.zeros((720, 1280, 3), dtype=np.uint8)
    return self._last_capture


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
    args = parser.parse_args()

    # Créer le simulateur
    _simulateur = SimulateurBlueStacks(scenario=args.scenario)
    _simulateur._delai_chargement = args.delai_chargement

    print("=" * 60)
    print(" TEST DU SYSTÈME AVEC SIMULATION")
    print("=" * 60)
    print(f"Scénario: {args.scenario}")
    print(f"Durée: {args.duree}s")
    print(f"Délai chargement: {args.delai_chargement}s")
    print("=" * 60)
    print()

    # Sauvegarder subprocess.run original
    import subprocess
    subprocess._original_run = subprocess.run

    # Appliquer les mocks
    with patch('subprocess.run', mock_subprocess_run), \
         patch('manoirs.manoir_base.ManoirBase.find_window', mock_find_window), \
         patch('manoirs.manoir_base.ManoirBase.capture', mock_capture), \
         patch('manoirs.manoir_base.ManoirBase.detect_image', mock_detect_image):

        # Patcher les vérifications d'état
        try:
            from manoirs.etats.etat_non_lance import EtatNonLance
            from manoirs.etats.etat_chargement import EtatChargement
            from manoirs.etats.etat_ville import EtatVille

            with patch.object(EtatNonLance, 'verif', mock_etat_verif_non_lance), \
                 patch.object(EtatChargement, 'verif', mock_etat_verif_chargement), \
                 patch.object(EtatVille, 'verif', mock_etat_verif_ville):

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

        except ImportError as e:
            print(f"Erreur d'import: {e}")
            print("Certains modules d'état ne sont pas disponibles")
            return 1


if __name__ == "__main__":
    sys.exit(main_test())

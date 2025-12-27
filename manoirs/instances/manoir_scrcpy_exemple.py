"""Exemple de Manoir Scrcpy - Automatisation Android via ADB

Cet exemple montre comment utiliser ManoirScrcpy pour automatiser
un appareil Android connecté en USB.

Fonctionnalités démontrées :
- Détection automatique de l'appareil
- Lancement optionnel de scrcpy
- Capture d'écran via ADB
- Clics et interactions via ADB
- Sauvegarde de captures pour templates
"""

import time

import actions.liste_actions as ListeActions
from manoirs.config_manoirs import get_config
from manoirs.manoir_scrcpy import ManoirScrcpy


class ManoirScrcpyExemple(ManoirScrcpy):
    """Exemple d'implémentation d'un manoir Scrcpy

    Ce manoir :
    1. Détecte automatiquement l'appareil Android
    2. Lance scrcpy pour visualisation (optionnel)
    3. Exécute une boucle qui :
       - Fait une capture d'écran toutes les 30 secondes
       - Log un message pour montrer qu'il est actif
    """

    def __init__(self, manoir_id="android", config=None):
        """Initialise le manoir exemple

        Args:
            manoir_id: Identifiant du manoir
            config: Configuration (chargée depuis config_manoirs si None)
        """
        if config is None:
            config = get_config(manoir_id) or {}

        super().__init__(
            manoir_id=manoir_id,
            nom=config.get("nom", "Android Exemple"),
            adb_path=config.get("adb_path", "adb"),
            scrcpy_path=config.get("scrcpy_path", "scrcpy"),
            scrcpy_max_size=config.get("scrcpy_max_size", 1024),
            device_serial=config.get("device_serial"),
            largeur=config.get("largeur", 1024),
            hauteur=config.get("hauteur", 576),
            priorite=config.get("priorite", 50),
        )

        self.logger.info(f"Manoir Scrcpy '{self.nom}' initialisé")
        self._premiere_fois = True

    def definir_timers(self):
        """Pas de timers pour cet exemple simple"""
        pass

    def _preparer_alimenter_sequence(self):
        """Alimente la séquence avec les actions à exécuter

        Logique :
        1. Vérifie que l'appareil est connecté
        2. Lance scrcpy si pas encore lancé
        3. Exécute la boucle principale
        """
        # Vérifier la connexion de l'appareil
        if not self.adb.is_device_connected():
            self.logger.warning("Aucun appareil connecté, attente...")
            # Ajouter une action d'attente non-bloquante
            self.sequence.ajouter(
                ListeActions.ActionAttendre(self, 5)
            )
            return True

        # Première fois : afficher les infos de l'appareil
        if self._premiere_fois:
            device_info = self.get_device_info()
            self.logger.info(f"Appareil: {device_info['name']} ({device_info['serial']})")
            self.logger.info(f"Écran: {device_info['screen_size']}")

            # Lancer scrcpy pour visualisation
            if not self.is_scrcpy_running():
                self.logger.info("Lancement de scrcpy...")
                self.launch_scrcpy()
                time.sleep(2)

            self._premiere_fois = False

        # Créer la boucle principale
        if self.sequence.is_end():
            self._creer_boucle_principale()

        return True

    def _creer_boucle_principale(self):
        """Crée la boucle principale d'actions"""
        boucle = ListeActions.ActionWhile(
            self,
            condition_func=lambda m: m.adb.is_device_connected(),
            actions=[
                # Attendre 30 secondes
                ListeActions.ActionAttendre(self, 30),
                # Log un message
                ListeActions.ActionLog(self, "Manoir Scrcpy actif", level="info"),
                # Sauvegarder une capture (optionnel, décommenter si besoin)
                # ActionSauvegarderCapture(self, suffix="_auto"),
            ],
            max_iterations=None,  # Boucle infinie
            nom_boucle="boucle_principale",
        )

        self.sequence.ajouter(boucle)
        self.logger.debug("Boucle principale ajoutée")

    def get_prochain_passage_prioritaire(self):
        """Pas d'actions prioritaires"""
        return float("inf")

    def get_prochain_passage_normal(self):
        """Toujours prêt à être traité"""
        return 0


# =====================================================
# FONCTIONS UTILITAIRES
# =====================================================

def creer_manoir_scrcpy(manoir_id="android"):
    """Crée une instance du manoir Scrcpy exemple

    Args:
        manoir_id: ID du manoir (doit exister dans config_manoirs)

    Returns:
        ManoirScrcpyExemple: Instance du manoir
    """
    return ManoirScrcpyExemple(manoir_id=manoir_id)


def test_connexion_adb():
    """Teste la connexion ADB et affiche les infos de l'appareil

    Returns:
        bool: True si un appareil est connecté
    """
    from core.adb_manager import get_adb_manager

    adb = get_adb_manager()
    devices = adb.get_connected_devices()

    if not devices:
        print("Aucun appareil Android connecté")
        print("Vérifiez que :")
        print("  1. L'appareil est connecté en USB")
        print("  2. Le débogage USB est activé")
        print("  3. ADB est installé et dans le PATH")
        return False

    print(f"Appareils connectés : {len(devices)}")
    for device in devices:
        print(f"  - {device['serial']} ({device['status']})")

    # Sélectionner le premier appareil prêt
    ready = [d for d in devices if d['status'] == 'device']
    if ready:
        adb.device_serial = ready[0]['serial']
        print(f"\nAppareil sélectionné : {adb.device_serial}")
        print(f"Modèle : {adb.get_device_name()}")
        print(f"Taille écran : {adb.get_screen_size()}")
        return True

    print("Aucun appareil prêt (vérifiez l'autorisation USB)")
    return False


def test_capture_adb():
    """Teste la capture d'écran via ADB

    Returns:
        bool: True si capture réussie
    """
    from core.adb_manager import get_adb_manager

    adb = get_adb_manager()

    if not adb.detect_device():
        print("Aucun appareil connecté")
        return False

    print("Capture en cours...")
    image = adb.capture_screen()

    if image:
        print(f"Capture réussie : {image.size}")
        # Sauvegarder la capture
        filepath = "test_capture_adb.png"
        image.save(filepath)
        print(f"Sauvegardée : {filepath}")
        return True

    print("Échec de la capture")
    return False


def test_tap_adb(x, y):
    """Teste un tap via ADB

    Args:
        x, y: Coordonnées du tap

    Returns:
        bool: True si tap réussi
    """
    from core.adb_manager import get_adb_manager

    adb = get_adb_manager()

    if not adb.detect_device():
        print("Aucun appareil connecté")
        return False

    print(f"Tap à ({x}, {y})...")
    result = adb.tap(x, y)

    if result:
        print("Tap réussi")
    else:
        print("Échec du tap")

    return result


# =====================================================
# POINT D'ENTRÉE POUR TESTS
# =====================================================

if __name__ == "__main__":
    print("=== Test Manoir Scrcpy ===\n")

    # Test 1 : Connexion ADB
    print("1. Test connexion ADB...")
    if not test_connexion_adb():
        print("\nArrêt des tests (pas d'appareil)")
        exit(1)

    print()

    # Test 2 : Capture d'écran
    print("2. Test capture d'écran...")
    test_capture_adb()

    print()

    # Test 3 : Création du manoir
    print("3. Création du manoir...")
    manoir = creer_manoir_scrcpy()
    print(f"Manoir créé : {manoir}")
    print(f"Infos appareil : {manoir.get_device_info()}")

    print("\n=== Tests terminés ===")

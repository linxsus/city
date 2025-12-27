"""Tests pour ManoirBlueStacks

Tests unitaires pour la classe ManoirBlueStacks qui gère
le cycle de vie d'une fenêtre BlueStacks via le système états/chemins.
"""

import logging
import sys
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

# Configuration du logging pour voir les logs pendant les tests
# Mettre level=logging.DEBUG pour voir tous les logs
# Mettre level=logging.WARNING pour masquer les logs (par défaut)
LOG_LEVEL = logging.DEBUG  # Changer en logging.WARNING pour désactiver

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Mock des modules de dépendances avant import
# Ces mocks sont nécessaires car les dépendances (mss, cv2, etc.) ne sont pas installées
mock_mss = MagicMock()
mock_mss_tools = MagicMock()
mock_cv2 = MagicMock()
mock_PIL = MagicMock()
mock_PIL_Image = MagicMock()
mock_numpy = MagicMock()
mock_pyautogui = MagicMock()
mock_pywin32_gui = MagicMock()
mock_pywin32_con = MagicMock()
mock_pywin32_api = MagicMock()
mock_pynput = MagicMock()
mock_pynput_keyboard = MagicMock()
mock_pynput_mouse = MagicMock()

# Installer les mocks dans sys.modules
sys.modules["mss"] = mock_mss
sys.modules["mss.tools"] = mock_mss_tools
sys.modules["cv2"] = mock_cv2
sys.modules["PIL"] = mock_PIL
sys.modules["PIL.Image"] = mock_PIL_Image
sys.modules["numpy"] = mock_numpy
sys.modules["pyautogui"] = mock_pyautogui
sys.modules["win32gui"] = mock_pywin32_gui
sys.modules["win32con"] = mock_pywin32_con
sys.modules["win32api"] = mock_pywin32_api
sys.modules["pynput"] = mock_pynput
sys.modules["pynput.keyboard"] = mock_pynput_keyboard
sys.modules["pynput.mouse"] = mock_pynput_mouse

# Maintenant on peut importer les modules du projet
from manoirs.instances.manoir_bluestacks import EtatBlueStacks, ManoirBlueStacks


class ManoirBlueStacksConcret(ManoirBlueStacks):
    """Implémentation concrète pour les tests

    ManoirBlueStacks est abstrait, on doit implémenter gestion_tour().
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gestion_tour_appellee = False
        self.gestion_tour_count = 0

    def gestion_tour(self):
        """Implémentation concrète pour les tests"""
        self.gestion_tour_appellee = True
        self.gestion_tour_count += 1


class TestEtatBlueStacks(unittest.TestCase):
    """Tests pour l'enum EtatBlueStacks"""

    def test_etats_existent(self):
        """Vérifie que tous les états requis existent"""
        self.assertEqual(EtatBlueStacks.EN_COURS.name, "EN_COURS")
        self.assertEqual(EtatBlueStacks.PRET.name, "PRET")
        self.assertEqual(EtatBlueStacks.BLOQUE.name, "BLOQUE")

    def test_etats_valeurs_auto(self):
        """Vérifie que les états ont des valeurs auto distinctes"""
        valeurs = [e.value for e in EtatBlueStacks]
        self.assertEqual(len(valeurs), len(set(valeurs)))  # Pas de doublons


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksInitialisation(unittest.TestCase):
    """Tests d'initialisation de ManoirBlueStacks"""

    def test_init_valeurs_defaut(self, *mocks):
        """Test initialisation avec valeurs par défaut"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        self.assertEqual(manoir.manoir_id, "test")
        self.assertEqual(manoir._etat_interne, EtatBlueStacks.EN_COURS)
        self.assertIsNone(manoir._heure_lancement)
        self.assertFalse(manoir._lancement_initie)
        self.assertEqual(manoir._historique_actions, [])

    def test_init_avec_config(self, *mocks):
        """Test initialisation avec configuration personnalisée"""
        config = {
            "nom": "Test Manoir",
            "titre_bluestacks": "TestWindow",
            "largeur": 800,
            "hauteur": 600,
            "priorite": 75,
            "commande_lancement": ["cmd", "/c", "echo test"],
            "temps_initialisation": 120,
        }

        manoir = ManoirBlueStacksConcret(manoir_id="test_config", config=config)

        self.assertEqual(manoir.nom, "Test Manoir")
        self.assertEqual(manoir.titre_bluestacks, "TestWindow")
        self.assertEqual(manoir.largeur, 800)
        self.assertEqual(manoir.hauteur, 600)
        self.assertEqual(manoir.priorite, 75)
        self.assertEqual(manoir.commande_lancement, ["cmd", "/c", "echo test"])
        self.assertEqual(manoir.temps_initialisation, 120)

    def test_constantes_timeout(self, *mocks):
        """Test que les constantes de timeout sont définies"""
        self.assertEqual(ManoirBlueStacks.TIMEOUT_LANCEMENT, 30 * 60)  # 30 minutes
        self.assertEqual(ManoirBlueStacks.ETAT_DESTINATION, "ville")


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksEtatInterne(unittest.TestCase):
    """Tests pour la gestion de l'état interne"""

    def test_etat_property_getter(self, *mocks):
        """Test du getter de l'état"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        self.assertEqual(manoir.etat, EtatBlueStacks.EN_COURS)

    def test_etat_property_setter(self, *mocks):
        """Test du setter de l'état avec log"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        manoir.etat = EtatBlueStacks.PRET

        self.assertEqual(manoir._etat_interne, EtatBlueStacks.PRET)
        # Vérifie qu'il y a un historique du changement
        self.assertTrue(any("EN_COURS -> PRET" in h for h in manoir._historique_actions))

    def test_etat_setter_meme_valeur(self, *mocks):
        """Test que setter avec la même valeur ne crée pas d'historique"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        nb_historique_initial = len(manoir._historique_actions)

        manoir.etat = EtatBlueStacks.EN_COURS  # Même valeur

        self.assertEqual(len(manoir._historique_actions), nb_historique_initial)

    def test_est_jeu_pret(self, *mocks):
        """Test de la méthode est_jeu_pret()"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        self.assertFalse(manoir.est_jeu_pret())

        manoir.etat = EtatBlueStacks.PRET
        self.assertTrue(manoir.est_jeu_pret())

        manoir.etat = EtatBlueStacks.BLOQUE
        self.assertFalse(manoir.est_jeu_pret())


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksHistorique(unittest.TestCase):
    """Tests pour l'historique des actions"""

    def test_ajouter_historique(self, *mocks):
        """Test d'ajout à l'historique"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        manoir._ajouter_historique("Test message")

        self.assertEqual(len(manoir._historique_actions), 1)
        self.assertIn("Test message", manoir._historique_actions[0])

    def test_historique_avec_timestamp(self, *mocks):
        """Test que l'historique inclut un timestamp"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        manoir._ajouter_historique("Test")

        # Format attendu: [HH:MM:SS] message
        self.assertRegex(manoir._historique_actions[0], r"\[\d{2}:\d{2}:\d{2}\] Test")

    def test_historique_limite_taille(self, *mocks):
        """Test que l'historique est limité à 100 entrées"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        # Ajouter plus de 100 entrées
        for i in range(150):
            manoir._ajouter_historique(f"Message {i}")

        self.assertEqual(len(manoir._historique_actions), 100)
        # Les plus anciens doivent être supprimés
        self.assertIn("Message 149", manoir._historique_actions[-1])
        self.assertNotIn("Message 0", str(manoir._historique_actions))

    def test_get_historique_actions_copie(self, *mocks):
        """Test que get_historique_actions() retourne une copie"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._ajouter_historique("Test")

        historique = manoir.get_historique_actions()
        historique.append("Nouveau")

        self.assertNotIn("Nouveau", manoir._historique_actions)


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksTimeout(unittest.TestCase):
    """Tests pour la gestion du timeout"""

    def test_get_temps_depuis_lancement_non_lance(self, *mocks):
        """Test temps écoulé quand pas encore lancé"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        self.assertEqual(manoir.get_temps_depuis_lancement(), 0)

    def test_get_temps_depuis_lancement_lance(self, *mocks):
        """Test temps écoulé après lancement"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._heure_lancement = time.time() - 60  # Lancé il y a 60 secondes

        temps = manoir.get_temps_depuis_lancement()

        self.assertGreaterEqual(temps, 59)
        self.assertLessEqual(temps, 61)

    def test_est_timeout_atteint_non(self, *mocks):
        """Test timeout non atteint"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._heure_lancement = time.time() - 60  # Seulement 60 secondes

        self.assertFalse(manoir.est_timeout_atteint())

    def test_est_timeout_atteint_oui(self, *mocks):
        """Test timeout atteint"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        # Simuler 31 minutes écoulées (timeout = 30 min)
        manoir._heure_lancement = time.time() - (31 * 60)

        self.assertTrue(manoir.est_timeout_atteint())


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksSilencieuxQuandBloque(unittest.TestCase):
    """Tests pour le comportement silencieux quand bloqué"""

    def test_capture_silencieux_quand_bloque(self, *mocks):
        """Test que capture() retourne None quand bloqué"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._etat_interne = EtatBlueStacks.BLOQUE

        result = manoir.capture()

        self.assertIsNone(result)

    def test_detect_image_silencieux_quand_bloque(self, *mocks):
        """Test que detect_image() retourne False quand bloqué"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._etat_interne = EtatBlueStacks.BLOQUE

        result = manoir.detect_image("template.png")

        self.assertFalse(result)

    def test_find_image_silencieux_quand_bloque(self, *mocks):
        """Test que find_image() retourne None quand bloqué"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._etat_interne = EtatBlueStacks.BLOQUE

        result = manoir.find_image("template.png")

        self.assertIsNone(result)


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksBlocage(unittest.TestCase):
    """Tests pour la gestion du blocage"""

    def test_signaler_blocage(self, *mocks):
        """Test signaler_blocage() change l'état et incrémente erreurs"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        initial_erreurs = manoir._stats["erreurs_detectees"]

        manoir.signaler_blocage()

        self.assertEqual(manoir._etat_interne, EtatBlueStacks.BLOQUE)
        self.assertEqual(manoir._stats["erreurs_detectees"], initial_erreurs + 1)
        self.assertTrue(any("BLOCAGE" in h for h in manoir._historique_actions))

    def test_detecter_erreur(self, *mocks):
        """Test _detecter_erreur() détecte l'état BLOQUE"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        self.assertFalse(manoir._detecter_erreur())

        manoir._etat_interne = EtatBlueStacks.BLOQUE
        self.assertTrue(manoir._detecter_erreur())

    def test_gerer_erreur_appelle_reboot(self, *mocks):
        """Test _gerer_erreur() appelle le reboot"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._etat_interne = EtatBlueStacks.BLOQUE

        with patch.object(manoir, "_reboot_bluestacks") as mock_reboot:
            result = manoir._gerer_erreur()

        mock_reboot.assert_called_once()
        self.assertFalse(result)


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksReboot(unittest.TestCase):
    """Tests pour le reboot"""

    def test_reboot_reset_flags(self, *mocks):
        """Test que reboot reset tous les flags"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._etat_interne = EtatBlueStacks.BLOQUE
        manoir._heure_lancement = time.time()
        manoir._lancement_initie = True
        manoir._ajouter_historique("Test avant reboot")

        manoir._reboot_bluestacks()

        self.assertEqual(manoir._etat_interne, EtatBlueStacks.EN_COURS)
        self.assertIsNone(manoir._heure_lancement)
        self.assertFalse(manoir._lancement_initie)
        self.assertIsNone(manoir._hwnd)
        self.assertIsNone(manoir._rect)
        self.assertIsNone(manoir.etat_actuel)
        # L'historique est vidé puis le changement d'état BLOQUE->EN_COURS est loggué
        self.assertEqual(len(manoir._historique_actions), 1)
        self.assertTrue(any("BLOQUE -> EN_COURS" in h for h in manoir._historique_actions))

    def test_reboot_ferme_fenetre_si_existe(self, *mocks):
        """Test que reboot ferme la fenêtre si elle existe"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._hwnd = 12345  # Fake handle

        with patch.object(manoir._wm, "close_window") as mock_close:
            with patch("time.sleep"):  # Skip sleep
                manoir._reboot_bluestacks()

        mock_close.assert_called_once_with(12345)


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksFenetre(unittest.TestCase):
    """Tests pour la gestion de la fenêtre"""

    def test_est_fenetre_ouverte_non(self, *mocks):
        """Test fenêtre non ouverte"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        with patch.object(manoir, "find_window", return_value=None):
            self.assertFalse(manoir.est_fenetre_ouverte())

    def test_est_fenetre_ouverte_oui(self, *mocks):
        """Test fenêtre ouverte"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        with patch.object(manoir, "find_window", return_value=12345):
            self.assertTrue(manoir.est_fenetre_ouverte())


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksPreparerAlimenterSequence(unittest.TestCase):
    """Tests pour _preparer_alimenter_sequence()"""

    def test_sans_gestionnaire_retourne_false(self, *mocks):
        """Test sans gestionnaire d'états"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._gestionnaire = None

        result = manoir._preparer_alimenter_sequence()

        self.assertFalse(result)

    def test_etat_ville_passe_en_pret(self, *mocks):
        """Test que l'état 'ville' passe le manoir en PRET"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        # Mock le gestionnaire et l'état
        mock_etat = Mock()
        mock_etat.nom = "ville"
        mock_etat.verif = Mock(return_value=True)

        mock_gestionnaire = Mock()
        mock_gestionnaire.determiner_etat_actuel = Mock(return_value=mock_etat)

        manoir._gestionnaire = mock_gestionnaire
        manoir.etat_actuel = mock_etat

        with patch.object(manoir, "activate"):
            result = manoir._preparer_alimenter_sequence()

        self.assertTrue(result)
        self.assertEqual(manoir._etat_interne, EtatBlueStacks.PRET)
        self.assertTrue(manoir.gestion_tour_appellee)

    def test_timeout_passe_en_bloque(self, *mocks):
        """Test que le timeout passe le manoir en BLOQUE"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        # Mock le gestionnaire et un état non-ville
        mock_etat = Mock()
        mock_etat.nom = "chargement"
        mock_etat.verif = Mock(return_value=True)

        mock_gestionnaire = Mock()
        mock_gestionnaire.determiner_etat_actuel = Mock(return_value=mock_etat)
        mock_gestionnaire.trouver_chemin = Mock(return_value=([], False))

        manoir._gestionnaire = mock_gestionnaire
        manoir.etat_actuel = mock_etat

        # Simuler un timeout
        manoir._heure_lancement = time.time() - (35 * 60)  # 35 minutes

        with patch.object(manoir, "sauvegarder_etat_timeout", return_value=None):
            result = manoir._preparer_alimenter_sequence()

        self.assertFalse(result)
        self.assertEqual(manoir._etat_interne, EtatBlueStacks.BLOQUE)


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksGetStatus(unittest.TestCase):
    """Tests pour get_status()"""

    def test_get_status_contenu(self, *mocks):
        """Test que get_status() retourne les infos attendues"""
        manoir = ManoirBlueStacksConcret(
            manoir_id="test", config={"nom": "Test Manoir", "titre_bluestacks": "TestWindow"}
        )

        with patch.object(manoir, "est_fenetre_ouverte", return_value=True):
            status = manoir.get_status()

        self.assertEqual(status["manoir_id"], "test")
        self.assertEqual(status["nom"], "Test Manoir")
        self.assertEqual(status["etat_interne"], "EN_COURS")
        self.assertEqual(status["etat_ecran"], "inconnu")
        self.assertTrue(status["fenetre_ouverte"])
        self.assertFalse(status["jeu_charge"])
        self.assertEqual(status["titre"], "TestWindow")

    def test_get_status_avec_etat_pret(self, *mocks):
        """Test get_status() quand jeu chargé"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._etat_interne = EtatBlueStacks.PRET

        mock_etat = Mock()
        mock_etat.nom = "ville"
        manoir.etat_actuel = mock_etat

        with patch.object(manoir, "est_fenetre_ouverte", return_value=True):
            status = manoir.get_status()

        self.assertEqual(status["etat_interne"], "PRET")
        self.assertEqual(status["etat_ecran"], "ville")
        self.assertTrue(status["jeu_charge"])


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksRepr(unittest.TestCase):
    """Tests pour __repr__()"""

    def test_repr_format(self, *mocks):
        """Test le format de __repr__"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        repr_str = repr(manoir)

        self.assertIn("ManoirBlueStacks", repr_str)
        self.assertIn("test", repr_str)
        self.assertIn("EN_COURS", repr_str)

    def test_repr_avec_etat_ecran(self, *mocks):
        """Test __repr__ avec état écran défini"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        mock_etat = Mock()
        mock_etat.nom = "ville"
        manoir.etat_actuel = mock_etat

        repr_str = repr(manoir)

        self.assertIn("écran=ville", repr_str)


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksReset(unittest.TestCase):
    """Tests pour reset()"""

    def test_reset_flags(self, *mocks):
        """Test que reset() réinitialise les flags BlueStacks"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._lancement_initie = True
        manoir._heure_lancement = time.time()

        manoir.reset()

        self.assertFalse(manoir._lancement_initie)
        self.assertIsNone(manoir._heure_lancement)


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksHookReprise(unittest.TestCase):
    """Tests pour _hook_reprise_changement()"""

    def test_hook_appelle_activate(self, *mocks):
        """Test que le hook appelle activate()"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")

        with patch.object(manoir, "activate") as mock_activate:
            manoir._hook_reprise_changement()

        mock_activate.assert_called_once()


@patch("manoirs.manoir_base.get_slot_manager")
@patch("manoirs.manoir_base.get_timer_manager")
@patch("manoirs.manoir_base.get_window_state_manager")
@patch("manoirs.manoir_base.get_message_bus")
@patch("manoirs.manoir_base.get_window_manager")
@patch("manoirs.manoir_base.get_screen_capture")
@patch("manoirs.manoir_base.get_image_matcher")
@patch("manoirs.manoir_base.get_color_detector")
@patch("manoirs.manoir_base.get_ocr_engine")
class TestManoirBlueStacksSauvegarderTimeout(unittest.TestCase):
    """Tests pour sauvegarder_etat_timeout()"""

    def test_sauvegarde_screenshot(self, *mocks):
        """Test que le timeout sauvegarde un screenshot"""
        manoir = ManoirBlueStacksConcret(manoir_id="test")
        manoir._heure_lancement = time.time() - 1800
        manoir._ajouter_historique("Action test")

        with patch.object(
            manoir, "save_capture", return_value="/path/to/screenshot.png"
        ) as mock_save:
            result = manoir.sauvegarder_etat_timeout()

        mock_save.assert_called_once_with(suffix="_TIMEOUT")
        self.assertEqual(result, "/path/to/screenshot.png")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
Test d'intégration du système d'états/chemins avec ManoirBase

Pour exécuter : python test_integration_etats.py
Pour supprimer : simplement supprimer ce fichier
"""
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent))

from typing import List, Any
from core.etat import Etat
from core.chemin import Chemin
from core.gestionnaire_etats import GestionnaireEtats
from core.exceptions import AucunEtatTrouve
from actions.action_reprise_preparer_tour import ActionReprisePreparerTour


# ============================================================
# ÉTATS DE TEST (simulés)
# ============================================================

class EtatVilleTest(Etat):
    """État : écran ville"""
    nom = "ville_test"
    groupes = ["ecran_principal"]

    # Simule si on est dans cet état
    _actif = False

    def verif(self, manoir) -> bool:
        return EtatVilleTest._actif


class EtatCarteTest(Etat):
    """État : écran carte"""
    nom = "carte_test"
    groupes = ["ecran_principal"]

    _actif = False

    def verif(self, manoir) -> bool:
        return EtatCarteTest._actif


class EtatPopupTest(Etat):
    """État : popup"""
    nom = "popup_test"
    groupes = ["popup"]

    _actif = False

    def verif(self, manoir) -> bool:
        return EtatPopupTest._actif


# ============================================================
# CHEMINS DE TEST (simulés)
# ============================================================

class ActionTest:
    """Action factice pour les tests"""
    def __init__(self, nom: str):
        self.nom = nom
        self.executee = False

    def condition(self):
        return True

    def execute(self):
        self.executee = True
        print(f"    [ACTION] {self.nom} exécutée")
        return True


class CheminVilleVersCarte(Chemin):
    """Chemin : ville → carte (certain)"""
    etat_initial = "ville_test"
    etat_sortie = "carte_test"

    def fonction_actions(self, manoir) -> List[Any]:
        return [
            ActionTest("Clic bouton carte"),
            ActionTest("Attendre chargement"),
        ]


class CheminCarteVersVille(Chemin):
    """Chemin : carte → ville (certain)"""
    etat_initial = "carte_test"
    etat_sortie = "ville_test"

    def fonction_actions(self, manoir) -> List[Any]:
        return [
            ActionTest("Clic bouton retour"),
        ]


class CheminVilleVersPopup(Chemin):
    """Chemin : ville → popup (incertain - peut échouer)"""
    etat_initial = "ville_test"
    etat_sortie = ["popup_test", "ville_test"]  # Sortie incertaine

    def fonction_actions(self, manoir) -> List[Any]:
        return [
            ActionTest("Clic bouton ouvrir popup"),
        ]


# ============================================================
# MANOIR DE TEST (simulé)
# ============================================================

class SequenceTest:
    """Séquence d'actions simulée"""
    def __init__(self):
        self._actions = []
        self._index = 0

    def ajouter(self, action):
        self._actions.append(action)

    def clear(self):
        self._actions.clear()
        self._index = 0

    def is_end(self):
        return self._index >= len(self._actions)

    def __iter__(self):
        return iter(self._actions)

    def __next__(self):
        if self._index < len(self._actions):
            action = self._actions[self._index]
            self._index += 1
            return action
        raise StopIteration


class ManoirTest:
    """Manoir simulé pour les tests"""
    def __init__(self):
        self.nom = "ManoirTest"
        self.sequence = SequenceTest()
        self._gestionnaire = None
        self.etat_actuel = None
        self._logs = []

    def log(self, msg):
        self._logs.append(msg)
        print(f"  [MANOIR] {msg}")

    # --- Méthodes copiées de ManoirBase ---

    def set_gestionnaire(self, gestionnaire):
        self._gestionnaire = gestionnaire
        self.log("Gestionnaire injecté")

    def verifier_etat(self) -> bool:
        if self._gestionnaire is None:
            self.log("ERREUR: Gestionnaire non configuré")
            return False

        if self.etat_actuel is None:
            return self._determiner_et_stocker_etat()

        if self.etat_actuel.verif(self):
            self.log(f"État vérifié: {self.etat_actuel.nom}")
            return True

        self.log(f"État {self.etat_actuel.nom} incorrect, redétermination...")
        return self._determiner_et_stocker_etat()

    def _determiner_et_stocker_etat(self) -> bool:
        try:
            self.etat_actuel = self._gestionnaire.determiner_etat_actuel(self)
            self.log(f"État déterminé: {self.etat_actuel.nom}")
            return True
        except AucunEtatTrouve:
            self.log("ERREUR: Aucun état trouvé")
            self.etat_actuel = None
            return False

    def naviguer_vers(self, destination) -> bool:
        if self._gestionnaire is None:
            self.log("ERREUR: Gestionnaire non configuré")
            return False

        if self.etat_actuel is None:
            self.log("ERREUR: État actuel inconnu")
            return False

        chemins, complet = self._gestionnaire.trouver_chemin(
            self.etat_actuel, destination
        )

        if not chemins:
            dest_nom = destination if isinstance(destination, str) else destination.nom
            self.log(f"ERREUR: Aucun chemin vers {dest_nom}")
            return False

        chemin = chemins[0]
        actions = chemin.generer_actions(self)

        for action in actions:
            self.sequence.ajouter(action)

        self.log(f"Navigation: {chemin} ({len(actions)} actions)")

        if not complet:
            # Vérifier si déjà une ActionReprise
            has_reprise = any(isinstance(a, ActionReprisePreparerTour) for a in self.sequence)
            if not has_reprise:
                self.sequence.ajouter(ActionReprisePreparerTour(self))
                self.log("Chemin incomplet → ActionReprisePreparerTour ajoutée")
            return False

        if chemin.etat_sortie is not None and hasattr(chemin.etat_sortie, 'nom'):
            self.etat_actuel = chemin.etat_sortie

        return True


# ============================================================
# GESTIONNAIRE DE TEST
# ============================================================

class GestionnaireTest:
    """Gestionnaire simplifié pour les tests (sans fichiers)"""

    def __init__(self):
        self._etats = {}
        self._chemins = []
        self._priorites = ["popup_test", "ville_test", "carte_test"]

    def ajouter_etat(self, etat: Etat):
        self._etats[etat.nom] = etat

    def ajouter_chemin(self, chemin: Chemin):
        self._chemins.append(chemin)
        # Résoudre les références
        chemin.etat_initial = self._etats.get(chemin.etat_initial, chemin.etat_initial)
        if isinstance(chemin.etat_sortie, str):
            chemin.etat_sortie = self._etats.get(chemin.etat_sortie, chemin.etat_sortie)
        elif isinstance(chemin.etat_sortie, list):
            chemin.etat_sortie = [
                self._etats.get(e, e) if isinstance(e, str) else e
                for e in chemin.etat_sortie
            ]

    def determiner_etat_actuel(self, manoir) -> Etat:
        # Tester par ordre de priorité
        for nom in self._priorites:
            if nom in self._etats:
                etat = self._etats[nom]
                if etat.verif(manoir):
                    return etat

        # Tester les autres
        for etat in self._etats.values():
            if etat.verif(manoir):
                return etat

        raise AucunEtatTrouve("Aucun état trouvé")

    def trouver_chemin(self, depart, arrivee):
        """Recherche simple (pas de BFS complet)"""
        depart_nom = depart.nom if hasattr(depart, 'nom') else depart
        arrivee_nom = arrivee.nom if hasattr(arrivee, 'nom') else arrivee

        for chemin in self._chemins:
            initial_nom = chemin.etat_initial.nom if hasattr(chemin.etat_initial, 'nom') else chemin.etat_initial

            if initial_nom == depart_nom:
                # Vérifier sortie
                if isinstance(chemin.etat_sortie, list):
                    sorties = [e.nom if hasattr(e, 'nom') else e for e in chemin.etat_sortie]
                    if arrivee_nom in sorties:
                        return ([chemin], False)  # Incertain
                elif hasattr(chemin.etat_sortie, 'nom'):
                    if chemin.etat_sortie.nom == arrivee_nom:
                        return ([chemin], True)  # Certain

        return ([], False)


# ============================================================
# TESTS
# ============================================================

def test_1_determiner_etat():
    """Test 1: Détermination de l'état actuel"""
    print("\n" + "="*60)
    print("TEST 1: Détermination de l'état actuel")
    print("="*60)

    # Reset états
    EtatVilleTest._actif = False
    EtatCarteTest._actif = False
    EtatPopupTest._actif = False

    # Créer gestionnaire et manoir
    gestionnaire = GestionnaireTest()
    gestionnaire.ajouter_etat(EtatVilleTest())
    gestionnaire.ajouter_etat(EtatCarteTest())
    gestionnaire.ajouter_etat(EtatPopupTest())

    manoir = ManoirTest()
    manoir.set_gestionnaire(gestionnaire)

    # Test 1a: Aucun état actif
    print("\n[Test 1a] Aucun état actif:")
    result = manoir.verifier_etat()
    assert result == False, "Devrait échouer si aucun état"
    print("  ✓ Correct: aucun état trouvé")

    # Test 1b: Ville active
    print("\n[Test 1b] Ville active:")
    EtatVilleTest._actif = True
    result = manoir.verifier_etat()
    assert result == True, "Devrait trouver ville"
    assert manoir.etat_actuel.nom == "ville_test"
    print("  ✓ Correct: état ville_test trouvé")

    # Test 1c: Vérification sans changement
    print("\n[Test 1c] Vérification état inchangé:")
    result = manoir.verifier_etat()
    assert result == True
    print("  ✓ Correct: état toujours valide")

    # Test 1d: Changement d'état (ville → carte)
    print("\n[Test 1d] Changement d'état:")
    EtatVilleTest._actif = False
    EtatCarteTest._actif = True
    result = manoir.verifier_etat()
    assert result == True
    assert manoir.etat_actuel.nom == "carte_test"
    print("  ✓ Correct: état carte_test détecté")

    print("\n✓ TEST 1 RÉUSSI")
    return True


def test_2_navigation_simple():
    """Test 2: Navigation avec chemin certain"""
    print("\n" + "="*60)
    print("TEST 2: Navigation avec chemin certain")
    print("="*60)

    # Reset
    EtatVilleTest._actif = True
    EtatCarteTest._actif = False

    # Setup
    gestionnaire = GestionnaireTest()
    gestionnaire.ajouter_etat(EtatVilleTest())
    gestionnaire.ajouter_etat(EtatCarteTest())
    gestionnaire.ajouter_chemin(CheminVilleVersCarte())
    gestionnaire.ajouter_chemin(CheminCarteVersVille())

    manoir = ManoirTest()
    manoir.set_gestionnaire(gestionnaire)
    manoir.verifier_etat()

    print(f"\n[État initial] {manoir.etat_actuel.nom}")

    # Navigation ville → carte
    print("\n[Navigation] ville → carte:")
    result = manoir.naviguer_vers("carte_test")

    assert result == True, "Chemin devrait être complet"
    assert len(list(manoir.sequence)) == 2, "Devrait avoir 2 actions"

    # Vérifier les actions
    print("\n[Actions dans la séquence]:")
    for action in manoir.sequence:
        print(f"  - {action.nom}")

    # Pas de ActionReprisePreparerTour
    has_reprise = any(isinstance(a, ActionReprisePreparerTour) for a in manoir.sequence)
    assert not has_reprise, "Pas de reprise pour chemin certain"

    print("\n✓ TEST 2 RÉUSSI")
    return True


def test_3_navigation_incertaine():
    """Test 3: Navigation avec chemin incertain"""
    print("\n" + "="*60)
    print("TEST 3: Navigation avec chemin incertain")
    print("="*60)

    # Reset
    EtatVilleTest._actif = True
    EtatPopupTest._actif = False

    # Setup
    gestionnaire = GestionnaireTest()
    gestionnaire.ajouter_etat(EtatVilleTest())
    gestionnaire.ajouter_etat(EtatPopupTest())
    gestionnaire.ajouter_chemin(CheminVilleVersPopup())

    manoir = ManoirTest()
    manoir.set_gestionnaire(gestionnaire)
    manoir.verifier_etat()

    print(f"\n[État initial] {manoir.etat_actuel.nom}")

    # Navigation ville → popup (incertain)
    print("\n[Navigation] ville → popup (incertain):")
    result = manoir.naviguer_vers("popup_test")

    assert result == False, "Chemin devrait être incomplet"

    # Vérifier ActionReprisePreparerTour
    actions = list(manoir.sequence)
    print("\n[Actions dans la séquence]:")
    for action in actions:
        nom = getattr(action, 'nom', action.__class__.__name__)
        print(f"  - {nom}")

    has_reprise = any(isinstance(a, ActionReprisePreparerTour) for a in actions)
    assert has_reprise, "Devrait avoir ActionReprisePreparerTour"

    # Vérifier que ActionReprise est en dernier
    last_action = actions[-1]
    assert isinstance(last_action, ActionReprisePreparerTour), "ActionReprise doit être en dernier"

    # Vérifier le flag demande_reprise
    assert last_action.demande_reprise == True, "Flag demande_reprise doit être True"

    print("\n✓ TEST 3 RÉUSSI")
    return True


def test_4_pas_de_double_reprise():
    """Test 4: Pas de double ActionReprisePreparerTour"""
    print("\n" + "="*60)
    print("TEST 4: Pas de double ActionReprisePreparerTour")
    print("="*60)

    # Reset
    EtatVilleTest._actif = True

    # Setup
    gestionnaire = GestionnaireTest()
    gestionnaire.ajouter_etat(EtatVilleTest())
    gestionnaire.ajouter_etat(EtatPopupTest())
    gestionnaire.ajouter_chemin(CheminVilleVersPopup())

    manoir = ManoirTest()
    manoir.set_gestionnaire(gestionnaire)
    manoir.verifier_etat()

    # Première navigation
    print("\n[1ère navigation]:")
    manoir.naviguer_vers("popup_test")
    count1 = sum(1 for a in manoir.sequence if isinstance(a, ActionReprisePreparerTour))
    print(f"  ActionReprise count: {count1}")

    # Deuxième appel (simule un bug potentiel)
    print("\n[2ème navigation (même destination)]:")
    manoir.naviguer_vers("popup_test")
    count2 = sum(1 for a in manoir.sequence if isinstance(a, ActionReprisePreparerTour))
    print(f"  ActionReprise count: {count2}")

    assert count2 == 1, "Ne devrait avoir qu'une seule ActionReprise"

    print("\n✓ TEST 4 RÉUSSI")
    return True


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "#"*60)
    print("# TESTS D'INTÉGRATION - SYSTÈME ÉTATS/CHEMINS")
    print("#"*60)

    tests = [
        test_1_determiner_etat,
        test_2_navigation_simple,
        test_3_navigation_incertaine,
        test_4_pas_de_double_reprise,
    ]

    resultats = []
    for test in tests:
        try:
            result = test()
            resultats.append((test.__name__, result))
        except Exception as e:
            print(f"\n✗ ERREUR: {e}")
            resultats.append((test.__name__, False))

    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)

    for nom, succes in resultats:
        status = "✓" if succes else "✗"
        print(f"  {status} {nom}")

    total_ok = sum(1 for _, s in resultats if s)
    total = len(resultats)

    print(f"\nTotal: {total_ok}/{total} tests réussis")

    if total_ok == total:
        print("\n" + "="*60)
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        print("="*60)

    return total_ok == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

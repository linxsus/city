"""
GestionnaireEtats - Composant central du système de gestion d'états et chemins.

Gère le graphe d'états, le pathfinding et la détermination d'état.
"""

import os
import importlib
import importlib.util
from typing import Dict, List, Tuple, Union, Optional, Any
from collections import deque
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from core.etat import Etat, SingletonMeta
from core.etat_inconnu import EtatInconnu
from core.chemin import Chemin
from core.exceptions import (
    ErreurConfiguration,
    ErreurValidation,
    EtatInconnuException,
    AucunEtatTrouve
)
from utils.logger import get_module_logger


class GestionnaireEtats:
    """
    Composant central gérant le graphe d'états, le pathfinding et la détermination d'état.

    Attributes:
        _etats: Dictionnaire nom → instance Etat
        _chemins: Liste de tous les chemins enregistrés
        _priorites: Ordre de priorité des noms d'états pour les tests
        _logger: Logger du module
        _config: Configuration chargée du fichier TOML
    """

    def __init__(self, chemin_config: str):
        """
        Initialise le gestionnaire, scan les états/chemins, charge la config.

        Args:
            chemin_config: Chemin vers fichier TOML de configuration

        Raises:
            ErreurConfiguration: Si le fichier TOML est invalide
            ErreurValidation: Si noms dupliqués ou références invalides
        """
        self._logger = get_module_logger('GestionnaireEtats')
        self._etats: Dict[str, Etat] = {}
        self._chemins: List[Chemin] = []
        self._priorites: List[str] = []
        self._config: Dict[str, Any] = {}

        self._base_path = Path(chemin_config).parent.parent

        self._charger_configuration(chemin_config)
        self._scanner_etats()
        self._scanner_chemins()
        self._resoudre_references()
        self._valider_coherence()

    def _charger_configuration(self, chemin_config: str) -> None:
        """Charge la configuration depuis le fichier TOML."""
        try:
            with open(chemin_config, 'rb') as f:
                self._config = tomllib.load(f)

            if 'priorites' in self._config:
                self._priorites = self._config['priorites'].get('ordre', [])

            if 'logging' in self._config:
                niveau = self._config['logging'].get('niveau', 'INFO')
                self._logger = get_module_logger('GestionnaireEtats', niveau)

            self._logger.info(f"Configuration chargée: {chemin_config}")

        except FileNotFoundError:
            raise ErreurConfiguration(f"Fichier de configuration introuvable: {chemin_config}")
        except Exception as e:
            raise ErreurConfiguration(f"Erreur lors du chargement de la configuration: {e}")

    def _scanner_etats(self) -> None:
        """Scanne le répertoire 'etats/' et instancie toutes les classes Etat."""
        repertoire_etats = self._base_path / 'etats'

        if not repertoire_etats.exists():
            self._logger.warning(f"Répertoire des états introuvable: {repertoire_etats}")
            return

        instances = self._scanner_modules(str(repertoire_etats), Etat)

        for instance in instances:
            if instance.nom in self._etats:
                raise ErreurValidation(f"Nom d'état dupliqué: {instance.nom}")
            self._etats[instance.nom] = instance

        self._logger.info(f"Scan du répertoire 'etats/': {len(self._etats)} états trouvés")

    def _scanner_chemins(self) -> None:
        """Scanne le répertoire 'chemins/' et instancie toutes les classes Chemin."""
        repertoire_chemins = self._base_path / 'chemins'

        if not repertoire_chemins.exists():
            self._logger.warning(f"Répertoire des chemins introuvable: {repertoire_chemins}")
            return

        self._chemins = self._scanner_modules(str(repertoire_chemins), Chemin)
        self._logger.info(f"Scan du répertoire 'chemins/': {len(self._chemins)} chemins trouvés")

    def _scanner_modules(self, repertoire: str, classe_base: type) -> List[Any]:
        """
        Scanne un répertoire et instancie les classes héritant de classe_base.

        Args:
            repertoire: Chemin du répertoire à scanner
            classe_base: Classe dont doivent hériter les classes trouvées

        Returns:
            Liste d'instances des classes trouvées
        """
        instances = []
        repertoire_path = Path(repertoire)

        for fichier in repertoire_path.glob('*.py'):
            if fichier.name.startswith('__'):
                continue

            try:
                module_name = fichier.stem
                spec = importlib.util.spec_from_file_location(module_name, fichier)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)

                    if (isinstance(attr, type) and
                        issubclass(attr, classe_base) and
                        attr is not classe_base and
                        attr is not Etat and
                        attr is not EtatInconnu and
                        attr is not Chemin):
                        try:
                            instance = attr()
                            instances.append(instance)
                        except Exception as e:
                            self._logger.warning(f"Erreur d'instanciation {attr_name}: {e}")

            except Exception as e:
                self._logger.warning(f"Import échoué: {fichier.name} ({e})")

        return instances

    def _resoudre_references(self) -> None:
        """Résout toutes les références (string/classe → instance) dans les chemins."""
        for chemin in self._chemins:
            chemin.etat_initial = self._resoudre_reference(chemin.etat_initial)

            if chemin.etat_sortie is not None:
                if isinstance(chemin.etat_sortie, list):
                    chemin.etat_sortie = [
                        self._resoudre_reference(e) for e in chemin.etat_sortie
                    ]
                else:
                    chemin.etat_sortie = self._resoudre_reference(chemin.etat_sortie)

        for nom, etat in self._etats.items():
            if isinstance(etat, EtatInconnu) and etat.etats_possibles:
                etat.etats_possibles = [
                    self._resoudre_reference(e) for e in etat.etats_possibles
                ]

    def _resoudre_reference(self, ref: Union[Etat, str, type]) -> Etat:
        """
        Résout une référence en instance d'Etat.

        Args:
            ref: Référence (string, classe ou instance)

        Returns:
            Instance d'Etat correspondante

        Raises:
            ErreurValidation: Si la référence est invalide
        """
        if isinstance(ref, Etat):
            return ref

        if isinstance(ref, str):
            if ref in self._etats:
                return self._etats[ref]
            raise ErreurValidation(f"État inexistant: {ref}")

        if isinstance(ref, type) and issubclass(ref, Etat):
            for etat in self._etats.values():
                if isinstance(etat, ref):
                    return etat
            raise ErreurValidation(f"Classe d'état non enregistrée: {ref.__name__}")

        raise ErreurValidation(f"Type de référence invalide: {type(ref)}")

    def _valider_coherence(self) -> None:
        """Valide la cohérence du système (noms uniques, références valides)."""
        noms_vus = set()
        for nom in self._etats.keys():
            if nom in noms_vus:
                raise ErreurValidation(f"Nom d'état dupliqué: {nom}")
            noms_vus.add(nom)

        for priorite in self._priorites:
            if priorite not in self._etats:
                self._logger.warning(f"État dans priorités mais non trouvé: {priorite}")

    def trouver_chemin(
        self,
        etat_depart: Union[Etat, str],
        etat_arrivee: Union[Etat, str]
    ) -> Tuple[List[Chemin], bool]:
        """
        Trouve le plus court chemin entre deux états.

        Args:
            etat_depart: État de départ (instance ou nom)
            etat_arrivee: État d'arrivée (instance ou nom)

        Returns:
            Tuple (liste_chemins, chemin_complet):
                - liste_chemins: Séquence ordonnée de Chemin à exécuter
                - chemin_complet: True = complet, False = partiel (incertitude)

        Raises:
            EtatInconnuException: Si etat_depart ou etat_arrivee n'existe pas
        """
        try:
            depart = self._resoudre_reference(etat_depart)
            arrivee = self._resoudre_reference(etat_arrivee)
        except ErreurValidation as e:
            raise EtatInconnuException(str(e))

        self._logger.debug(f"Pathfinding: {depart.nom} → {arrivee.nom}")

        graphe_certain = self._construire_graphe(seulement_certains=True)
        chemin = self._bfs_plus_court_chemin(graphe_certain, depart, arrivee)

        if chemin is not None:
            self._logger.debug(f"Chemin trouvé: {' → '.join(c.etat_initial.nom for c in chemin)} → {arrivee.nom} ({len(chemin)} étapes)")
            return (chemin, True)

        graphe_complet = self._construire_graphe(seulement_certains=False)
        chemin = self._bfs_plus_court_chemin(graphe_complet, depart, arrivee)

        if chemin is not None:
            chemin_partiel = []
            for c in chemin:
                chemin_partiel.append(c)
                if not c.est_certain():
                    self._logger.debug(f"Chemin partiel: s'arrête à {c} (incertain)")
                    return (chemin_partiel, False)

            return (chemin_partiel, True)

        return ([], False)

    def _construire_graphe(self, seulement_certains: bool = False) -> Dict[Etat, List[Chemin]]:
        """
        Construit le graphe pour le pathfinding.

        Args:
            seulement_certains: True = ignorer chemins incertains

        Returns:
            Map associant chaque état aux chemins partant de cet état
        """
        graphe: Dict[Etat, List[Chemin]] = {}

        for chemin in self._chemins:
            if seulement_certains and not chemin.est_certain():
                continue

            etat_depart = chemin.etat_initial

            if etat_depart not in graphe:
                graphe[etat_depart] = []

            graphe[etat_depart].append(chemin)

        return graphe

    def _bfs_plus_court_chemin(
        self,
        graphe: Dict[Etat, List[Chemin]],
        depart: Etat,
        arrivee: Etat
    ) -> Optional[List[Chemin]]:
        """
        Algorithme BFS pour trouver le plus court chemin.

        Args:
            graphe: Pour chaque état, liste des chemins sortants
            depart: État de départ
            arrivee: État d'arrivée

        Returns:
            Liste ordonnée de Chemin formant le plus court chemin, ou None
        """
        max_profondeur = self._config.get('pathfinding', {}).get('max_profondeur', 20)

        file: deque = deque()
        file.append((depart, []))
        visites = set()

        while file:
            etat_actuel, chemin_parcouru = file.popleft()

            if len(chemin_parcouru) > max_profondeur:
                continue

            if etat_actuel in visites:
                continue

            visites.add(etat_actuel)

            if etat_actuel == arrivee:
                return chemin_parcouru

            chemins_sortants = graphe.get(etat_actuel, [])

            for chemin in chemins_sortants:
                etats_suivants = self._obtenir_etats_sortie(chemin)

                for etat_suivant in etats_suivants:
                    if etat_suivant not in visites:
                        nouveau_chemin = chemin_parcouru + [chemin]
                        file.append((etat_suivant, nouveau_chemin))

        return None

    def _obtenir_etats_sortie(self, chemin: Chemin) -> List[Etat]:
        """
        Obtient les états de sortie possibles d'un chemin.

        Args:
            chemin: Le chemin à analyser

        Returns:
            Liste des états de sortie possibles
        """
        if chemin.etat_sortie is None:
            return list(self._etats.values())

        if isinstance(chemin.etat_sortie, list):
            return chemin.etat_sortie

        if isinstance(chemin.etat_sortie, EtatInconnu):
            if not chemin.etat_sortie.etats_possibles:
                return list(self._etats.values())
            return chemin.etat_sortie.etats_possibles

        if isinstance(chemin.etat_sortie, Etat):
            return [chemin.etat_sortie]

        return []

    def determiner_etat_actuel(
        self,
        liste_etats: Optional[List[Union[Etat, str]]] = None
    ) -> Etat:
        """
        Teste les états pour déterminer l'état actuel du système.

        Args:
            liste_etats: Liste d'états à tester (None = tous les états)

        Returns:
            Instance Etat correspondant à l'état actuel

        Raises:
            AucunEtatTrouve: Si aucun état ne correspond et pas d'EtatInconnuGlobal
            EtatInconnuException: Si un nom d'état dans liste_etats n'existe pas
        """
        if liste_etats is None:
            etats_a_tester = list(self._etats.values())
        else:
            etats_a_tester = []
            for e in liste_etats:
                try:
                    etats_a_tester.append(self._resoudre_reference(e))
                except ErreurValidation as err:
                    raise EtatInconnuException(str(err))

        etats_a_tester = [e for e in etats_a_tester if not isinstance(e, EtatInconnu)]

        def priorite_key(etat: Etat) -> Tuple[int, str]:
            try:
                idx = self._priorites.index(etat.nom)
                return (0, idx)
            except ValueError:
                return (1, etat.nom)

        etats_a_tester.sort(key=lambda e: priorite_key(e))

        for etat in etats_a_tester:
            if etat.verif():
                self._logger.info(f"État actuel déterminé: {etat.nom}")
                return etat

        for etat in self._etats.values():
            if isinstance(etat, EtatInconnu) and not etat.etats_possibles:
                self._logger.info(f"État actuel: {etat.nom} (fallback EtatInconnuGlobal)")
                return etat

        raise AucunEtatTrouve("Aucun état ne correspond et pas d'EtatInconnuGlobal configuré")

    def obtenir_etat(self, nom: str) -> Etat:
        """
        Récupère une instance d'état par son nom.

        Args:
            nom: Nom de l'état à récupérer

        Returns:
            Instance Etat

        Raises:
            EtatInconnuException: Si nom invalide
        """
        if nom not in self._etats:
            raise EtatInconnuException(f"État inconnu: {nom}")
        return self._etats[nom]

    def obtenir_chemins_depuis(self, etat: Union[Etat, str]) -> List[Chemin]:
        """
        Liste tous les chemins partant d'un état.

        Args:
            etat: État de départ (instance ou nom)

        Returns:
            Liste de Chemin ayant etat comme etat_initial
        """
        etat_instance = self._resoudre_reference(etat)
        return [c for c in self._chemins if c.etat_initial == etat_instance]

    def obtenir_chemins_vers(self, etat: Union[Etat, str]) -> List[Chemin]:
        """
        Liste tous les chemins arrivant à un état.

        Args:
            etat: État d'arrivée (instance ou nom)

        Returns:
            Liste de Chemin ayant etat comme etat_sortie possible
        """
        etat_instance = self._resoudre_reference(etat)
        chemins_vers = []

        for chemin in self._chemins:
            etats_sortie = self._obtenir_etats_sortie(chemin)
            if etat_instance in etats_sortie:
                chemins_vers.append(chemin)

        return chemins_vers

    @property
    def etats(self) -> Dict[str, Etat]:
        """Retourne le dictionnaire des états enregistrés."""
        return self._etats.copy()

    @property
    def chemins(self) -> List[Chemin]:
        """Retourne la liste des chemins enregistrés."""
        return self._chemins.copy()

# -*- coding: utf-8 -*-
"""Point d'entrée principal de l'automatisation Mafia City

Usage:
    python main.py                  # Démarrer l'automatisation
    python main.py --dry-run        # Mode simulation (pas d'actions réelles)
    python main.py --manoirs m1,m2  # Seulement certains manoirs
    python main.py --list           # Lister les manoirs disponibles
    python main.py --status         # Afficher le statut
    python main.py --test           # Lancer les tests
"""
import sys
import argparse
import time
import signal
from pathlib import Path

# Ajouter le dossier au path si exécuté directement
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logging, get_module_logger
from utils.config import init_directories
from core.engine import get_engine, EtatEngine
from manoirs.config_manoirs import (
    MANOIRS_CONFIG,
    get_all_manoir_ids,
    get_config,
)

logger = get_module_logger("Main")


# =============================================================================
# FACTORY DE MANOIRS
# =============================================================================

def creer_manoir(manoir_id):
    """Crée un manoir selon son type dans la configuration

    Args:
        manoir_id: Identifiant du manoir

    Returns:
        Instance de manoir ou None si type inconnu
    """
    config = get_config(manoir_id)
    if not config:
        logger.error(f"Configuration non trouvée pour: {manoir_id}")
        return None

    type_manoir = config.get('type', 'virtuel')

    if type_manoir == 'bluestacks':
        from manoirs.instances.manoir_bluestacks import ManoirBlueStacks
        # ManoirBlueStacks est abstrait, il faut une sous-classe concrète
        # Pour l'instant on log une erreur
        logger.error(f"ManoirBlueStacks est abstrait, créez une sous-classe pour: {manoir_id}")
        return None

    elif type_manoir == 'principal':
        from manoirs.instances.manoir_principal import ManoirPrincipal
        return ManoirPrincipal(manoir_id, config)

    elif type_manoir == 'virtuel':
        from manoirs.instances.manoir_virtuel import ManoirVirtuel
        return ManoirVirtuel(manoir_id, config)

    else:
        logger.warning(f"Type de manoir inconnu: {type_manoir}, utilisation de ManoirVirtuel")
        from manoirs.instances.manoir_virtuel import ManoirVirtuel
        return ManoirVirtuel(manoir_id, config)


def creer_tous_manoirs(manoir_ids=None):
    """Crée tous les manoirs configurés

    Args:
        manoir_ids: Liste optionnelle d'IDs à créer (None = tous)

    Returns:
        dict: Dictionnaire {manoir_id: manoir}
    """
    if manoir_ids is None:
        manoir_ids = get_all_manoir_ids()

    manoirs = {}

    for manoir_id in manoir_ids:
        manoir = creer_manoir(manoir_id)
        if manoir:
            manoirs[manoir_id] = manoir
            logger.info(f"Manoir créé: {manoir_id} ({type(manoir).__name__})")

    return manoirs


# =============================================================================
# COMMANDES
# =============================================================================

def parse_args():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Automatisation Mafia City",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python main.py                     Démarrer l'automatisation
  python main.py --manoirs farm1,farm2   Seulement farm1 et farm2
  python main.py --dry-run           Mode simulation
  python main.py --list              Lister les manoirs
  python main.py --test              Lancer les tests
        """
    )

    parser.add_argument(
        '--manoirs', '-m',
        type=str,
        help='Liste des manoirs à automatiser (séparées par des virgules)'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Mode simulation (pas d\'actions réelles)'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='Lister les manoirs disponibles'
    )

    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Afficher le statut actuel'
    )

    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Lancer les tests'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Afficher plus de détails (niveau DEBUG)'
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Chemin vers un fichier de configuration JSON'
    )

    return parser.parse_args()


def lister_manoirs():
    """Affiche la liste des manoirs configurés"""
    print("\n" + "=" * 60)
    print(" MANOIRS CONFIGURÉS")
    print("=" * 60)

    for mid in get_all_manoir_ids():
        config = get_config(mid)
        type_man = config.get('type', 'inconnu')
        nom = config.get('nom', mid)
        titre = config.get('titre_bluestacks', 'N/A')
        priorite = config.get('priorite', 0)
        niveau = config.get('niveau_manoir', 'N/A')

        print(f"\n  [{mid}]")
        print(f"    Nom:       {nom}")
        print(f"    Type:      {type_man}")
        print(f"    BlueStacks: {titre}")
        print(f"    Priorité:  {priorite}")
        print(f"    Manoir:    {niveau}")

    print("\n" + "=" * 60)


def afficher_status():
    """Affiche le statut actuel"""
    from core.window_state_manager import get_window_state_manager
    from core.timer_manager import get_timer_manager
    from core.slot_manager import get_slot_manager

    wsm = get_window_state_manager()
    tm = get_timer_manager()
    sm = get_slot_manager()

    print("\n" + "=" * 60)
    print(" STATUT ACTUEL")
    print("=" * 60)

    for mid in get_all_manoir_ids():
        state = wsm.get_state(mid)

        print(f"\n  [{mid}]")

        if state:
            print(f"    État:     {state.etat.name}")
            if state.time_until_available() > 0:
                print(f"    Dispo dans: {state.time_until_available():.0f}s")

        # Slots
        free = sm.count_free_slots(mid)
        total = len(sm.get_available_slots(mid)) + free
        print(f"    Slots:    {free}/{total} libres")

        # Timers dus
        timers_dus = tm.get_due_timers(mid)
        if timers_dus:
            print(f"    Timers dus: {[t.nom for t in timers_dus]}")

    print("\n" + "=" * 60)


def lancer_tests():
    """Lance tous les tests"""
    import subprocess
    
    print("\n" + "=" * 60)
    print(" LANCEMENT DES TESTS")
    print("=" * 60 + "\n")
    
    tests_dir = Path(__file__).parent / "tests"
    
    for test_file in sorted(tests_dir.glob("test_phase*.py")):
        print(f"\n>>> {test_file.name}")
        print("-" * 40)
        
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=False
        )
        
        if result.returncode != 0:
            print(f"ÉCHEC: {test_file.name}")
            return False
    
    print("\n" + "=" * 60)
    print(" TOUS LES TESTS PASSÉS ✓")
    print("=" * 60)
    
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Fonction principale"""
    args = parse_args()

    # Initialiser le logging
    log_level = 'DEBUG' if args.verbose else 'DEBUG'
    setup_logging(level=log_level)

    # Initialiser les dossiers
    init_directories()

    # Commandes spéciales
    if args.list:
        lister_manoirs()
        return 0

    if args.status:
        afficher_status()
        return 0

    if args.test:
        success = lancer_tests()
        return 0 if success else 1

    # Charger la configuration personnalisée si fournie
    if args.config:
        from manoirs.config_manoirs import charger_config_depuis_fichier
        if not charger_config_depuis_fichier(args.config):
            logger.error(f"Impossible de charger {args.config}")
            return 1

    # Déterminer quels manoirs créer
    if args.manoirs:
        manoir_ids = [m.strip() for m in args.manoirs.split(',')]
    else:
        manoir_ids = None  # Tous les manoirs

    # Créer les manoirs
    logger.info("Création des manoirs...")
    manoirs = creer_tous_manoirs(manoir_ids)

    if not manoirs:
        logger.error("Aucun manoir créé")
        if manoir_ids:
            logger.info(f"Demandés: {manoir_ids}")
            logger.info(f"Disponibles: {get_all_manoir_ids()}")
        return 1

    logger.info(f"Manoirs à automatiser: {list(manoirs.keys())}")

    # Mode dry-run
    if args.dry_run:
        logger.info("=== MODE DRY-RUN (simulation) ===")
        print("\nManoirs qui seraient automatisés:")
        for mid, man in manoirs.items():
            print(f"  - {mid}: {man.nom} ({type(man).__name__}, priorité={man.priorite})")
        print("\nAucune action réelle effectuée.")
        return 0

    # Créer le moteur
    engine = get_engine()

    # Ajouter les manoirs
    engine.ajouter_manoirs(manoirs)

    # Callbacks pour affichage
    def on_manoir_change(manoir_id, manoir):
        print(f"[{time.strftime('%H:%M:%S')}] >>> Manoir actif: {manoir.nom}")

    def on_state_change(ancien_etat, nouvel_etat):
        if nouvel_etat == EtatEngine.ATTENTE_UTILISATEUR:
            print(f"[{time.strftime('%H:%M:%S')}] >>> PAUSE - Activité utilisateur détectée")
        elif ancien_etat == EtatEngine.ATTENTE_UTILISATEUR and nouvel_etat == EtatEngine.EN_COURS:
            print(f"[{time.strftime('%H:%M:%S')}] >>> REPRISE - Automatisation active")

    def on_error(manoir_id, erreur):
        logger.warning(f"Erreur {manoir_id}: {erreur}")

    engine.set_callback('manoir_change', on_manoir_change)
    engine.set_callback('state_change', on_state_change)
    engine.set_callback('error', on_error)

    # Démarrer
    logger.info("=" * 60)
    logger.info(" DÉMARRAGE DE L'AUTOMATISATION")
    logger.info("=" * 60)
    logger.info("Appuyez sur Ctrl+C pour arrêter proprement")
    logger.info("Bougez la souris ou tapez au clavier pour mettre en pause")

    try:
        engine.demarrer()
    except KeyboardInterrupt:
        logger.info("Interruption clavier...")
        engine.arreter()

    # Afficher les statistiques finales
    stats = engine.get_stats()

    logger.info("=" * 60)
    logger.info(" STATISTIQUES FINALES")
    logger.info("=" * 60)
    logger.info(f"Actions exécutées:  {stats['actions_executees']}")
    logger.info(f"Manoirs traités:    {stats['manoirs_traites']}")
    logger.info(f"Erreurs détectées:  {stats['erreurs_detectees']}")
    if stats.get('temps_total', 0) > 0:
        duree = stats['temps_total']
        heures = int(duree // 3600)
        minutes = int((duree % 3600) // 60)
        secondes = int(duree % 60)
        logger.info(f"Durée totale:       {heures}h {minutes}m {secondes}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())

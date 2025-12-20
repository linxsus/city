# -*- coding: utf-8 -*-
"""Gestionnaire de slots avec persistance

Gère les slots d'envoi pour chaque fenêtre (1-5 selon niveau du manoir).
Permet de savoir quand un slot sera disponible.
"""
import json
import time
from pathlib import Path
from threading import Lock

from utils.config import SLOTS_FILE, DATA_DIR
from utils.logger import get_module_logger

logger = get_module_logger("SlotManager")


class Slot:
    """Représente un slot d'envoi

    Attributes:
        manoir_id: ID du manoir propriétaire
        slot_type: Type de slot (ex: "mercenaire", "collecte", "raid")
        slot_index: Index du slot dans son type (0, 1, 2...)
        heure_liberation: Timestamp estimé de libération
        actif: Si le slot est en cours d'utilisation
    """

    def __init__(self, manoir_id, slot_type, slot_index=0):
        """
        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (ex: "mercenaire", "collecte")
            slot_index: Index du slot dans son type (0, 1, 2...)
        """
        self.manoir_id = manoir_id
        self.slot_type = slot_type
        self.slot_index = slot_index
        self.heure_liberation = 0
        self.actif = False
    
    def is_available(self, margin=30):
        """Vérifie si le slot est disponible ou le sera bientôt
        
        Args:
            margin: Marge en secondes pour considérer "bientôt disponible"
            
        Returns:
            bool: True si disponible ou bientôt disponible
        """
        if not self.actif:
            return True
        return time.time() + margin >= self.heure_liberation
    
    def is_free(self):
        """Vérifie si le slot est actuellement libre
        
        Returns:
            bool: True si libre maintenant
        """
        if not self.actif:
            return True
        return time.time() >= self.heure_liberation
    
    def time_until_free(self):
        """Retourne le temps restant avant libération
        
        Returns:
            float: Secondes restantes (0 si déjà libre)
        """
        if not self.actif:
            return 0
        remaining = self.heure_liberation - time.time()
        return max(0, remaining)
    
    def occupy(self, duree):
        """Occupe le slot

        Args:
            duree: Durée estimée en secondes
        """
        self.actif = True
        self.heure_liberation = time.time() + duree
        logger.debug(
            f"Slot {self.manoir_id}:{self.slot_type}[{self.slot_index}] occupé "
            f"pour {duree}s"
        )
    
    def release(self):
        """Libère le slot"""
        self.actif = False
        self.heure_liberation = 0
    
    def update_liberation(self, nouvelle_heure):
        """Met à jour l'heure de libération
        
        Args:
            nouvelle_heure: Nouveau timestamp de libération
        """
        self.heure_liberation = nouvelle_heure
    
    def to_dict(self):
        """Convertit en dictionnaire pour sérialisation"""
        return {
            'manoir_id': self.manoir_id,
            'slot_type': self.slot_type,
            'slot_index': self.slot_index,
            'heure_liberation': self.heure_liberation,
            'actif': self.actif,
        }

    @classmethod
    def from_dict(cls, data):
        """Crée un slot depuis un dictionnaire"""
        slot = cls(
            data['manoir_id'],
            data['slot_type'],
            data.get('slot_index', 0)
        )
        slot.heure_liberation = data.get('heure_liberation', 0)
        slot.actif = data.get('actif', False)

        # Vérifier si le slot devrait être libéré
        if slot.actif and time.time() >= slot.heure_liberation:
            slot.release()

        return slot

    def __repr__(self):
        if self.actif:
            remaining = self.time_until_free()
            return f"Slot({self.slot_type}[{self.slot_index}], occupé, libre dans {remaining:.0f}s)"
        return f"Slot({self.slot_type}[{self.slot_index}], libre)"


class SlotManager:
    """Gestionnaire de slots avec persistance

    Gère les slots par manoir et par type. Permet de savoir quand des slots
    seront disponibles pour planifier les actions.

    Les slots sont organisés par type:
        slots_config = [
            {'nom': 'mercenaire', 'nb': 2},
            {'nom': 'collecte', 'nb': 3},
            {'nom': 'raid', 'nb': 1},
        ]
    """

    # Temps moyens par type d'action (en secondes)
    TEMPS_MOYENS = {
        'mercenaire': 60,
        'collecte': 180,
        'raid': 120,
        'reconnaissance': 30,
        'default': 120,
    }

    def __init__(self, filepath=None):
        """
        Args:
            filepath: Chemin du fichier de persistance
        """
        self.filepath = Path(filepath) if filepath else SLOTS_FILE
        self._slots = {}  # {manoir_id: {slot_type: [Slot, ...]}}
        self._slots_config = {}  # {manoir_id: [{'nom': str, 'nb': int}, ...]}
        self._lock = Lock()

        # Charger les données existantes
        self._load()

    def register_manoir(self, manoir_id, slots_config):
        """Enregistre un manoir avec sa configuration de slots

        Args:
            manoir_id: ID du manoir
            slots_config: Liste de dicts [{'nom': str, 'nb': int}, ...]
                          Peut aussi être un int pour rétrocompatibilité
        """
        with self._lock:
            # Rétrocompatibilité: si c'est un int, créer des slots génériques
            if isinstance(slots_config, int):
                slots_config = [{'nom': 'default', 'nb': slots_config}]

            self._slots_config[manoir_id] = slots_config

            if manoir_id not in self._slots:
                self._slots[manoir_id] = {}

            # Créer/mettre à jour les slots par type
            for slot_def in slots_config:
                slot_type = slot_def['nom']
                nb_slots = slot_def['nb']

                if slot_type not in self._slots[manoir_id]:
                    self._slots[manoir_id][slot_type] = [
                        Slot(manoir_id, slot_type, i) for i in range(nb_slots)
                    ]
                else:
                    # Ajuster le nombre si nécessaire
                    current = len(self._slots[manoir_id][slot_type])
                    if nb_slots > current:
                        for i in range(current, nb_slots):
                            self._slots[manoir_id][slot_type].append(
                                Slot(manoir_id, slot_type, i)
                            )
                    elif nb_slots < current:
                        self._slots[manoir_id][slot_type] = \
                            self._slots[manoir_id][slot_type][:nb_slots]

            # Supprimer les types qui ne sont plus dans la config
            types_config = {s['nom'] for s in slots_config}
            for slot_type in list(self._slots[manoir_id].keys()):
                if slot_type not in types_config:
                    del self._slots[manoir_id][slot_type]

        total = sum(len(slots) for slots in self._slots[manoir_id].values())
        types_str = ', '.join(f"{s['nom']}:{s['nb']}" for s in slots_config)
        logger.debug(f"Manoir {manoir_id} enregistré avec {total} slots ({types_str})")
    
    def _get_all_slots_list(self, manoir_id):
        """Retourne tous les slots d'un manoir en liste plate (PROTÉGÉ)"""
        if manoir_id not in self._slots:
            return []
        slots = []
        for slot_list in self._slots[manoir_id].values():
            slots.extend(slot_list)
        return slots

    def get_available_slots(self, manoir_id, slot_type=None, margin=30):
        """Récupère les slots disponibles ou bientôt disponibles

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (None = tous les types)
            margin: Marge en secondes

        Returns:
            List[Slot]: Slots disponibles
        """
        with self._lock:
            if manoir_id not in self._slots:
                return []

            if slot_type:
                slots = self._slots[manoir_id].get(slot_type, [])
            else:
                slots = self._get_all_slots_list(manoir_id)

            return [s for s in slots if s.is_available(margin)]

    def get_free_slots(self, manoir_id, slot_type=None):
        """Récupère les slots actuellement libres

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (None = tous les types)

        Returns:
            List[Slot]: Slots libres
        """
        with self._lock:
            if manoir_id not in self._slots:
                return []

            if slot_type:
                slots = self._slots[manoir_id].get(slot_type, [])
            else:
                slots = self._get_all_slots_list(manoir_id)

            return [s for s in slots if s.is_free()]

    def count_free_slots(self, manoir_id, slot_type=None):
        """Compte les slots libres

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (None = tous les types)

        Returns:
            int: Nombre de slots libres
        """
        return len(self.get_free_slots(manoir_id, slot_type))

    def count_available_slots(self, manoir_id, slot_type=None, margin=30):
        """Compte les slots disponibles ou bientôt disponibles

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (None = tous les types)
            margin: Marge en secondes

        Returns:
            int: Nombre de slots disponibles
        """
        return len(self.get_available_slots(manoir_id, slot_type, margin))

    def has_free_slot(self, manoir_id, slot_type=None):
        """Vérifie si le manoir a au moins un slot libre

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (None = tous les types)

        Returns:
            bool: True si au moins un slot libre
        """
        return self.count_free_slots(manoir_id, slot_type) > 0

    def occupy_slot(self, manoir_id, slot_type, duree=None):
        """Occupe le premier slot libre du type spécifié

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot à occuper
            duree: Durée estimée (utilise temps moyen si None)

        Returns:
            Slot ou None: Le slot occupé ou None si aucun disponible
        """
        if duree is None:
            duree = self.TEMPS_MOYENS.get(slot_type, self.TEMPS_MOYENS['default'])

        with self._lock:
            if manoir_id not in self._slots:
                return None

            slots = self._slots[manoir_id].get(slot_type, [])
            for slot in slots:
                if slot.is_free():
                    slot.occupy(duree)
                    return slot

        return None

    def release_slot(self, manoir_id, slot_type, slot_index=0):
        """Libère un slot spécifique

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot
            slot_index: Index du slot dans son type
        """
        with self._lock:
            if manoir_id in self._slots and slot_type in self._slots[manoir_id]:
                slots = self._slots[manoir_id][slot_type]
                if slot_index < len(slots):
                    slots[slot_index].release()

    def update_slot_time(self, manoir_id, slot_type, slot_index, nouvelle_heure):
        """Met à jour l'heure de libération d'un slot

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot
            slot_index: Index du slot dans son type
            nouvelle_heure: Nouveau timestamp
        """
        with self._lock:
            if manoir_id in self._slots and slot_type in self._slots[manoir_id]:
                slots = self._slots[manoir_id][slot_type]
                if slot_index < len(slots):
                    slots[slot_index].update_liberation(nouvelle_heure)

    def get_next_free_time(self, manoir_id, slot_type=None):
        """Récupère le timestamp de la prochaine libération de slot

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (None = tous les types)

        Returns:
            float ou None: Timestamp de la prochaine libération
        """
        with self._lock:
            if manoir_id not in self._slots:
                return None

            if slot_type:
                slots = self._slots[manoir_id].get(slot_type, [])
            else:
                slots = self._get_all_slots_list(manoir_id)

            # Si un slot est déjà libre, retourner maintenant
            for slot in slots:
                if slot.is_free():
                    return time.time()

            # Sinon trouver le slot qui se libère le plus tôt
            next_time = None
            for slot in slots:
                if slot.actif:
                    if next_time is None or slot.heure_liberation < next_time:
                        next_time = slot.heure_liberation

            return next_time

    def get_all_slots(self, manoir_id, slot_type=None):
        """Récupère tous les slots d'un manoir

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (None = tous les types)

        Returns:
            List[Slot]: Tous les slots (ou dict si slot_type=None)
        """
        with self._lock:
            if manoir_id not in self._slots:
                return [] if slot_type else {}

            if slot_type:
                return self._slots[manoir_id].get(slot_type, []).copy()
            else:
                # Retourne une copie du dict
                return {
                    t: slots.copy()
                    for t, slots in self._slots[manoir_id].items()
                }

    def get_slot_types(self, manoir_id):
        """Récupère les types de slots disponibles pour un manoir

        Args:
            manoir_id: ID du manoir

        Returns:
            List[str]: Types de slots
        """
        with self._lock:
            if manoir_id not in self._slots:
                return []
            return list(self._slots[manoir_id].keys())

    def refresh_slots(self, manoir_id, slot_type=None):
        """Actualise l'état des slots (libère ceux qui devraient l'être)

        Args:
            manoir_id: ID du manoir
            slot_type: Type de slot (None = tous les types)
        """
        with self._lock:
            if manoir_id not in self._slots:
                return

            if slot_type:
                slots = self._slots[manoir_id].get(slot_type, [])
            else:
                slots = self._get_all_slots_list(manoir_id)

            now = time.time()
            for slot in slots:
                if slot.actif and now >= slot.heure_liberation:
                    slot.release()

    def _load(self):
        """Charge les données depuis le fichier (PROTÉGÉ)"""
        if not self.filepath.exists():
            logger.info("Pas de fichier slots existant, démarrage à vide")
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._lock:
                self._slots_config = data.get('slots_config', {})
                self._slots = {}

                # Charger les slots par manoir et par type
                for manoir_id, types_data in data.get('slots', {}).items():
                    self._slots[manoir_id] = {}
                    for slot_type, slots_data in types_data.items():
                        self._slots[manoir_id][slot_type] = [
                            Slot.from_dict(s) for s in slots_data
                        ]

            total = sum(
                len(slots)
                for types in self._slots.values()
                for slots in types.values()
            )
            logger.info(f"Chargé {total} slot(s) pour {len(self._slots)} manoir(s)")

        except Exception as e:
            logger.error(f"Erreur chargement slots: {e}")

    def save(self):
        """Sauvegarde les données dans le fichier"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            with self._lock:
                data = {
                    'last_save': time.time(),
                    'slots_config': self._slots_config,
                    'slots': {
                        manoir_id: {
                            slot_type: [s.to_dict() for s in slots]
                            for slot_type, slots in types.items()
                        }
                        for manoir_id, types in self._slots.items()
                    }
                }
            
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Slots sauvegardés")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde slots: {e}")
    
    def __repr__(self):
        total = sum(
            len(slots)
            for types in self._slots.values()
            for slots in types.values()
        )
        return f"SlotManager({len(self._slots)} manoirs, {total} slots)"


# Instance globale
_slot_manager_instance = None


def get_slot_manager():
    """Retourne une instance singleton de SlotManager
    
    Returns:
        SlotManager: Instance partagée
    """
    global _slot_manager_instance
    if _slot_manager_instance is None:
        _slot_manager_instance = SlotManager()
    return _slot_manager_instance

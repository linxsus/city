"""Bus de messages pour communication inter-fenêtres

Permet aux fenêtres de communiquer entre elles de manière asynchrone.
Version simple pour commencer, à enrichir plus tard.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Optional

from utils.logger import get_module_logger

logger = get_module_logger("MessageBus")


class MessageType(Enum):
    """Types de messages possibles"""

    # Coordination
    DEMANDE_RAID = "demande_raid"  # Demande de raid multi-comptes
    CONFIRMATION_RAID = "confirm_raid"  # Confirmation de participation
    ANNULATION_RAID = "annul_raid"  # Annulation de raid

    # Priorité
    PRIORITE_HAUTE = "prio_haute"  # Demande de priorité haute
    CEDE_PRIORITE = "cede_prio"  # Cède la priorité

    # État
    TACHE_TERMINEE = "tache_ok"  # Tâche terminée
    TACHE_ECHOUEE = "tache_ko"  # Tâche échouée
    FENETRE_PRETE = "pret"  # Fenêtre prête
    FENETRE_OCCUPEE = "occupe"  # Fenêtre occupée

    # Kill Event
    KILLS_TERMINES = "kills_ok"  # Kills terminés
    DEMANDE_AIDE_KILLS = "aide_kills"  # Demande d'aide pour kills

    # Générique
    INFO = "info"  # Information générale
    COMMANDE = "commande"  # Commande directe


@dataclass
class Message:
    """Représente un message inter-fenêtres

    Attributes:
        source: ID de la fenêtre émettrice
        destination: ID de la fenêtre destinataire (None = broadcast)
        type_msg: Type de message (MessageType)
        contenu: Contenu du message (dict ou str)
        timestamp: Timestamp de création
        id: ID unique du message
        lu: Si le message a été lu
        expire: Timestamp d'expiration (None = pas d'expiration)
    """

    source: str
    destination: Optional[str]
    type_msg: MessageType
    contenu: Any = None
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: f"{time.time():.6f}")
    lu: bool = False
    expire: Optional[float] = None

    def is_expired(self):
        """Vérifie si le message a expiré"""
        if self.expire is None:
            return False
        return time.time() > self.expire

    def is_for(self, fenetre_id):
        """Vérifie si le message est destiné à une fenêtre

        Args:
            fenetre_id: ID de la fenêtre

        Returns:
            bool: True si destiné à cette fenêtre
        """
        if self.destination is None:
            # Broadcast - pour tout le monde sauf l'émetteur
            return self.source != fenetre_id
        return self.destination == fenetre_id

    def to_dict(self):
        """Convertit en dictionnaire"""
        return {
            "source": self.source,
            "destination": self.destination,
            "type_msg": self.type_msg.value,
            "contenu": self.contenu,
            "timestamp": self.timestamp,
            "id": self.id,
            "lu": self.lu,
            "expire": self.expire,
        }

    @classmethod
    def from_dict(cls, data):
        """Crée un message depuis un dictionnaire"""
        return cls(
            source=data["source"],
            destination=data.get("destination"),
            type_msg=MessageType(data["type_msg"]),
            contenu=data.get("contenu"),
            timestamp=data.get("timestamp", time.time()),
            id=data.get("id", f"{time.time():.6f}"),
            lu=data.get("lu", False),
            expire=data.get("expire"),
        )

    def __repr__(self):
        dest = self.destination or "ALL"
        return f"Message({self.source}->{dest}, {self.type_msg.value})"


class MessageBus:
    """Bus de messages pour communication inter-fenêtres

    Permet d'envoyer des messages entre fenêtres de manière asynchrone.
    Les messages sont stockés jusqu'à lecture ou expiration.
    """

    MAX_MESSAGES = 1000  # Limite de messages en file
    DEFAULT_EXPIRE = 3600  # 1 heure par défaut

    def __init__(self):
        """Initialise le bus de messages"""
        self._messages = deque(maxlen=self.MAX_MESSAGES)
        self._lock = Lock()
        self._subscribers = {}  # {fenetre_id: callback}

    def send(self, source, destination, type_msg, contenu=None, expire=None):
        """Envoie un message

        Args:
            source: ID de la fenêtre émettrice
            destination: ID du destinataire (None = broadcast)
            type_msg: Type de message (MessageType)
            contenu: Contenu optionnel
            expire: Durée de vie en secondes (None = défaut)

        Returns:
            Message: Le message créé
        """
        expire_time = time.time() + self.DEFAULT_EXPIRE if expire is None else time.time() + expire

        msg = Message(
            source=source,
            destination=destination,
            type_msg=type_msg,
            contenu=contenu,
            expire=expire_time,
        )

        with self._lock:
            self._messages.append(msg)

        logger.debug(f"Message envoyé: {msg}")

        # Notifier le subscriber si présent
        if destination and destination in self._subscribers:
            try:
                self._subscribers[destination](msg)
            except Exception as e:
                logger.error(f"Erreur callback subscriber {destination}: {e}")

        return msg

    def send_to(self, source, destination, type_msg, contenu=None, expire=None):
        """Alias pour envoyer un message direct

        Args:
            source: ID source
            destination: ID destination
            type_msg: Type
            contenu: Contenu
            expire: Expiration

        Returns:
            Message
        """
        return self.send(source, destination, type_msg, contenu, expire)

    def broadcast(self, source, type_msg, contenu=None, expire=None):
        """Envoie un message à toutes les fenêtres

        Args:
            source: ID source
            type_msg: Type
            contenu: Contenu
            expire: Expiration

        Returns:
            Message
        """
        return self.send(source, None, type_msg, contenu, expire)

    def get_messages(self, fenetre_id, type_filter=None, mark_as_read=True):
        """Récupère les messages pour une fenêtre

        Args:
            fenetre_id: ID de la fenêtre
            type_filter: Type de message à filtrer (optionnel)
            mark_as_read: Marquer comme lus

        Returns:
            List[Message]: Messages correspondants
        """
        result = []

        with self._lock:
            for msg in self._messages:
                if msg.is_expired() or msg.lu:
                    continue
                if not msg.is_for(fenetre_id):
                    continue
                if type_filter and msg.type_msg != type_filter:
                    continue

                result.append(msg)
                if mark_as_read:
                    msg.lu = True

        return result

    def has_messages(self, fenetre_id, type_filter=None):
        """Vérifie si une fenêtre a des messages en attente

        Args:
            fenetre_id: ID de la fenêtre
            type_filter: Type optionnel

        Returns:
            bool: True si des messages attendent
        """
        with self._lock:
            for msg in self._messages:
                if msg.is_expired() or msg.lu:
                    continue
                if not msg.is_for(fenetre_id):
                    continue
                if type_filter and msg.type_msg != type_filter:
                    continue
                return True
        return False

    def peek_messages(self, fenetre_id, type_filter=None):
        """Récupère les messages sans les marquer comme lus

        Args:
            fenetre_id: ID de la fenêtre
            type_filter: Type optionnel

        Returns:
            List[Message]: Messages correspondants
        """
        return self.get_messages(fenetre_id, type_filter, mark_as_read=False)

    def count_messages(self, fenetre_id, type_filter=None):
        """Compte les messages en attente

        Args:
            fenetre_id: ID de la fenêtre
            type_filter: Type optionnel

        Returns:
            int: Nombre de messages
        """
        return len(self.peek_messages(fenetre_id, type_filter))

    def subscribe(self, fenetre_id, callback):
        """Abonne une fenêtre pour recevoir des notifications

        Args:
            fenetre_id: ID de la fenêtre
            callback: Fonction à appeler (reçoit Message en paramètre)
        """
        self._subscribers[fenetre_id] = callback
        logger.debug(f"Fenêtre {fenetre_id} abonnée au bus")

    def unsubscribe(self, fenetre_id):
        """Désabonne une fenêtre

        Args:
            fenetre_id: ID de la fenêtre
        """
        if fenetre_id in self._subscribers:
            del self._subscribers[fenetre_id]
            logger.debug(f"Fenêtre {fenetre_id} désabonnée")

    def clear_expired(self):
        """Supprime les messages expirés"""
        with self._lock:
            # Créer une nouvelle deque avec seulement les messages valides
            valid = [m for m in self._messages if not m.is_expired()]
            self._messages = deque(valid, maxlen=self.MAX_MESSAGES)

    def clear_all(self):
        """Supprime tous les messages"""
        with self._lock:
            self._messages.clear()
        logger.debug("Bus de messages vidé")

    def clear_for(self, fenetre_id):
        """Supprime tous les messages pour une fenêtre

        Args:
            fenetre_id: ID de la fenêtre
        """
        with self._lock:
            self._messages = deque(
                [m for m in self._messages if not m.is_for(fenetre_id)], maxlen=self.MAX_MESSAGES
            )

    def __len__(self):
        return len(self._messages)

    def __repr__(self):
        return f"MessageBus({len(self._messages)} messages)"


# Instance globale
_message_bus_instance = None


def get_message_bus():
    """Retourne une instance singleton de MessageBus

    Returns:
        MessageBus: Instance partagée
    """
    global _message_bus_instance
    if _message_bus_instance is None:
        _message_bus_instance = MessageBus()
    return _message_bus_instance


# Fonctions helper pour simplifier l'envoi de messages courants
def demander_raid(source, destination, details=None):
    """Helper: Envoie une demande de raid"""
    return get_message_bus().send_to(source, destination, MessageType.DEMANDE_RAID, details)


def signaler_kills_termines(source, nb_kills=None):
    """Helper: Signale que les kills sont terminés"""
    return get_message_bus().broadcast(source, MessageType.KILLS_TERMINES, {"nb_kills": nb_kills})


def demander_priorite(source):
    """Helper: Demande la priorité haute"""
    return get_message_bus().broadcast(source, MessageType.PRIORITE_HAUTE)

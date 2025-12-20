# -*- coding: utf-8 -*-
"""Package core - Composants principaux du framework"""

from core.window_manager import WindowManager, get_window_manager
from core.user_activity_detector import UserActivityDetector, get_activity_detector
from core.timer_manager import Timer, TimerManager, get_timer_manager
from core.slot_manager import Slot, SlotManager, get_slot_manager
from core.window_state_manager import (
    EtatManoir,
    ManoirState,
    ManoirStateManager,
    get_window_state_manager
)
from core.message_bus import (
    MessageType,
    Message,
    MessageBus,
    get_message_bus,
    demander_raid,
    signaler_kills_termines,
    demander_priorite,
)
from core.simple_scheduler import (
    ManoirSelection,
    SimpleScheduler,
    get_simple_scheduler,
)
from core.engine import (
    EtatEngine,
    Engine,
    get_engine,
)

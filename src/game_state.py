from enum import Enum, auto


class GameState(Enum):
    START = auto()
    HELP = auto()
    PAUSED = auto()
    VILLAGE_EXPLORING = auto()
    OUTSKIRTS_EXPLORING = auto()
    TEMPLE_EXPLORING = auto()
    BATTLE = auto()
    BATTLE_VICTORY = auto()
    COMPLETE = auto()
    FAILED = auto()

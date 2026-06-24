from enum import Enum, auto


class GameState(Enum):
    """游戏状态枚举，用于控制当前应该响应哪些输入和绘制哪些界面。"""

    START = auto()
    HELP = auto()
    PAUSED = auto()
    VILLAGE_EXPLORING = auto()
    OUTSKIRTS_EXPLORING = auto()
    FOREST_EXPLORING = auto()
    TEMPLE_EXPLORING = auto()
    BATTLE = auto()
    BATTLE_VICTORY = auto()
    COMPLETE = auto()
    FAILED = auto()

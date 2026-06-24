"""Stage 1 基础配置：只保留地图、玩家、摄像机和碰撞需要的常量。"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCE_DIR = BASE_DIR / "resource"

VILLAGE_MAP_PATH = RESOURCE_DIR / "tmx" / "village1.tmx"
SWK_DIR = RESOURCE_DIR / "img" / "swk"

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
FPS = 60

PLAYER_SPEED = 220
PLAYER_SCALE = 0.5
PLAYER_HITBOX_SIZE = (32, 28)
DEFAULT_PLAYER_SPAWN = (400, 300)

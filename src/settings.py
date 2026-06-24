"""Stage 2 配置：加入多地图、NPC 和对话框所需常量。"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCE_DIR = BASE_DIR / "resource"

VILLAGE_MAP_PATH = RESOURCE_DIR / "tmx" / "village1.tmx"
TEMPLE_MAP_PATH = RESOURCE_DIR / "tmx" / "temple1.tmx"
TEMPLE_FALLBACK_MAP_PATH = RESOURCE_DIR / "tmx" / "temple.tmx"
SWK_DIR = RESOURCE_DIR / "img" / "swk"
ELDER_DIR = RESOURCE_DIR / "img" / "elder"
GOD_DIR = RESOURCE_DIR / "img" / "god"
DIALOG_IMAGE_PATH = RESOURCE_DIR / "img" / "dialog" / "dialog.png"
FONT_PATH = RESOURCE_DIR / "font" / "newfont.TTF"

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
FPS = 60

PLAYER_SPEED = 220
PLAYER_SCALE = 0.5
PLAYER_HITBOX_SIZE = (32, 28)
DEFAULT_PLAYER_SPAWN = (400, 300)
DEFAULT_TEMPLE_SPAWN = (300, 900)

NPC_LAYERS = ("god", "elder", "child")
NPC_INTERACTION_PADDING = 40

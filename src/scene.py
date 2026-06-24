"""Stage 2 场景模块：把地图、出生点和 NPC 组织在一起。"""

from .npc import NPC
from .settings import NPC_LAYERS
from .tmx_map import TmxMap


class Scene:
    """一个可探索场景，例如村庄或寺庙。"""

    def __init__(self, name, map_path, default_spawn, npc_layers=()):
        self.name = name
        self.map_path = map_path
        self.map = TmxMap(map_path)
        self.player_spawn = self.map.get_object_position("actor", "sun", default_spawn)
        self.npcs = self._load_npcs(npc_layers)

    @classmethod
    def village(cls, map_path, default_spawn):
        """创建有 NPC 的村庄场景。"""
        return cls("village", map_path, default_spawn, NPC_LAYERS)

    @classmethod
    def temple(cls, map_path, default_spawn):
        """创建寺庙场景；Stage 2 只探索，不启用怪物战斗。"""
        return cls("temple", map_path, default_spawn)

    def _load_npcs(self, npc_layers):
        """从 TMX 对象层读取 NPC。"""
        npcs = []
        for obj in self.map.get_objects(npc_layers):
            npcs.append(NPC(obj["layer"], obj["name"], (obj["x"], obj["y"])))
        return npcs

    @property
    def obstacle_rects(self):
        """当前地图障碍物列表。"""
        return self.map.obstacle_rects

    @property
    def pixel_size(self):
        """当前地图像素大小。"""
        return self.map.pixel_size

    def draw_map(self, surface, camera):
        """绘制场景地图。"""
        self.map.draw(surface, camera)

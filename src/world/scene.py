from collections import deque

import pygame

from ..combat.monster import Monster
from ..story.npc import NPC
from ..config.settings import (
    MONSTER_LAYERS,
    NPC_INTERACTION_PADDING,
    NPC_LAYERS,
    FOREST_NPC_SPAWNS,
    OUTSKIRTS_NPC_SPAWNS,
    PLAYER_HITBOX_SIZE,
)
from .tmx_map import TmxMap


"""场景管理模块。

Scene 把一张地图和它上面的 NPC、怪物、Boss、出生点组织在一起。Game 切换场景时
只需要切换当前 Scene，就能同时换地图、碰撞数据和场景对象。
"""


class Scene:
    """一个可探索场景，例如村庄、郊外、森林或寺庙。"""

    def __init__(self, name, map_path, default_spawn, npc_layers=(), monster_layers=(), extra_npcs=()):
        """加载地图、读取玩家出生点，并按对象层创建 NPC 和怪物。"""
        self.name = name
        self.map_path = map_path
        self.map = TmxMap(map_path)
        self.player_spawn = self.map.get_object_position(
            "actor",
            "sun",
            default_spawn,
        )
        self.npcs = self._load_npcs(npc_layers)
        self.npcs.extend(self._load_extra_npcs(extra_npcs))
        self._ensure_npcs_reachable()
        self.monsters = self._load_monsters(monster_layers)
        self.boss = None
        self.boss_spawned = False
        self.boss_spawn = self._compute_boss_spawn()

    @classmethod
    def village(cls, map_path, default_spawn):
        """创建村庄场景：有 NPC，没有怪物。"""
        return cls("village", map_path, default_spawn, NPC_LAYERS)

    @classmethod
    def outskirts(cls, map_path, default_spawn):
        """创建郊外过渡场景：用于村庄和森林之间的连接。"""
        # 原郊外场景：scene.tmx 使用瓦片地图，作为村庄和森林之间的连接。
        return cls("outskirts", map_path, default_spawn, extra_npcs=OUTSKIRTS_NPC_SPAWNS)

    @classmethod
    def forest(cls, map_path, default_spawn):
        """创建森林过渡场景：位于郊外和寺庙之间。"""
        # 新森林场景：forest.tmx 使用郊外.jpg 整图背景，整图可走。
        return cls("forest", map_path, default_spawn, extra_npcs=FOREST_NPC_SPAWNS)

    @classmethod
    def temple(cls, map_path, default_spawn):
        """创建寺庙场景：读取 monster 层生成怪物。"""
        return cls("temple", map_path, default_spawn, monster_layers=MONSTER_LAYERS)

    def _load_npcs(self, npc_layers):
        """从地图对象层读取 NPC 数据并创建 NPC 对象。"""
        npcs = []
        for obj in self.map.get_objects(npc_layers):
            npcs.append(
                NPC(
                    obj["layer"],
                    obj["name"],
                    (obj["x"], obj["y"]),
                )
            )
        return npcs

    def _load_extra_npcs(self, extra_npcs):
        """创建代码配置的场景 NPC，用于没有 NPC 对象层的过渡地图。"""
        npcs = []
        for layer_name, object_name, position in extra_npcs:
            npcs.append(NPC(layer_name, object_name, position))
        return npcs

    _REACH_CELL = 16

    def _ensure_npcs_reachable(self):
        """检查 NPC 是否可交互，必要时把 NPC 挪到附近可到达位置。"""
        # 有些 NPC 被障碍物（建筑/水域）围住，玩家走不到旁边。
        # 这里从玩家出生点做 flood-fill 求可达区，把够不到的 NPC 挪到最近的可达落脚点。
        # 不依赖 .tmx 的具体摆放，新增/调整障碍后也能自动保证每个 NPC 可达。
        if not self.npcs or not self.obstacle_rects:
            return

        reachable = self._reachable_cells()
        if not reachable:
            return

        cell = self._REACH_CELL
        taken = set()
        for npc in self.npcs:
            if self._npc_reachable(npc, reachable, cell):
                continue
            spot = self._nearest_reachable_point(npc.position, reachable, cell, taken)
            if spot is not None:
                npc.relocate(spot)

    def _reachable_cells(self):
        """从玩家出生点开始 flood-fill，计算玩家可以走到的网格区域。"""
        cell = self._REACH_CELL
        map_width, map_height = self.pixel_size
        foot_w, foot_h = PLAYER_HITBOX_SIZE
        obstacles = self.obstacle_rects
        grid_w, grid_h = map_width // cell, map_height // cell

        def walkable(cx, cy):
            """判断某个网格中心是否能容纳玩家脚下 hitbox。"""
            rect = pygame.Rect(0, 0, foot_w, foot_h)
            rect.center = (cx * cell + cell // 2, cy * cell + cell // 2)
            if rect.left < 0 or rect.top < 0 or rect.right > map_width or rect.bottom > map_height:
                return False
            return not any(rect.colliderect(obstacle) for obstacle in obstacles)

        spawn_x, spawn_y = self.player_spawn
        start = (int(spawn_x) // cell, int(spawn_y) // cell)
        if not (0 <= start[0] < grid_w and 0 <= start[1] < grid_h and walkable(*start)):
            start = self._find_walkable_cell(start, grid_w, grid_h, walkable)
            if start is None:
                return set()

        seen = {start}
        queue = deque([start])
        while queue:
            cx, cy = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) not in seen and 0 <= nx < grid_w and 0 <= ny < grid_h and walkable(nx, ny):
                    seen.add((nx, ny))
                    queue.append((nx, ny))
        return seen

    def _find_walkable_cell(self, origin, grid_w, grid_h, walkable):
        """当出生点不可走时，向外搜索最近的可走网格。"""
        ox, oy = origin
        for radius in range(1, max(grid_w, grid_h)):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    cx, cy = ox + dx, oy + dy
                    if 0 <= cx < grid_w and 0 <= cy < grid_h and walkable(cx, cy):
                        return (cx, cy)
        return None

    def _npc_reachable(self, npc, reachable, cell):
        """判断玩家可到达区域是否能碰到 NPC 的交互范围。"""
        interaction = npc.interaction_rect
        foot_w, foot_h = PLAYER_HITBOX_SIZE
        for (cx, cy) in reachable:
            reach = pygame.Rect(0, 0, foot_w, foot_h)
            reach.center = (cx * cell + cell // 2, cy * cell + cell // 2)
            reach = reach.inflate(NPC_INTERACTION_PADDING, NPC_INTERACTION_PADDING)
            if reach.colliderect(interaction):
                return True
        return False

    def _nearest_reachable_point(self, pos, reachable, cell, taken):
        """为不可达 NPC 寻找最近的可站立位置，并避免多个 NPC 重叠。"""
        best = None
        best_dist = None
        best_key = None
        for (cx, cy) in reachable:
            if (cx, cy) in taken:
                continue
            px, py = cx * cell + cell // 2, cy * cell + cell // 2
            dist = (px - pos.x) ** 2 + (py - pos.y) ** 2
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = (px, py)
                best_key = (cx, cy)
        if best_key is not None:
            # 把落点附近一小片标记为已占用，避免多个 NPC 叠在同一处。
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    taken.add((best_key[0] + dx, best_key[1] + dy))
        return best

    def _load_monsters(self, monster_layers):
        """从地图 monster 对象层读取怪物出生位置。"""
        monsters = []
        for obj in self.map.get_objects(monster_layers):
            monsters.append(
                Monster(
                    obj["name"],
                    obj["x"],
                    obj["y"],
                    obj["width"],
                    obj["height"],
                )
            )
        return monsters

    def _compute_boss_spawn(self):
        """计算 Boss 出生点，默认复用第一只小怪附近的合法位置。"""
        # 复用第一只小怪的合法落点作为 Boss 出生点，保证可走、可见、贴近战场。
        if self.monsters:
            first = self.monsters[0].hitbox
            return (first.x, first.y, first.width, first.height)
        return None

    def spawn_boss(self, boss):
        """把 Boss 加入当前场景的怪物列表。"""
        self.monsters.append(boss)
        self.boss = boss
        self.boss_spawned = True

    @property
    def active_monsters(self):
        """返回尚未被移除的怪物，死亡消失动画未结束前仍算 active。"""
        return [monster for monster in self.monsters if monster.is_active]

    def update_monsters(self, dt, player_hitbox=None):
        """更新场景内所有怪物的探索状态动画和简单 AI。"""
        for monster in self.active_monsters:
            monster.update_exploration(
                dt,
                player_hitbox,
                self.obstacle_rects,
                self.pixel_size,
            )

    def update_npcs(self, dt):
        """更新场景内所有 NPC 的待机动画。"""
        for npc in self.npcs:
            npc.update(dt)

    @property
    def obstacle_rects(self):
        """当前地图的障碍物碰撞矩形列表。"""
        return self.map.obstacle_rects

    @property
    def pixel_size(self):
        """当前地图的像素尺寸。"""
        return self.map.pixel_size

    def draw_map(self, surface, camera):
        """绘制当前场景地图。"""
        self.map.draw(surface, camera)

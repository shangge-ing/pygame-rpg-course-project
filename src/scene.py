from collections import deque

import pygame

from .monster import Monster
from .npc import NPC
from .settings import (
    MONSTER_LAYERS,
    NPC_INTERACTION_PADDING,
    NPC_LAYERS,
    PLAYER_HITBOX_SIZE,
)
from .tmx_map import TmxMap


class Scene:
    def __init__(self, name, map_path, default_spawn, npc_layers=(), monster_layers=()):
        self.name = name
        self.map_path = map_path
        self.map = TmxMap(map_path)
        self.player_spawn = self.map.get_object_position(
            "actor",
            "sun",
            default_spawn,
        )
        self.npcs = self._load_npcs(npc_layers)
        self._ensure_npcs_reachable()
        self.monsters = self._load_monsters(monster_layers)
        self.boss = None
        self.boss_spawned = False
        self.boss_spawn = self._compute_boss_spawn()

    @classmethod
    def village(cls, map_path, default_spawn):
        return cls("village", map_path, default_spawn, NPC_LAYERS)

    @classmethod
    def outskirts(cls, map_path, default_spawn):
        # 过渡场景：scene.tmx 只有瓦片装饰层，没有 NPC / 怪物 / 障碍层，整图可走。
        return cls("outskirts", map_path, default_spawn)

    @classmethod
    def temple(cls, map_path, default_spawn):
        return cls("temple", map_path, default_spawn, monster_layers=MONSTER_LAYERS)

    def _load_npcs(self, npc_layers):
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

    _REACH_CELL = 16

    def _ensure_npcs_reachable(self):
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
        cell = self._REACH_CELL
        map_width, map_height = self.pixel_size
        foot_w, foot_h = PLAYER_HITBOX_SIZE
        obstacles = self.obstacle_rects
        grid_w, grid_h = map_width // cell, map_height // cell

        def walkable(cx, cy):
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
        ox, oy = origin
        for radius in range(1, max(grid_w, grid_h)):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    cx, cy = ox + dx, oy + dy
                    if 0 <= cx < grid_w and 0 <= cy < grid_h and walkable(cx, cy):
                        return (cx, cy)
        return None

    def _npc_reachable(self, npc, reachable, cell):
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
        # 复用第一只小怪的合法落点作为 Boss 出生点，保证可走、可见、贴近战场。
        if self.monsters:
            first = self.monsters[0].hitbox
            return (first.x, first.y, first.width, first.height)
        return None

    def spawn_boss(self, boss):
        self.monsters.append(boss)
        self.boss = boss
        self.boss_spawned = True

    @property
    def active_monsters(self):
        return [monster for monster in self.monsters if monster.is_active]

    def update_monsters(self, dt, player_hitbox=None):
        for monster in self.active_monsters:
            monster.update_exploration(
                dt,
                player_hitbox,
                self.obstacle_rects,
                self.pixel_size,
            )

    def update_npcs(self, dt):
        for npc in self.npcs:
            npc.update(dt)

    @property
    def obstacle_rects(self):
        return self.map.obstacle_rects

    @property
    def pixel_size(self):
        return self.map.pixel_size

    def draw_map(self, surface, camera):
        self.map.draw(surface, camera)

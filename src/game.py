"""Stage 2 游戏主循环：多场景、NPC 对话和村庄到寺庙切换。"""

import pygame

from .camera import Camera
from .dialog import DialogBox
from .player import Player
from .scene import Scene
from .settings import (
    DEFAULT_PLAYER_SPAWN,
    DEFAULT_TEMPLE_SPAWN,
    FONT_PATH,
    FPS,
    NPC_INTERACTION_PADDING,
    SWK_DIR,
    TEMPLE_FALLBACK_MAP_PATH,
    TEMPLE_MAP_PATH,
    VILLAGE_MAP_PATH,
    WINDOW_SIZE,
)


class Game:
    """Stage 2 游戏类，负责探索、对话和场景切换。"""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Journey to the West - Stage 2")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.dialog_box = DialogBox(FONT_PATH, WINDOW_SIZE)
        self.scene = self._create_village_scene()
        self.player = Player(SWK_DIR, self.scene.player_spawn)
        self.camera = Camera(WINDOW_SIZE, self.scene.pixel_size)
        self.active_npc = None
        self.camera.update(self.player.rect)

    def _create_village_scene(self):
        """创建村庄场景。"""
        return Scene.village(VILLAGE_MAP_PATH, DEFAULT_PLAYER_SPAWN)

    def _create_temple_scene(self):
        """创建寺庙场景，temple1.tmx 失败时使用 temple.tmx。"""
        try:
            return Scene.temple(TEMPLE_MAP_PATH, DEFAULT_TEMPLE_SPAWN)
        except Exception as exc:
            print(f"temple1.tmx load failed, falling back to temple.tmx: {exc}")
            return Scene.temple(TEMPLE_FALLBACK_MAP_PATH, DEFAULT_TEMPLE_SPAWN)

    def run(self):
        """主循环。"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self):
        """处理退出、对话和场景切换输入。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.active_npc:
                    self.active_npc = None
                else:
                    self.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_SPACE):
                self._handle_interact()

    def _handle_interact(self):
        """靠近 NPC 时打开/关闭对话；靠近土地公再次交互进入寺庙。"""
        if self.active_npc:
            npc = self.active_npc
            self.active_npc = None
            if self.scene.name == "village" and npc.layer_name == "god":
                self._enter_temple()
            return
        self.active_npc = self._nearby_npc()

    def _enter_temple(self):
        """切换到寺庙场景。"""
        self.scene = self._create_temple_scene()
        self.player = Player(SWK_DIR, self.scene.player_spawn)
        self.camera = Camera(WINDOW_SIZE, self.scene.pixel_size)
        self.camera.update(self.player.rect)

    def _nearby_npc(self):
        """查找玩家附近最近的 NPC。"""
        player_range = self.player.hitbox.inflate(NPC_INTERACTION_PADDING, NPC_INTERACTION_PADDING)
        nearby = [npc for npc in self.scene.npcs if player_range.colliderect(npc.interaction_rect)]
        if not nearby:
            return None
        return min(
            nearby,
            key=lambda npc: (
                (self.player.hitbox.centerx - npc.rect.centerx) ** 2
                + (self.player.hitbox.centery - npc.rect.centery) ** 2
            ),
        )

    def _update(self, dt):
        """对话打开时暂停移动；否则更新玩家和摄像机。"""
        if self.active_npc:
            return
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.scene.pixel_size, self.scene.obstacle_rects)
        self.camera.update(self.player.rect)

    def _draw(self):
        """绘制地图、NPC、玩家和对话框。"""
        self.screen.fill((0, 0, 0))
        self.scene.draw_map(self.screen, self.camera)
        drawables = [*self.scene.npcs, self.player]
        for drawable in sorted(drawables, key=lambda item: item.rect.bottom):
            drawable.draw(self.screen, self.camera)
        if self.active_npc:
            self.dialog_box.draw(self.screen, self.active_npc)
        pygame.display.flip()

"""Stage 1 游戏主循环：基础地图、玩家移动、边界和摄像机。"""

import pygame

from .camera import Camera
from .player import Player
from .settings import DEFAULT_PLAYER_SPAWN, FPS, SWK_DIR, VILLAGE_MAP_PATH, WINDOW_SIZE
from .tmx_map import TmxMap


class Game:
    """基础版游戏类。"""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Journey to the West - Stage 1")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.map = TmxMap(VILLAGE_MAP_PATH)
        spawn = self.map.get_object_position("actor", "sun", DEFAULT_PLAYER_SPAWN)
        self.player = Player(SWK_DIR, spawn)
        self.camera = Camera(WINDOW_SIZE, self.map.pixel_size)
        self.camera.update(self.player.rect)

    def run(self):
        """主循环：处理退出、更新玩家、绘制地图和玩家。"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self):
        """处理关闭窗口和 Esc 退出。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def _update(self, dt):
        """更新玩家移动和摄像机。"""
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.map.pixel_size, self.map.obstacle_rects)
        self.camera.update(self.player.rect)

    def _draw(self):
        """绘制地图和孙悟空。"""
        self.screen.fill((0, 0, 0))
        self.map.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        pygame.display.flip()

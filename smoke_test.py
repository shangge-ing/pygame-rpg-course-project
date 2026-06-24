"""地图加载冒烟测试脚本。

这个文件用于早期验证 Pygame、PyTMX、tiled_render.py 和 village1.tmx
能不能正常协作。正式游戏入口是 main.py，本文件保留为环境排查工具。
"""

import os
from pathlib import Path

import pygame

from tiled_render import TiledRenderer


WINDOW_SIZE = (800, 600)
MAP_PATH = Path(__file__).resolve().parent / "resource" / "tmx" / "village1.tmx"


def main():
    """打开一个 800x600 窗口，显示村庄地图左上角区域。"""
    pygame.init()
    pygame.display.set_caption("village1.tmx smoke test")
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()

    renderer = TiledRenderer(str(MAP_PATH))
    map_surface = pygame.Surface(renderer.pixel_size).convert_alpha()
    renderer.render_map(map_surface)

    auto_quit_seconds = float(os.environ.get("SMOKE_TEST_AUTO_QUIT", "0") or 0)
    start_ticks = pygame.time.get_ticks()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if auto_quit_seconds > 0:
            elapsed = (pygame.time.get_ticks() - start_ticks) / 1000
            if elapsed >= auto_quit_seconds:
                running = False

        screen.fill((0, 0, 0))
        screen.blit(map_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()

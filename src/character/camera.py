"""摄像机模块。

地图通常比窗口大，摄像机负责根据玩家位置计算当前应该显示地图的哪一部分。
所有地图、NPC、怪物、玩家绘制时都会减去 camera offset，从世界坐标转换为屏幕坐标。
"""

import pygame


class Camera:
    """根据目标位置计算地图滚动偏移量。"""

    def __init__(self, window_size, map_size):
        """记录窗口大小、地图像素大小，并初始化偏移量。"""
        self.window_width, self.window_height = window_size
        self.map_width, self.map_height = map_size
        self.offset = pygame.Vector2(0, 0)

    def update(self, target_rect):
        """让摄像机尽量以目标矩形为中心，同时不显示地图外区域。"""
        x = target_rect.centerx - self.window_width / 2
        y = target_rect.centery - self.window_height / 2

        max_x = max(0, self.map_width - self.window_width)
        max_y = max(0, self.map_height - self.window_height)
        self.offset.x = min(max(x, 0), max_x)
        self.offset.y = min(max(y, 0), max_y)

    def apply_rect(self, rect):
        """把世界坐标中的矩形转换成屏幕坐标矩形。"""
        return rect.move(-int(self.offset.x), -int(self.offset.y))

    def apply_pos(self, pos):
        """把世界坐标中的点转换成屏幕坐标点。"""
        return int(pos[0] - self.offset.x), int(pos[1] - self.offset.y)

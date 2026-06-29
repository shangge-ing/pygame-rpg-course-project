import math

import pygame
from pytmx import TiledImageLayer, TiledTileLayer
from pytmx.util_pygame import load_pygame


class TmxMap:
    """封装 TMX 地图加载、静态图层渲染和对象层读取。"""

    def __init__(self, filename):
        """加载指定 TMX 文件，并预渲染瓦片层为一张大 Surface。"""
        self.filename = str(filename)
        self.tmx_data = load_pygame(self.filename)
        self.pixel_size = (
            self.tmx_data.width * self.tmx_data.tilewidth,
            self.tmx_data.height * self.tmx_data.tileheight,
        )
        self.surface = pygame.Surface(self.pixel_size, pygame.SRCALPHA).convert_alpha()
        self._render_static_layers()
        self.obstacle_rects = self.get_object_rects("obstacle")

    def _render_static_layers(self):
        """把可见瓦片层和图片层绘制到地图缓存 Surface。"""
        if self.tmx_data.background_color:
            self.surface.fill(pygame.Color(self.tmx_data.background_color))

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, TiledTileLayer):
                self._render_tile_layer(layer)
            elif isinstance(layer, TiledImageLayer):
                self._render_image_layer(layer)

    def _render_tile_layer(self, layer):
        """绘制一个 Tiled 瓦片图层。"""
        tile_width = self.tmx_data.tilewidth
        tile_height = self.tmx_data.tileheight
        for x, y, image in layer.tiles():
            if image:
                self.surface.blit(image, (x * tile_width, y * tile_height))

    def _render_image_layer(self, layer):
        """绘制 Tiled 图片层，通常用于地图背景或装饰。"""
        if not layer.image:
            return

        x = int(getattr(layer, "offsetx", 0) or 0)
        y = int(getattr(layer, "offsety", 0) or 0)
        self.surface.blit(layer.image, (x, y))

    def get_object_position(self, layer_name, object_name, default):
        """从对象层读取指定对象的坐标，常用于玩家出生点。"""
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
        except ValueError:
            return default

        for obj in layer:
            if getattr(obj, "name", None) == object_name:
                return float(obj.x), float(obj.y)

        return default

    def get_objects(self, layer_names):
        """批量读取若干对象层，返回普通字典列表给 NPC/怪物等系统使用。"""
        objects = []
        for layer_name in layer_names:
            try:
                layer = self.tmx_data.get_layer_by_name(layer_name)
            except ValueError:
                continue

            for obj in layer:
                objects.append(
                    {
                        "layer": layer_name,
                        "name": getattr(obj, "name", "") or layer_name,
                        "x": float(getattr(obj, "x", 0) or 0),
                        "y": float(getattr(obj, "y", 0) or 0),
                        "width": float(getattr(obj, "width", 0) or 0),
                        "height": float(getattr(obj, "height", 0) or 0),
                    }
                )
        return objects

    def get_object_rects(self, layer_name):
        """读取对象层并转换为 pygame.Rect，主要用于 obstacle 碰撞。"""
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
        except ValueError:
            return []

        rects = []
        for obj in layer:
            rects.append(self._object_to_rect(obj))
        return rects

    def _object_to_rect(self, obj):
        """把矩形或 polygon 对象转换成碰撞矩形；复杂形状使用外接矩形。"""
        points = getattr(obj, "points", None)
        if points:
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            left = math.floor(min(xs))
            top = math.floor(min(ys))
            width = max(1, math.ceil(max(xs) - min(xs)))
            height = max(1, math.ceil(max(ys) - min(ys)))
            return pygame.Rect(left, top, width, height)

        x = math.floor(float(getattr(obj, "x", 0) or 0))
        y = math.floor(float(getattr(obj, "y", 0) or 0))
        width = max(1, math.ceil(float(getattr(obj, "width", 0) or 0)))
        height = max(1, math.ceil(float(getattr(obj, "height", 0) or 0)))
        return pygame.Rect(x, y, width, height)

    def draw(self, target_surface, camera):
        """把预渲染地图按摄像机偏移绘制到窗口。"""
        target_surface.blit(self.surface, camera.apply_pos((0, 0)))

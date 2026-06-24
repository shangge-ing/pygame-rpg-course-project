"""TMX 地图加载与绘制模块。"""

import math

import pygame
from pytmx import TiledImageLayer, TiledTileLayer
from pytmx.util_pygame import load_pygame


class TmxMap:
    """加载 Tiled 地图，绘制静态图层，并读取 obstacle 碰撞对象。"""

    def __init__(self, filename):
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
        """把瓦片层和图片层预先渲染到一张大图上。"""
        if self.tmx_data.background_color:
            self.surface.fill(pygame.Color(self.tmx_data.background_color))

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, TiledTileLayer):
                self._render_tile_layer(layer)
            elif isinstance(layer, TiledImageLayer):
                self._render_image_layer(layer)

    def _render_tile_layer(self, layer):
        """绘制一个瓦片图层。"""
        tile_width = self.tmx_data.tilewidth
        tile_height = self.tmx_data.tileheight
        for x, y, image in layer.tiles():
            if image:
                self.surface.blit(image, (x * tile_width, y * tile_height))

    def _render_image_layer(self, layer):
        """绘制图片层。"""
        if not layer.image:
            return
        x = int(getattr(layer, "offsetx", 0) or 0)
        y = int(getattr(layer, "offsety", 0) or 0)
        self.surface.blit(layer.image, (x, y))

    def get_object_position(self, layer_name, object_name, default):
        """从对象层读取指定对象坐标，例如 actor/sun 出生点。"""
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
        except ValueError:
            return default

        for obj in layer:
            if getattr(obj, "name", None) == object_name:
                return float(obj.x), float(obj.y)
        return default

    def get_objects(self, layer_names):
        """批量读取若干对象层，返回 NPC 等系统可用的字典列表。"""
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
        """读取对象层并转换为 pygame.Rect，用于碰撞检测。"""
        try:
            layer = self.tmx_data.get_layer_by_name(layer_name)
        except ValueError:
            return []
        return [self._object_to_rect(obj) for obj in layer]

    def _object_to_rect(self, obj):
        """把矩形或 polygon 对象转换成碰撞矩形。"""
        points = getattr(obj, "points", None)
        if points:
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            return pygame.Rect(
                math.floor(min(xs)),
                math.floor(min(ys)),
                max(1, math.ceil(max(xs) - min(xs))),
                max(1, math.ceil(max(ys) - min(ys))),
            )

        x = math.floor(float(getattr(obj, "x", 0) or 0))
        y = math.floor(float(getattr(obj, "y", 0) or 0))
        width = max(1, math.ceil(float(getattr(obj, "width", 0) or 0)))
        height = max(1, math.ceil(float(getattr(obj, "height", 0) or 0)))
        return pygame.Rect(x, y, width, height)

    def draw(self, target_surface, camera):
        """按摄像机偏移绘制地图。"""
        target_surface.blit(self.surface, camera.apply_pos((0, 0)))

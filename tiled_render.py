"""早期 Tiled 地图渲染辅助。

smoke_test.py 使用这个类快速验证 .tmx 地图能否被 Pygame 显示。
正式游戏后续改为使用 src/tmx_map.py，但这个文件仍可作为地图排错工具。
"""

import pygame
from pytmx import *
from pytmx.util_pygame import load_pygame


class TiledRenderer(object):
    """
    把 Tiled 地图中的图层绘制到一个 Pygame Surface 上。
    """

    def __init__(self, filename):
        """加载 .tmx 文件，并记录整张地图的像素尺寸。"""
        tm = load_pygame(filename)

        # self.size will be the pixel size of the map
        # this value is used later to render the entire map to a pygame surface
        self.pixel_size = tm.width * tm.tilewidth, tm.height * tm.tileheight
        self.tmx_data = tm

        # for layer in self.tmx_data.visible_tile_layers:
        #     layer = self.tmx_data.layers[layer]
        #     for i in layer.tiles():
        #         # print(i)
        #         continue

    def render_map(self, surface):
        """把所有可见图层按顺序绘制到传入的 surface 上。

        注意：这个渲染器会把对象层也画出来，适合测试和调试；
        正式游戏中不显示对象层红框。
        """

        # fill the background color of our render surface
        if self.tmx_data.background_color:
            surface.fill(pygame.Color(self.tmx_data.background_color))

        # iterate over all the visible layers, then draw them
        for layer in self.tmx_data.visible_layers:
            # each layer can be handled differently by checking their type

            if isinstance(layer, TiledTileLayer):
                self.render_tile_layer(surface, layer)

            elif isinstance(layer, TiledObjectGroup):
                self.render_object_layer(surface, layer)

            elif isinstance(layer, TiledImageLayer):
                self.render_image_layer(surface, layer)

    def render_tile_layer(self, surface, layer):
        """绘制瓦片图层，例如地面、建筑、装饰等 tile。"""
        # deref these heavily used references for speed
        tw = self.tmx_data.tilewidth
        th = self.tmx_data.tileheight
        surface_blit = surface.blit

        # iterate over the tiles in the layer, and blit them
        for x, y, image in layer.tiles():
            surface_blit(image, (x * tw, y * th))

    def render_object_layer(self, surface, layer):
        """绘制对象层调试图形，用于检查 Tiled 中对象位置。"""
        # deref these heavily used references for speed
        draw_rect = pygame.draw.rect
        draw_lines = pygame.draw.lines
        surface_blit = surface.blit

        # these colors are used to draw vector shapes,
        # like polygon and box shapes
        rect_color = (255, 0, 0)
        poly_color = (0, 255, 0)

        # iterate over all the objects in the layer
        # These may be Tiled shapes like circles or polygons, GID objects, or Tiled Objects
        for obj in layer:
            # objects with points are polygons or lines
            if hasattr(obj, 'points'):
                draw_lines(surface, poly_color, obj.closed, obj.points, 3)

            # some objects have an image
            # Tiled calls them "GID Objects"
            elif obj.image:
                surface_blit(obj.image, (obj.x, obj.y))

            # draw a rect for everything else
            # Mostly, I am lazy, but you could check if it is circle/oval
            # and use pygame to draw an oval here...I just do a rect.
            else:
                draw_rect(surface, rect_color,
                          (obj.x, obj.y, obj.width, obj.height), 3)

    def render_image_layer(self, surface, layer):
        """绘制整张图片图层。"""
        if layer.image:
            surface.blit(layer.image, (0, 0))

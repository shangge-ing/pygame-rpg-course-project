import pygame


class Camera:
    def __init__(self, window_size, map_size):
        self.window_width, self.window_height = window_size
        self.map_width, self.map_height = map_size
        self.offset = pygame.Vector2(0, 0)

    def update(self, target_rect):
        x = target_rect.centerx - self.window_width / 2
        y = target_rect.centery - self.window_height / 2

        max_x = max(0, self.map_width - self.window_width)
        max_y = max(0, self.map_height - self.window_height)
        self.offset.x = min(max(x, 0), max_x)
        self.offset.y = min(max(y, 0), max_y)

    def apply_rect(self, rect):
        return rect.move(-int(self.offset.x), -int(self.offset.y))

    def apply_pos(self, pos):
        return int(pos[0] - self.offset.x), int(pos[1] - self.offset.y)

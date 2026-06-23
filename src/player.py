from pathlib import Path

import pygame

from .settings import PLAYER_HITBOX_SIZE, PLAYER_SCALE, PLAYER_SPEED


class Player(pygame.sprite.Sprite):
    FRAME_NAMES = {
        "down": ["00000.tga", "00001.tga", "00002.tga", "00003.tga"],
        "left": ["01000.tga", "01001.tga", "01002.tga", "01003.tga"],
        "up": ["02000.tga", "02001.tga", "02002.tga", "02003.tga"],
        "right": ["03000.tga", "03001.tga", "03002.tga", "03003.tga"],
    }

    def __init__(self, image_dir, spawn):
        super().__init__()
        self.position = pygame.Vector2(spawn)
        self.direction = "down"
        self.speed = PLAYER_SPEED
        self.animation_time = 0.0
        self.frame_index = 0
        self.load_error = None
        self.frames = self._load_frames(Path(image_dir))
        self.image = self.frames[self.direction][self.frame_index]
        self.rect = self.image.get_rect(center=self.position)
        self.hitbox = self._make_hitbox()

    def _load_frames(self, image_dir):
        try:
            frames = {}
            for direction, names in self.FRAME_NAMES.items():
                loaded = []
                for name in names:
                    image = pygame.image.load(image_dir / name).convert_alpha()
                    if PLAYER_SCALE != 1:
                        width = max(1, int(image.get_width() * PLAYER_SCALE))
                        height = max(1, int(image.get_height() * PLAYER_SCALE))
                        image = pygame.transform.smoothscale(image, (width, height))
                    loaded.append(image)
                frames[direction] = loaded
            return frames
        except Exception as exc:
            self.load_error = str(exc)
            placeholder = pygame.Surface((48, 72), pygame.SRCALPHA)
            placeholder.fill((220, 70, 70))
            pygame.draw.rect(placeholder, (255, 230, 80), placeholder.get_rect(), 3)
            return {direction: [placeholder] for direction in self.FRAME_NAMES}

    def update(self, dt, keys, map_size, obstacle_rects):
        movement = pygame.Vector2(0, 0)

        if keys[pygame.K_LEFT]:
            movement.x -= 1
            self.direction = "left"
        if keys[pygame.K_RIGHT]:
            movement.x += 1
            self.direction = "right"
        if keys[pygame.K_UP]:
            movement.y -= 1
            self.direction = "up"
        if keys[pygame.K_DOWN]:
            movement.y += 1
            self.direction = "down"

        moving = movement.length_squared() > 0
        if moving:
            movement = movement.normalize() * self.speed * dt
            self._move_axis(movement.x, 0, map_size, obstacle_rects)
            self._move_axis(0, movement.y, map_size, obstacle_rects)
            self._animate(dt)
        else:
            self.frame_index = 0
            self.animation_time = 0.0

        self.image = self.frames[self.direction][self.frame_index]
        self.rect = self.image.get_rect(center=self.position)
        self.hitbox = self._make_hitbox()

    def _move_axis(self, dx, dy, map_size, obstacle_rects):
        if dx == 0 and dy == 0:
            return

        old_position = self.position.copy()
        self.position.x += dx
        self.position.y += dy
        self.hitbox = self._make_hitbox()
        self._clamp_hitbox_to_map(map_size)
        self.hitbox = self._make_hitbox()

        if self._collides(obstacle_rects):
            self.position = old_position
            self.hitbox = self._make_hitbox()

    def _collides(self, obstacle_rects):
        return any(self.hitbox.colliderect(rect) for rect in obstacle_rects)

    def _animate(self, dt):
        frames = self.frames[self.direction]
        self.animation_time += dt
        if self.animation_time >= 0.12:
            self.animation_time = 0.0
            self.frame_index = (self.frame_index + 1) % len(frames)

    def _make_hitbox(self):
        width, height = PLAYER_HITBOX_SIZE
        hitbox = pygame.Rect(0, 0, width, height)
        hitbox.centerx = round(self.position.x)
        hitbox.bottom = round(self.position.y) + self.rect.height // 2 - 8
        return hitbox

    def _clamp_hitbox_to_map(self, map_size):
        map_width, map_height = map_size
        shift_x = 0
        shift_y = 0

        if self.hitbox.left < 0:
            shift_x = -self.hitbox.left
        elif self.hitbox.right > map_width:
            shift_x = map_width - self.hitbox.right

        if self.hitbox.top < 0:
            shift_y = -self.hitbox.top
        elif self.hitbox.bottom > map_height:
            shift_y = map_height - self.hitbox.bottom

        self.position.x += shift_x
        self.position.y += shift_y

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply_rect(self.rect))

import math
import random

import pygame

from .animation import Animation
from .settings import (
    CATTLE_BACK_DIR,
    CATTLE_DIE_DIR,
    CATTLE_FIGHT_DIR,
    CATTLE_LOOK_DIR,
    CATTLE_RUN_DIR,
    CATTLE_STATION_DIR,
    CATTLE_WALK1_DIR,
    CATTLE_WALK2_DIR,
    MAGIC_DISAPPEAR_DIR,
    MONSTER_ANIMATION_FRAME_LIMIT,
    MONSTER_ANIMATION_FRAME_TIME,
    MONSTER_ATTACK_COOLDOWN,
    MONSTER_ATTACK_DAMAGE,
    MONSTER_CHASE_LEASH,
    MONSTER_CHASE_SPEED,
    MONSTER_DISAPPEAR_FRAME_LIMIT,
    MONSTER_DISAPPEAR_FRAME_TIME,
    MONSTER_LOOK_PADDING,
    MONSTER_MAX_HEALTH,
    MONSTER_PATROL_MOVE_TIME,
    MONSTER_PATROL_PAUSE_TIME,
    MONSTER_PATROL_RADIUS,
    MONSTER_PATROL_SPEED,
    MONSTER_SCALE,
    MONSTER_TRIGGER_PADDING,
)


class Monster:
    STATE_ALIASES = {
        "station": "idle",
    }

    def __init__(self, object_name, x, y, width, height, scale=MONSTER_SCALE):
        self.object_name = object_name or "monster"
        self.scale = scale
        self.title = "妖怪"
        self.max_health = MONSTER_MAX_HEALTH
        self.health = MONSTER_MAX_HEALTH
        self.attack_damage = MONSTER_ATTACK_DAMAGE
        self.attack_cooldown = MONSTER_ATTACK_COOLDOWN
        self.defeated = False
        self.removed = False
        self.disappearing = False
        self.load_error = None
        self.disappear_error = None
        self.animation_errors = {}
        self.state = "idle"
        self.hitbox = pygame.Rect(
            round(x),
            round(y),
            max(1, round(width)),
            max(1, round(height)),
        )
        self.animations = self._load_animations()
        self.disappear_animation = self._load_disappear_animation()
        self.image = self.animations[self.state].current_frame
        self.rect = self.image.get_rect(midbottom=self.hitbox.midbottom)

        # 巡逻 AI：基于世界坐标 hitbox 移动，绘制框由 hitbox 派生，图片尺寸不影响碰撞。
        self.home = pygame.Vector2(self.hitbox.center)
        self.pos = pygame.Vector2(self.hitbox.center)
        self.ai_state = "patrol"
        self.ai_phase = "pause"
        self.ai_timer = random.uniform(0.2, MONSTER_PATROL_PAUSE_TIME)
        self.move_dir = pygame.Vector2(1, 0)

    def _load_animations(self):
        frame_sources = {
            "idle": CATTLE_STATION_DIR,
            "look": CATTLE_LOOK_DIR,
            "walk": CATTLE_WALK1_DIR,
            "walk_alt": CATTLE_WALK2_DIR,
            "run": CATTLE_RUN_DIR,
            "back": CATTLE_BACK_DIR,
            "fight": CATTLE_FIGHT_DIR,
            "die": CATTLE_DIE_DIR,
        }
        loaded_frames = {
            state: self._load_frames(state, directory, MONSTER_ANIMATION_FRAME_LIMIT)
            for state, directory in frame_sources.items()
        }

        fallback = (
            loaded_frames.get("idle")
            or loaded_frames.get("fight")
            or next((frames for frames in loaded_frames.values() if frames), None)
            or [self._placeholder_image()]
        )
        if fallback[0].get_size() == (56, 64):
            self.load_error = "no cattle animation frames could be loaded"

        fallbacks = {
            "idle": fallback,
            "look": loaded_frames.get("idle") or fallback,
            "walk": loaded_frames.get("idle") or fallback,
            "walk_alt": loaded_frames.get("walk") or loaded_frames.get("idle") or fallback,
            "run": loaded_frames.get("walk") or loaded_frames.get("idle") or fallback,
            "back": loaded_frames.get("idle") or fallback,
            "fight": loaded_frames.get("idle") or fallback,
            "die": loaded_frames.get("fight") or loaded_frames.get("idle") or fallback,
        }

        animations = {}
        for state, frames in loaded_frames.items():
            state_frames = frames or fallbacks[state]
            animations[state] = Animation(
                state_frames,
                MONSTER_ANIMATION_FRAME_TIME,
                loop=(state != "die"),
            )
        return animations

    def _load_frames(self, state, directory, limit):
        frames = []
        paths = self._default_direction_paths(directory)[:limit]
        for path in paths:
            try:
                image = pygame.image.load(path).convert_alpha()
                if self.scale != 1:
                    width = max(1, round(image.get_width() * self.scale))
                    height = max(1, round(image.get_height() * self.scale))
                    image = pygame.transform.smoothscale(image, (width, height))
                frames.append(image)
            except Exception as exc:
                self.animation_errors[state] = str(exc)
        return frames

    def _default_direction_paths(self, directory):
        paths = sorted(directory.glob("*.tga"))
        default_paths = [
            path for path in paths
            if path.stem.rsplit("-", 1)[-1].startswith("000")
        ]
        return default_paths or paths

    def _placeholder_image(self):
        image = pygame.Surface((56, 64), pygame.SRCALPHA)
        image.fill((150, 70, 55))
        pygame.draw.rect(image, (255, 235, 160), image.get_rect(), 2)
        return image

    def _load_disappear_animation(self):
        frames = self._load_disappear_frames()
        if not frames:
            return None
        return Animation(frames, MONSTER_DISAPPEAR_FRAME_TIME, loop=False)

    def _load_disappear_frames(self):
        frames = []
        paths = self._default_direction_paths(MAGIC_DISAPPEAR_DIR)[:MONSTER_DISAPPEAR_FRAME_LIMIT]
        for path in paths:
            try:
                image = pygame.image.load(path).convert_alpha()
                width = max(1, round(image.get_width() * self.scale))
                height = max(1, round(image.get_height() * self.scale))
                frames.append(pygame.transform.smoothscale(image, (width, height)))
            except Exception as exc:
                self.disappear_error = str(exc)
        return frames

    @property
    def is_active(self):
        return not self.removed

    @property
    def trigger_rect(self):
        return self.hitbox.inflate(MONSTER_TRIGGER_PADDING, MONSTER_TRIGGER_PADDING)

    @property
    def notice_rect(self):
        return self.hitbox.inflate(MONSTER_LOOK_PADDING, MONSTER_LOOK_PADDING)

    def set_state(self, state):
        if self.removed:
            return

        state = self.STATE_ALIASES.get(state, state)
        if state == self.state or state not in self.animations:
            return

        if self.defeated and state not in ("die",):
            return

        self.state = state
        self.disappearing = False
        self.animations[self.state].reset()
        self._sync_image()

    def update_exploration(self, dt, player_hitbox=None, obstacle_rects=(), map_size=None):
        if self.defeated:
            self.update(dt)
            return

        sees_player = bool(player_hitbox and self.notice_rect.colliderect(player_hitbox))

        # 没有地图信息时退回到原地待机/察觉行为，保证向后兼容与安全。
        if map_size is None:
            self.set_state("look" if sees_player else "idle")
            self.update(dt)
            return

        if self.ai_state == "patrol":
            if sees_player:
                self.ai_state = "alert"
                self.set_state("look")
            else:
                self._update_patrol(dt, obstacle_rects, map_size)
        elif self.ai_state == "alert":
            if not sees_player:
                self.ai_state = "return"
            elif (self.pos - self.home).length() > MONSTER_CHASE_LEASH:
                self.set_state("look")  # 已到牵引上限，原地警戒不再追，避免跑出地图
            else:
                self._update_alert(dt, player_hitbox, obstacle_rects, map_size)
        elif self.ai_state == "return":
            if sees_player:
                self.ai_state = "alert"
            elif self._update_return(dt, obstacle_rects, map_size):
                self.ai_state = "patrol"
                self._begin_patrol_pause()

        self.update(dt)

    def _update_patrol(self, dt, obstacle_rects, map_size):
        self.ai_timer -= dt

        if self.ai_phase == "pause":
            self.set_state("idle")
            if self.ai_timer <= 0:
                self._begin_patrol_walk()
            return

        if (self.pos - self.home).length() > MONSTER_PATROL_RADIUS:
            self.move_dir = self._safe_normalize(self.home - self.pos)

        step = self.move_dir * MONSTER_PATROL_SPEED * dt
        blocked = self._try_move(step.x, step.y, obstacle_rects, map_size)
        self.set_state("walk")

        if blocked:
            self._pick_patrol_direction()
        elif self.ai_timer <= 0:
            self._begin_patrol_pause()

    def _update_alert(self, dt, player_hitbox, obstacle_rects, map_size):
        to_player = pygame.Vector2(player_hitbox.center) - self.pos
        if to_player.length() > 1:
            step = to_player.normalize() * MONSTER_CHASE_SPEED * dt
            self._try_move(step.x, step.y, obstacle_rects, map_size)
        self.set_state("run")

    def _update_return(self, dt, obstacle_rects, map_size):
        to_home = self.home - self.pos
        if to_home.length() <= 4:
            return True

        step = self._safe_normalize(to_home) * MONSTER_PATROL_SPEED * dt
        self.set_state("walk")
        blocked = self._try_move(step.x, step.y, obstacle_rects, map_size)
        # 回家被墙挡住就地恢复巡逻，避免卡死在障碍物上。
        return blocked or (self.home - self.pos).length() <= 4

    def _begin_patrol_walk(self):
        self._pick_patrol_direction()
        self.ai_phase = "walk"
        self.ai_timer = random.uniform(
            MONSTER_PATROL_MOVE_TIME * 0.7,
            MONSTER_PATROL_MOVE_TIME * 1.3,
        )

    def _begin_patrol_pause(self):
        self.ai_phase = "pause"
        self.ai_timer = random.uniform(
            MONSTER_PATROL_PAUSE_TIME * 0.6,
            MONSTER_PATROL_PAUSE_TIME * 1.4,
        )

    def _pick_patrol_direction(self):
        angle = random.uniform(0, 2 * math.pi)
        self.move_dir = pygame.Vector2(math.cos(angle), math.sin(angle))

    def _try_move(self, dx, dy, obstacle_rects, map_size):
        blocked = False
        if dx:
            self.pos.x += dx
            self.hitbox.centerx = round(self.pos.x)
            if self._blocked(obstacle_rects, map_size):
                self.pos.x -= dx
                self.hitbox.centerx = round(self.pos.x)
                blocked = True
        if dy:
            self.pos.y += dy
            self.hitbox.centery = round(self.pos.y)
            if self._blocked(obstacle_rects, map_size):
                self.pos.y -= dy
                self.hitbox.centery = round(self.pos.y)
                blocked = True
        return blocked

    def _blocked(self, obstacle_rects, map_size):
        if map_size:
            map_width, map_height = map_size
            if (
                self.hitbox.left < 0
                or self.hitbox.top < 0
                or self.hitbox.right > map_width
                or self.hitbox.bottom > map_height
            ):
                return True
        return any(self.hitbox.colliderect(rect) for rect in obstacle_rects)

    @staticmethod
    def _safe_normalize(vec):
        if vec.length_squared() == 0:
            return pygame.Vector2(1, 0)
        return vec.normalize()

    def update(self, dt):
        if self.removed:
            return

        if self.state == "disappear":
            self._update_disappear(dt)
            return

        animation = self.animations[self.state]
        animation.update(dt)
        self._sync_image()

        if self.state == "die" and animation.finished:
            self._start_disappear()

    def _update_disappear(self, dt):
        if not self.disappear_animation:
            self.removed = True
            self.disappearing = False
            return

        self.disappear_animation.update(dt)
        self.image = self.disappear_animation.current_frame
        self.rect = self.image.get_rect(midbottom=self.hitbox.midbottom)
        if self.disappear_animation.finished:
            self.removed = True
            self.disappearing = False

    def take_damage(self, amount):
        if self.defeated:
            return

        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.defeated = True
            self.set_state("die")

    def _start_disappear(self):
        if not self.disappear_animation:
            self.removed = True
            return

        self.state = "disappear"
        self.disappearing = True
        self.disappear_animation.reset()
        self.image = self.disappear_animation.current_frame
        self.rect = self.image.get_rect(midbottom=self.hitbox.midbottom)

    def reset_for_retry(self):
        self.health = self.max_health
        self.defeated = False
        self.removed = False
        self.disappearing = False
        if self.disappear_animation:
            self.disappear_animation.reset()
        self.state = "idle"
        self.set_state("fight")

    def _sync_image(self):
        self.image = self.animations[self.state].current_frame
        self.rect = self.image.get_rect(midbottom=self.hitbox.midbottom)

    def draw(self, surface, camera):
        if not self.removed:
            surface.blit(self.image, camera.apply_rect(self.rect))

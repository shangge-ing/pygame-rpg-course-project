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


"""怪物模块。

Monster 表示寺庙中的小怪，包含地图探索时的动画/简单 AI、进入战斗后的血量、
受击、死亡和消失特效。注意：战斗判定使用 hitbox，绘制图片使用 rect，两者分开
可以避免不同动画帧尺寸导致碰撞区域抖动。
"""


class Monster:
    """寺庙小怪实体，负责动画状态、生命值、地图碰撞和死亡流程。"""

    STATE_ALIASES = {
        "station": "idle",
    }

    def __init__(self, object_name, x, y, width, height, scale=MONSTER_SCALE):
        """根据 TMX monster 对象创建怪物，x/y/width/height 来自地图对象层。"""
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
        """加载 cattle 各目录的动画，并为缺失目录准备回退帧。"""
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
        """从指定目录加载某个动画状态的帧，并按缩放比例调整尺寸。"""
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
        """优先选择默认方向帧；如果没有方向规律，就使用目录内全部帧。"""
        paths = sorted(directory.glob("*.tga"))
        default_paths = [
            path for path in paths
            if path.stem.rsplit("-", 1)[-1].startswith("000")
        ]
        return default_paths or paths

    def _placeholder_image(self):
        """怪物素材加载失败时使用占位图，保证流程仍可演示。"""
        image = pygame.Surface((56, 64), pygame.SRCALPHA)
        image.fill((150, 70, 55))
        pygame.draw.rect(image, (255, 235, 160), image.get_rect(), 2)
        return image

    def _load_disappear_animation(self):
        """加载怪物死亡后的消失特效动画。"""
        frames = self._load_disappear_frames()
        if not frames:
            return None
        return Animation(frames, MONSTER_DISAPPEAR_FRAME_TIME, loop=False)

    def _load_disappear_frames(self):
        """从 magic/disappear 目录加载消失特效帧。"""
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
        """怪物是否还应该留在场景中。"""
        return not self.removed

    @property
    def trigger_rect(self):
        """触发战斗的矩形区域，比真实 hitbox 稍大。"""
        return self.hitbox.inflate(MONSTER_TRIGGER_PADDING, MONSTER_TRIGGER_PADDING)

    @property
    def notice_rect(self):
        """怪物发现玩家的警戒范围，用于切换 look/run 状态。"""
        return self.hitbox.inflate(MONSTER_LOOK_PADDING, MONSTER_LOOK_PADDING)

    def set_state(self, state):
        """切换怪物动画状态，并在切换时重置对应动画。"""
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
        """探索状态下更新怪物简单 AI：巡逻、警戒、追击或回家。"""
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
        """小范围巡逻：暂停一会儿，再向随机方向走一小段。"""
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
        """玩家靠近时向玩家方向移动，表现为警戒/追击。"""
        to_player = pygame.Vector2(player_hitbox.center) - self.pos
        if to_player.length() > 1:
            step = to_player.normalize() * MONSTER_CHASE_SPEED * dt
            self._try_move(step.x, step.y, obstacle_rects, map_size)
        self.set_state("run")

    def _update_return(self, dt, obstacle_rects, map_size):
        """离出生点太远或玩家离开后，让怪物回到出生点附近。"""
        to_home = self.home - self.pos
        if to_home.length() <= 4:
            return True

        step = self._safe_normalize(to_home) * MONSTER_PATROL_SPEED * dt
        self.set_state("walk")
        blocked = self._try_move(step.x, step.y, obstacle_rects, map_size)
        # 回家被墙挡住就地恢复巡逻，避免卡死在障碍物上。
        return blocked or (self.home - self.pos).length() <= 4

    def _begin_patrol_walk(self):
        """进入巡逻移动阶段，并随机一个移动方向。"""
        self._pick_patrol_direction()
        self.ai_phase = "walk"
        self.ai_timer = random.uniform(
            MONSTER_PATROL_MOVE_TIME * 0.7,
            MONSTER_PATROL_MOVE_TIME * 1.3,
        )

    def _begin_patrol_pause(self):
        """进入巡逻停顿阶段。"""
        self.ai_phase = "pause"
        self.ai_timer = random.uniform(
            MONSTER_PATROL_PAUSE_TIME * 0.6,
            MONSTER_PATROL_PAUSE_TIME * 1.4,
        )

    def _pick_patrol_direction(self):
        """随机选择一个二维移动方向。"""
        angle = random.uniform(0, 2 * math.pi)
        self.move_dir = pygame.Vector2(math.cos(angle), math.sin(angle))

    def _try_move(self, dx, dy, obstacle_rects, map_size):
        """按 X/Y 方向尝试移动怪物，撞到障碍物或地图边界就回退。"""
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
        """判断怪物 hitbox 是否越界或碰到障碍物。"""
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
        """安全归一化向量，避免零向量 normalize 报错。"""
        if vec.length_squared() == 0:
            return pygame.Vector2(1, 0)
        return vec.normalize()

    def update(self, dt):
        """更新当前动画状态；死亡动画播完后进入消失特效。"""
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
        """播放死亡消失特效，播完后把怪物标记为 removed。"""
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
        """扣除怪物血量；血量归零后进入 die 状态。"""
        if self.defeated:
            return

        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.defeated = True
            self.set_state("die")

    def _start_disappear(self):
        """从死亡动画切换到 disappear 特效；没有特效时直接移除。"""
        if not self.disappear_animation:
            self.removed = True
            return

        self.state = "disappear"
        self.disappearing = True
        self.disappear_animation.reset()
        self.image = self.disappear_animation.current_frame
        self.rect = self.image.get_rect(midbottom=self.hitbox.midbottom)

    def reset_for_retry(self):
        """玩家失败后重试战斗时，把怪物恢复到可战斗状态。"""
        self.health = self.max_health
        self.defeated = False
        self.removed = False
        self.disappearing = False
        if self.disappear_animation:
            self.disappear_animation.reset()
        self.state = "idle"
        self.set_state("fight")

    def _sync_image(self):
        """把当前动画帧同步到 image，并用底部中心锚点保持位置稳定。"""
        self.image = self.animations[self.state].current_frame
        self.rect = self.image.get_rect(midbottom=self.hitbox.midbottom)

    def draw(self, surface, camera):
        """按摄像机偏移绘制怪物，已移除的怪物不再绘制。"""
        if not self.removed:
            surface.blit(self.image, camera.apply_rect(self.rect))

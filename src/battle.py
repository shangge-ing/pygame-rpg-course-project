import pygame

from .animation import Animation
from .settings import (
    BATTLE_EFFECT_FRAME_LIMIT,
    BATTLE_EFFECT_FRAME_TIME,
    BATTLE_HIT_FLASH_TIME,
    BATTLE_VICTORY_SECONDS,
    MAGIC_APPEAR_DIR,
    MONSTER_FIRST_ATTACK_DELAY,
    PLAYER_ATTACK_DAMAGE,
    PLAYER_MAX_HEALTH,
    SWK2_ATTACK_FRAME_COUNT,
    SWK2_ATTACK_FRAME_START,
    SWK2_ATTACK_FRAME_TIME,
    SWK2_BATTLE_SCALE,
    SWK2_DIR,
)


class Battle:
    def __init__(self, monster, font_path, window_size):
        self.monster = monster
        self.player_health = PLAYER_MAX_HEALTH
        self.victory = False
        self.finished = False
        self.player_defeated = False
        self.victory_timer = BATTLE_VICTORY_SECONDS
        self.monster_attack_timer = MONSTER_FIRST_ATTACK_DELAY
        self.hit_flash_timer = 0.0
        self.window_width, self.window_height = window_size
        self.font_error = None
        self.effect_error = None
        self.effect_frames = self._load_effect_frames()
        self.effect_index = 0
        self.effect_time = 0.0
        self.effect_active = False
        self.attack_animation_error = None
        self.attack_frame_paths = []
        self.attack_animation = self._load_attack_animation()
        self.attack_active = False
        self.title_font = self._load_font(font_path, 36)
        self.text_font = self._load_font(font_path, 24)
        self.monster.set_state("fight")

    def _load_font(self, font_path, size):
        try:
            return pygame.font.Font(str(font_path), size)
        except Exception as exc:
            self.font_error = str(exc)
            return pygame.font.Font(None, size)

    def _load_effect_frames(self):
        frames = []
        try:
            paths = sorted(MAGIC_APPEAR_DIR.glob("*.tga"))[:BATTLE_EFFECT_FRAME_LIMIT]
            for path in paths:
                image = pygame.image.load(path).convert_alpha()
                width = max(1, round(image.get_width() * 0.45))
                height = max(1, round(image.get_height() * 0.45))
                frames.append(pygame.transform.smoothscale(image, (width, height)))
        except Exception as exc:
            self.effect_error = str(exc)
        return frames

    def _load_attack_animation(self):
        try:
            paths = sorted(SWK2_DIR.glob("*.png"))
            start = max(0, SWK2_ATTACK_FRAME_START - 1)
            selected = paths[start:start + SWK2_ATTACK_FRAME_COUNT]
            if not selected:
                raise FileNotFoundError(f"no swk2 attack frames found in {SWK2_DIR}")

            frames = []
            for path in selected:
                image = pygame.image.load(path).convert_alpha()
                width = max(1, round(image.get_width() * SWK2_BATTLE_SCALE))
                height = max(1, round(image.get_height() * SWK2_BATTLE_SCALE))
                frames.append(pygame.transform.smoothscale(image, (width, height)))

            self.attack_frame_paths = selected
            return Animation(frames, SWK2_ATTACK_FRAME_TIME, loop=False)
        except Exception as exc:
            self.attack_animation_error = str(exc)
            return None

    def attack(self):
        if self.victory or self.finished or self.player_defeated:
            return None

        if self.attack_active and self.attack_animation and not self.attack_animation.finished:
            return None

        self._start_attack_animation()
        self._start_effect()
        self.monster.take_damage(PLAYER_ATTACK_DAMAGE)
        if self.monster.defeated:
            self.victory = True
            self.victory_timer = BATTLE_VICTORY_SECONDS
            return "victory"

        return "hit"

    def update(self, dt):
        self.monster.update(dt)
        self._update_attack_animation(dt)
        self._update_effect(dt)
        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)

        if self.victory:
            self.victory_timer -= dt
            if self.victory_timer <= 0 and self.monster.removed:
                self.finished = True
            return

        if self.finished or self.player_defeated:
            return

        self._update_monster_attack(dt)

    def _update_monster_attack(self, dt):
        self.monster_attack_timer -= dt
        if self.monster_attack_timer > 0:
            return

        self.monster_attack_timer = self.monster.attack_cooldown
        self.player_health = max(0, self.player_health - self.monster.attack_damage)
        self.hit_flash_timer = BATTLE_HIT_FLASH_TIME
        swing = self.monster.animations.get(self.monster.state)
        if swing:
            swing.reset()
        if self.player_health <= 0:
            self.player_defeated = True

    def _start_effect(self):
        if not self.effect_frames:
            return

        self.effect_active = True
        self.effect_index = 0
        self.effect_time = 0.0

    def _update_effect(self, dt):
        if not self.effect_active or not self.effect_frames:
            return

        self.effect_time += dt
        if self.effect_time >= BATTLE_EFFECT_FRAME_TIME:
            self.effect_time = 0.0
            self.effect_index += 1
            if self.effect_index >= len(self.effect_frames):
                self.effect_active = False
                self.effect_index = 0

    def _start_attack_animation(self):
        if not self.attack_animation:
            return

        self.attack_animation.reset()
        self.attack_active = True

    def _update_attack_animation(self, dt):
        if not self.attack_active or not self.attack_animation:
            return

        self.attack_animation.update(dt)
        if self.attack_animation.finished:
            self.attack_active = False

    def draw(self, surface):
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(80, 92, self.window_width - 160, 300)
        pygame.draw.rect(surface, (24, 24, 32), panel)
        pygame.draw.rect(surface, (232, 214, 160), panel, 3)

        title = "战斗胜利" if self.victory else f"遭遇{self.monster.title}"
        self._blit_text(surface, self.title_font, title, panel.left + 28, panel.top + 26, (255, 232, 150))
        self._draw_player(surface, panel)
        self._draw_monster(surface, panel)

        y = panel.top + 92
        self._draw_health_bar(surface, "玩家血量", self.player_health, PLAYER_MAX_HEALTH, panel.left + 32, y)
        self._draw_health_bar(
            surface,
            "怪物血量",
            self.monster.health,
            self.monster.max_health,
            panel.left + 32,
            y + 64,
        )

        if self.victory:
            hint = "战斗胜利，正在返回寺庙。"
        elif getattr(self.monster, "enraged", False):
            hint = f"{self.monster.title}暴怒，攻势凶猛！按 J 拼命反击！"
        elif self.hit_flash_timer > 0:
            hint = "妖怪反击,损失血量!按 J 反击,按 Esc 撤退。"
        else:
            hint = "按 J 攻击妖怪，按 Esc 撤退。当心妖怪反击！"
        self._blit_text(surface, self.text_font, hint, panel.left + 32, panel.bottom - 64, (245, 245, 245))

    def _draw_health_bar(self, surface, label, value, maximum, x, y):
        self._blit_text(surface, self.text_font, f"{label}: {value}/{maximum}", x, y, (245, 245, 245))
        bar_rect = pygame.Rect(x + 150, y + 6, 300, 18)
        pygame.draw.rect(surface, (70, 70, 80), bar_rect)
        fill_width = round(bar_rect.width * max(0, value) / maximum)
        if fill_width:
            pygame.draw.rect(surface, (190, 54, 54), (bar_rect.x, bar_rect.y, fill_width, bar_rect.height))
        pygame.draw.rect(surface, (230, 230, 230), bar_rect, 2)

    def _draw_monster(self, surface, panel):
        monster_rect = self.monster.image.get_rect(midbottom=(panel.right - 112, panel.bottom - 48))
        surface.blit(self.monster.image, monster_rect)

        if self.effect_active and self.effect_frames:
            effect = self.effect_frames[self.effect_index]
            effect_rect = effect.get_rect(center=monster_rect.center)
            surface.blit(effect, effect_rect)

    def _draw_player(self, surface, panel):
        player_anchor = (panel.left + 108, panel.bottom - 22)
        if self.attack_animation:
            image = self.attack_animation.current_frame
            player_rect = image.get_rect(midbottom=player_anchor)
            surface.blit(image, player_rect)
        else:
            player_rect = pygame.Rect(0, 0, 90, 130)
            player_rect.midbottom = player_anchor

        if self.hit_flash_timer > 0:
            flash = pygame.Surface(player_rect.size, pygame.SRCALPHA)
            alpha = int(150 * (self.hit_flash_timer / BATTLE_HIT_FLASH_TIME))
            flash.fill((220, 40, 40, alpha))
            surface.blit(flash, player_rect)

    def _blit_text(self, surface, font, text, x, y, color):
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, (x, y))

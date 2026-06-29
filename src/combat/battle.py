"""回合制战斗系统模块。

Battle 是一个覆盖在当前地图上的回合制战斗状态。它负责玩家回合菜单、普通攻击、
技能攻击、防御、撤退、怪物回合、战斗日志、孙悟空 swk2 攻击动画、命中特效，
以及胜利/失败判定。Game 只负责把键盘事件交给 Battle，并根据结果切回探索或失败界面。
"""

import pygame

from ..presentation.animation import Animation
from ..config.settings import (
    BATTLE_EFFECT_FRAME_LIMIT,
    BATTLE_EFFECT_FRAME_TIME,
    BATTLE_HIT_FLASH_TIME,
    BATTLE_VICTORY_SECONDS,
    DEFEND_DAMAGE_RATE,
    MAGIC_APPEAR_DIR,
    PLAYER_MAX_HEALTH,
    PLAYER_NORMAL_ATTACK_DAMAGE,
    PLAYER_SKILL_COOLDOWN_TURNS,
    PLAYER_SKILL_DAMAGE,
    SWK2_ATTACK_FRAME_COUNT,
    SWK2_ATTACK_FRAME_START,
    SWK2_ATTACK_FRAME_TIME,
    SWK2_BATTLE_SCALE,
    SWK2_DIR,
)


PLAYER_TURN = "PLAYER_TURN"
PLAYER_ATTACKING = "PLAYER_ATTACKING"
PLAYER_SKILL = "PLAYER_SKILL"
ENEMY_TURN = "ENEMY_TURN"
ENEMY_ATTACKING = "ENEMY_ATTACKING"
VICTORY = "VICTORY"
DEFEAT = "DEFEAT"
ESCAPED = "ESCAPED"


class Battle:
    """一次玩家与某个怪物或 Boss 的回合制战斗。"""

    LOG_LIMIT = 5

    def __init__(self, monster, font_path, window_size):
        """创建战斗对象，并把怪物切换到 fight 动画状态。"""
        self.monster = monster
        self.player_health = PLAYER_MAX_HEALTH
        self.phase = PLAYER_TURN
        self.phase_timer = 0.0
        self.victory = False
        self.finished = False
        self.player_defeated = False
        self.escaped = False
        self.pending_victory = False
        self.victory_timer = BATTLE_VICTORY_SECONDS
        self.hit_flash_timer = 0.0
        self.skill_cooldown = 0
        self.defending = False
        self.logs = []
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
        self.title_font = self._load_font(font_path, 34)
        self.text_font = self._load_font(font_path, 23)
        self.small_font = self._load_font(font_path, 20)
        self.monster.set_facing("left")
        self.monster.set_state("fight")
        self._add_log(f"遭遇{self.monster.title}，进入玩家回合。")

    def _load_font(self, font_path, size):
        """加载战斗界面字体，失败时退回 pygame 默认字体。"""
        try:
            return pygame.font.Font(str(font_path), size)
        except Exception as exc:
            self.font_error = str(exc)
            return pygame.font.Font(None, size)

    def _load_effect_frames(self):
        """加载 magic/appear 命中特效帧。"""
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
        """加载 swk2 中选定的一段帧，作为玩家战斗攻击动画。"""
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

    def handle_key(self, key):
        """处理战斗按键，只在玩家回合接受行动输入。"""
        if self.phase == VICTORY and key == pygame.K_ESCAPE:
            self.finished = True
            return "finish_victory"

        if self.phase != PLAYER_TURN:
            return None

        if key == pygame.K_ESCAPE:
            self.escape()
            return "escaped"
        if key in (pygame.K_j, pygame.K_1, pygame.K_KP1):
            return self._player_attack("normal")
        if key in (pygame.K_k, pygame.K_2, pygame.K_KP2):
            return self._player_attack("skill")
        if key in (pygame.K_d, pygame.K_3, pygame.K_KP3):
            return self._defend()
        return None

    def attack(self):
        """兼容旧调用：执行一次普通攻击。"""
        return self._player_attack("normal")

    def escape(self):
        """玩家撤退，战斗结束但不进入失败界面。"""
        if self.phase != PLAYER_TURN:
            return
        self.escaped = True
        self.finished = True
        self.phase = ESCAPED
        self._add_log("孙悟空暂时撤出战斗。")

    def update(self, dt):
        """更新战斗动画、回合状态、敌人行动、胜利等待和失败状态。"""
        self.monster.update(dt)
        self._update_attack_animation(dt)
        self._update_effect(dt)
        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)

        if self.phase == VICTORY:
            if self.monster.removed:
                self.victory_timer -= dt
                if self.victory_timer <= 0:
                    self.finished = True
            return

        if self.phase in (DEFEAT, ESCAPED) or self.finished:
            return

        if self.phase in (PLAYER_ATTACKING, PLAYER_SKILL):
            self.phase_timer = max(0.0, self.phase_timer - dt)
            if not self.attack_active and self.phase_timer <= 0:
                if self.pending_victory or self.monster.defeated:
                    self._enter_victory()
                else:
                    self._begin_enemy_turn()
            return

        if self.phase == ENEMY_TURN:
            self.phase_timer = max(0.0, self.phase_timer - dt)
            if self.phase_timer <= 0:
                self._start_enemy_attack()
            return

        if self.phase == ENEMY_ATTACKING:
            self.phase_timer = max(0.0, self.phase_timer - dt)
            if not self.player_defeated and self.phase_timer <= 0:
                self._begin_player_turn()

    def _player_attack(self, attack_type):
        """执行玩家普通攻击或技能攻击，并保证一次按键只结算一次伤害。"""
        if self.phase != PLAYER_TURN or self.victory or self.finished or self.player_defeated:
            return None

        if attack_type == "skill":
            if self.skill_cooldown > 0:
                self._add_log(f"技能冷却中，还需 {self.skill_cooldown} 回合。")
                return None
            damage = PLAYER_SKILL_DAMAGE
            self.skill_cooldown = PLAYER_SKILL_COOLDOWN_TURNS
            self.phase = PLAYER_SKILL
            action_name = "技能攻击"
            result = "skill_attack"
        else:
            damage = PLAYER_NORMAL_ATTACK_DAMAGE
            self.phase = PLAYER_ATTACKING
            action_name = "普通攻击"
            result = "normal_attack"

        self.defending = False
        self.phase_timer = 0.35
        self.pending_victory = False
        self._start_attack_animation()
        self._start_effect()
        self.monster.take_damage(damage)
        self._add_log(f"孙悟空使用{action_name}，造成 {damage} 点伤害。")
        if self.monster.defeated:
            self.pending_victory = True
            self._add_log(f"{self.monster.title}被击败了！")
            return "victory"
        return result

    def _defend(self):
        """玩家选择防御，本回合怪物攻击伤害减半。"""
        if self.phase != PLAYER_TURN:
            return None
        self.defending = True
        self._add_log("孙悟空进入防御姿态，本回合受到伤害减半。")
        self._begin_enemy_turn()
        return "defend"

    def _begin_enemy_turn(self):
        """玩家行动结束后进入怪物回合。"""
        self.phase = ENEMY_TURN
        self.phase_timer = 0.45
        self._add_log(f"轮到{self.monster.title}行动。")

    def _start_enemy_attack(self):
        """怪物自动攻击玩家，并根据防御状态计算伤害。"""
        self.phase = ENEMY_ATTACKING
        self.phase_timer = 0.65
        self.monster.set_facing("left")
        self.monster.set_state("fight")
        swing = self.monster.animations.get(self.monster.state)
        if swing:
            swing.reset()

        damage = self.monster.attack_damage
        if self.defending:
            damage = max(1, round(damage * DEFEND_DAMAGE_RATE))
        self.player_health = max(0, self.player_health - damage)
        self.hit_flash_timer = BATTLE_HIT_FLASH_TIME
        self._add_log(f"{self.monster.title}发动攻击，造成 {damage} 点伤害。")
        if self.player_health <= 0:
            self.phase = DEFEAT
            self.player_defeated = True
            self._add_log("孙悟空体力耗尽，战斗失败。")

    def _begin_player_turn(self):
        """怪物行动结束后回到玩家回合，并推进技能冷却。"""
        self.defending = False
        if self.skill_cooldown > 0:
            self.skill_cooldown -= 1
        self.phase = PLAYER_TURN
        self._add_log("回到玩家回合。")

    def _enter_victory(self):
        """怪物死亡后进入胜利等待，等待 die/disappear 动画播完。"""
        self.victory = True
        self.phase = VICTORY
        self.victory_timer = BATTLE_VICTORY_SECONDS

    def _start_effect(self):
        """启动命中特效动画。"""
        if not self.effect_frames:
            return

        self.effect_active = True
        self.effect_index = 0
        self.effect_time = 0.0

    def _update_effect(self, dt):
        """推进命中特效帧，播完后自动关闭。"""
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
        """启动孙悟空攻击动画。"""
        if not self.attack_animation:
            self.attack_active = False
            return

        self.attack_animation.reset()
        self.attack_active = True

    def _update_attack_animation(self, dt):
        """推进孙悟空攻击动画，播完前不允许下一次玩家行动。"""
        if not self.attack_active or not self.attack_animation:
            return

        self.attack_animation.update(dt)
        if self.attack_animation.finished:
            self.attack_active = False

    def _add_log(self, message):
        """追加战斗日志，只保留最近几行。"""
        self.logs.append(message)
        if len(self.logs) > self.LOG_LIMIT:
            self.logs = self.logs[-self.LOG_LIMIT:]

    def draw(self, surface):
        """绘制战斗覆盖层、血条、回合菜单、角色、怪物和战斗日志。"""
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(56, 64, self.window_width - 112, 470)
        pygame.draw.rect(surface, (24, 24, 32), panel)
        pygame.draw.rect(surface, (232, 214, 160), panel, 3)

        title = "战斗胜利" if self.victory else f"遭遇{self.monster.title}"
        self._blit_text(surface, self.title_font, title, panel.left + 28, panel.top + 22, (255, 232, 150))
        self._draw_player(surface, panel)
        self._draw_monster(surface, panel)

        y = panel.top + 78
        self._draw_health_bar(surface, "玩家血量", self.player_health, PLAYER_MAX_HEALTH, panel.left + 30, y)
        self._draw_health_bar(
            surface,
            "怪物血量",
            self.monster.health,
            self.monster.max_health,
            panel.left + 30,
            y + 42,
        )

        self._draw_turn_info(surface, panel)
        self._draw_logs(surface, panel)

    def _draw_turn_info(self, surface, panel):
        """绘制当前回合、操作菜单和技能冷却状态。"""
        menu_rect = pygame.Rect(panel.left + 250, panel.top + 156, 278, 142)
        pygame.draw.rect(surface, (18, 20, 26), menu_rect)
        pygame.draw.rect(surface, (92, 92, 110), menu_rect, 1)

        x = menu_rect.left + 14
        y = menu_rect.top + 12
        self._blit_text(surface, self.text_font, self._phase_text(), x, y, (255, 232, 150))

        y += 32
        if self.phase == PLAYER_TURN:
            cooldown_text = "可用" if self.skill_cooldown == 0 else f"冷却 {self.skill_cooldown} 回合"
            lines = [
                "1 / J：普通攻击",
                f"2 / K：技能攻击（{cooldown_text}）",
                "3 / D：防御",
                "Esc：撤退",
            ]
        elif self.phase in (PLAYER_ATTACKING, PLAYER_SKILL):
            lines = ["孙悟空正在行动..."]
        elif self.phase in (ENEMY_TURN, ENEMY_ATTACKING):
            lines = [f"{self.monster.title}回合，准备攻击..."]
        elif self.phase == VICTORY:
            lines = ["战斗胜利，等待怪物消失。"]
        elif self.phase == DEFEAT:
            lines = ["战斗失败。"]
        elif self.phase == ESCAPED:
            lines = ["已撤退。"]
        else:
            lines = []

        for line in lines:
            self._blit_text(surface, self.small_font, line, x, y, (245, 245, 245))
            y += 24

    def _draw_logs(self, surface, panel):
        """绘制最近几条战斗日志。"""
        log_rect = pygame.Rect(panel.left + 30, panel.top + 322, panel.width - 60, 120)
        pygame.draw.rect(surface, (18, 20, 26), log_rect)
        pygame.draw.rect(surface, (92, 92, 110), log_rect, 1)
        self._blit_text(surface, self.small_font, "战斗日志", log_rect.left + 12, log_rect.top + 8, (255, 232, 150))
        y = log_rect.top + 36
        for line in self.logs[-self.LOG_LIMIT:]:
            self._blit_text(surface, self.small_font, line, log_rect.left + 12, y, (235, 235, 235))
            y += 22

    def _phase_text(self):
        """把内部战斗状态转换成 UI 文字。"""
        labels = {
            PLAYER_TURN: "玩家回合",
            PLAYER_ATTACKING: "玩家攻击中",
            PLAYER_SKILL: "玩家技能攻击中",
            ENEMY_TURN: "怪物回合",
            ENEMY_ATTACKING: "怪物攻击中",
            VICTORY: "战斗胜利",
            DEFEAT: "战斗失败",
            ESCAPED: "已撤退",
        }
        return labels.get(self.phase, self.phase)

    def _draw_health_bar(self, surface, label, value, maximum, x, y):
        """绘制玩家或怪物血条。"""
        self._blit_text(surface, self.small_font, f"{label}: {value}/{maximum}", x, y, (245, 245, 245))
        bar_rect = pygame.Rect(x + 150, y + 5, 280, 17)
        pygame.draw.rect(surface, (70, 70, 80), bar_rect)
        fill_width = round(bar_rect.width * max(0, value) / maximum)
        if fill_width:
            pygame.draw.rect(surface, (190, 54, 54), (bar_rect.x, bar_rect.y, fill_width, bar_rect.height))
        pygame.draw.rect(surface, (230, 230, 230), bar_rect, 2)

    def _draw_monster(self, surface, panel):
        """在战斗面板右侧绘制怪物，并在命中时绘制特效。"""
        monster_rect = self.monster.image.get_rect(midbottom=(panel.right - 112, panel.top + 242))
        surface.blit(self.monster.image, monster_rect)

        if self.effect_active and self.effect_frames:
            effect = self.effect_frames[self.effect_index]
            effect_rect = effect.get_rect(center=monster_rect.center)
            surface.blit(effect, effect_rect)

    def _draw_player(self, surface, panel):
        """在战斗面板左侧绘制孙悟空攻击动画或占位区域。"""
        player_anchor = (panel.left + 112, panel.top + 256)
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
        """渲染一行文字到指定位置。"""
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, (x, y))

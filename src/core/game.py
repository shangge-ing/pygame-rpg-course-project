"""游戏主控制模块。

Game 是整个项目的调度中心：初始化 pygame 和各类资源，管理当前游戏状态，
处理键盘输入，切换村庄/郊外/森林/寺庙场景，触发 NPC 对话、战斗、Boss 和最终完成界面。
其他模块负责具体对象行为，Game 负责把它们串成完整流程。
"""

import pygame

from ..presentation.audio import AudioManager
from ..combat.battle import Battle
from ..combat.boss import Boss
from ..character.camera import Camera
from ..story.dialog import DialogBox
from .game_state import GameState
from ..character.player import Player
from ..story.quest import QuestManager, QuestStage
from ..world.scene import Scene
from ..config.settings import (
    ATTACK_SOUND_PATH,
    BACKGROUND_MUSIC_PATH,
    BOSS_BANNER_SECONDS,
    DEFAULT_FOREST_SPAWN,
    DEFAULT_OUTSKIRTS_SPAWN,
    DEFAULT_PLAYER_SPAWN,
    DEFAULT_TEMPLE_SPAWN,
    FOREST_RETURN_FROM_TEMPLE_SPAWN,
    FOREST_MAP_PATH,
    FONT_PATH,
    FPS,
    FAIL_IMAGE_PATH,
    MUSIC_VOLUME,
    NPC_INTERACTION_PADDING,
    NO_BUTTON_PATH,
    OK_BUTTON_PATH,
    OUTSKIRTS_EXIT_BAND,
    OUTSKIRTS_MAP_PATH,
    SOUND_VOLUME,
    SMALL_TEMPLE_BUTTON_PATH,
    START_BACKGROUND_PATH,
    SWK_DIR,
    TEMPLE_FALLBACK_MAP_PATH,
    TEMPLE_BUTTON_PATH,
    TEMPLE_MAP_PATH,
    VICTORY_SOUND_PATH,
    VILLAGE_BUTTON_PATH,
    VILLAGE_MAP_PATH,
    WIN_IMAGE_PATH,
    WINDOW_SIZE,
)
from ..presentation.ui import UI


class Game:
    """主游戏类，封装初始化、主循环、事件处理、更新和绘制。"""

    def __init__(self):
        """初始化窗口、资源管理器、UI、场景、玩家、任务和初始状态。"""
        pygame.init()
        pygame.display.set_caption("Journey to the West")
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.dialog_box = DialogBox(FONT_PATH, WINDOW_SIZE)
        self.audio = AudioManager(
            BACKGROUND_MUSIC_PATH,
            ATTACK_SOUND_PATH,
            VICTORY_SOUND_PATH,
            MUSIC_VOLUME,
            SOUND_VOLUME,
        )
        self.ui = UI(
            FONT_PATH,
            WINDOW_SIZE,
            START_BACKGROUND_PATH,
            {
                "ok": OK_BUTTON_PATH,
                "no": NO_BUTTON_PATH,
                "small_temple": SMALL_TEMPLE_BUTTON_PATH,
                "village": VILLAGE_BUTTON_PATH,
                "temple": TEMPLE_BUTTON_PATH,
            },
        )
        self.win_image, self.win_image_error = self._load_overlay_image(WIN_IMAGE_PATH)
        self.fail_image, self.fail_image_error = self._load_overlay_image(FAIL_IMAGE_PATH)
        self.scene = self._create_village_scene()
        self.player = Player(SWK_DIR, self.scene.player_spawn)
        self.camera = Camera(WINDOW_SIZE, self.scene.pixel_size)
        self.active_npc = None
        self.battle = None
        self.battle_blocked_monster = None
        self.quest = QuestManager()
        self.state = GameState.START
        self.paused_state = GameState.VILLAGE_EXPLORING
        self.complete_message_visible = False
        self.failure_message_visible = False
        self.failure_reason = None
        self.boss_banner_timer = 0.0
        self.camera.update(self.player.rect)

        if self.player.load_error:
            print(f"Player image load failed, using placeholder: {self.player.load_error}")
        self._report_npc_load_issues()
        self._report_monster_load_issues()
        if self.dialog_box.font_error:
            print(f"Dialog font load failed, using default font: {self.dialog_box.font_error}")
        if self.ui.font_error:
            print(f"UI font load failed, using default font: {self.ui.font_error}")
        if self.ui.start_background_error:
            print(f"Start background load failed, using plain background: {self.ui.start_background_error}")
        for button_name, error in self.ui.button_errors.items():
            print(f"Button image load failed for {button_name}, using text button: {error}")
        if self.dialog_box.image_error:
            print(f"Dialog image load failed, using drawn box: {self.dialog_box.image_error}")
        if self.dialog_box.portrait_error:
            print(f"God dialog portrait load failed, continuing without it: {self.dialog_box.portrait_error}")
        if self.win_image_error:
            print(f"Win image load failed, using drawn overlay: {self.win_image_error}")
        if self.fail_image_error:
            print(f"Fail image load failed, using drawn overlay: {self.fail_image_error}")

    def _load_overlay_image(self, image_path):
        """加载胜利/失败背景图，并缩放到窗口大小；失败时返回错误信息。"""
        try:
            image = pygame.image.load(image_path).convert()
            return pygame.transform.smoothscale(image, WINDOW_SIZE), None
        except Exception as exc:
            return None, str(exc)

    def _create_village_scene(self):
        """创建村庄场景。"""
        return Scene.village(VILLAGE_MAP_PATH, DEFAULT_PLAYER_SPAWN)

    def _create_outskirts_scene(self):
        """创建郊外过渡场景。"""
        return Scene.outskirts(OUTSKIRTS_MAP_PATH, DEFAULT_OUTSKIRTS_SPAWN)

    def _create_forest_scene(self):
        """创建森林过渡场景。"""
        return Scene.forest(FOREST_MAP_PATH, DEFAULT_FOREST_SPAWN)

    def _create_temple_scene(self):
        """创建寺庙场景，temple1.tmx 失败时退回 temple.tmx。"""
        try:
            return Scene.temple(TEMPLE_MAP_PATH, DEFAULT_TEMPLE_SPAWN)
        except Exception as exc:
            print(f"temple1.tmx load failed, falling back to temple.tmx: {exc}")
            return Scene.temple(TEMPLE_FALLBACK_MAP_PATH, DEFAULT_TEMPLE_SPAWN)

    def _report_npc_load_issues(self):
        """打印 NPC 图片或动画加载失败信息，便于调试资源问题。"""
        for npc in self.scene.npcs:
            if npc.load_error:
                print(
                    f"NPC image load failed for {npc.layer_name}:{npc.object_name}, "
                    f"using placeholder: {npc.load_error}"
                )
            if npc.animation_error:
                print(
                    f"NPC animation load failed for {npc.layer_name}:{npc.object_name}, "
                    f"using static image: {npc.animation_error}"
                )

    def _report_monster_load_issues(self):
        """打印怪物图片、动画和消失特效加载失败信息。"""
        for monster in self.scene.monsters:
            if monster.load_error:
                print(
                    f"Monster image load failed for {monster.object_name}, "
                    f"using placeholder: {monster.load_error}"
                )
            for state_name, error in monster.animation_errors.items():
                print(
                    f"Monster animation load failed for {monster.object_name}:{state_name}, "
                    f"using fallback animation: {error}"
                )
            if monster.disappear_error:
                print(
                    f"Monster disappear effect load failed for {monster.object_name}, "
                    f"removing instantly on defeat: {monster.disappear_error}"
                )

    def run(self):
        """游戏主循环：处理输入、更新状态、绘制画面，直到窗口关闭。"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self._handle_events()
            self._update(dt)
            self._draw()

        pygame.quit()

    def _handle_events(self):
        """统一分发 pygame 事件，根据当前状态交给对应处理函数。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.audio.toggle_mute()
            elif self.state == GameState.START:
                self._handle_start_event(event)
            elif self.state == GameState.HELP:
                self._handle_help_event(event)
            elif self.state == GameState.PAUSED:
                self._handle_pause_event(event)
            elif self.complete_message_visible:
                self._handle_complete_event(event)
            elif self.failure_message_visible:
                self._handle_failure_event(event)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self._pause()
            elif self.battle:
                self._handle_battle_event(event)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.active_npc:
                    self._close_dialog()
                else:
                    self.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_SPACE):
                self._handle_interact()

    def _handle_start_event(self, event):
        """开始界面按键：Enter 开始、H 帮助、Esc 退出。"""
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN:
            self._sync_state()
        elif event.key == pygame.K_h:
            self.state = GameState.HELP
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def _handle_help_event(self, event):
        """帮助界面按 Esc 返回开始界面。"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.START

    def _handle_pause_event(self, event):
        """暂停界面按 P 继续，按 Esc 退出游戏。"""
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_p:
            self.state = self.paused_state
            self._sync_state()
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def _handle_complete_event(self, event):
        """完成界面按 Esc 退出游戏。"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False

    def _handle_failure_event(self, event):
        """失败界面按 R 重试当前战斗，按 Esc 退出。"""
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_r:
            self._retry_battle()
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def _pause(self):
        """进入暂停状态，并记录暂停前的探索/战斗状态。"""
        self.paused_state = self.state
        self.state = GameState.PAUSED

    def _handle_battle_event(self, event):
        """战斗状态按键：把玩家选择交给 Battle 的回合制状态机处理。"""
        if event.type != pygame.KEYDOWN:
            return

        result = self.battle.handle_key(event.key)
        if result in ("normal_attack", "skill_attack", "victory"):
            self.audio.play_attack()
        if result == "victory":
            self.audio.play_victory()
        elif result == "escaped":
            self._exit_battle_escape()
        elif result == "finish_victory":
            self.battle = None
            self._check_final_completion()

    def _enter_battle_failure(self, reason):
        """进入战斗失败/撤退界面，并暂时阻止同一怪物立刻再次触发战斗。"""
        monster = self.battle.monster
        self.battle_blocked_monster = monster
        monster.set_state("station")
        monster.ai_state = "patrol"
        self.failure_reason = reason
        self.failure_message_visible = True
        self.battle = None
        self._sync_state()

    def _exit_battle_escape(self):
        """玩家主动撤退，回到寺庙探索，并阻止贴着同一怪物时立刻重进战斗。"""
        monster = self.battle.monster
        self.battle_blocked_monster = monster
        monster.set_state("station")
        monster.ai_state = "patrol"
        self.battle = None
        self._sync_state()

    def _retry_battle(self):
        """失败或撤退后重新挑战同一只怪物。"""
        monster = self.battle_blocked_monster
        self.failure_message_visible = False
        self.failure_reason = None

        if monster and not monster.removed:
            monster.reset_for_retry()
            self.battle = Battle(monster, FONT_PATH, WINDOW_SIZE)
            if self.battle.font_error:
                print(f"Battle font load failed, using default font: {self.battle.font_error}")
            if self.battle.effect_error:
                print(f"Battle effect load failed, continuing without effect: {self.battle.effect_error}")
            if self.battle.attack_animation_error:
                print(
                    "SWK2 attack animation load failed, continuing without it: "
                    f"{self.battle.attack_animation_error}"
                )
        else:
            self.battle_blocked_monster = None
        self._sync_state()

    def _handle_interact(self):
        """处理 E/空格交互：关对话、切场景、或打开最近 NPC 对话。"""
        if self.active_npc:
            self._close_dialog()
            return

        if self._can_return_to_village():
            self._return_to_village()
            return

        if self._can_return_to_outskirts():
            self._return_to_outskirts()
            return

        if self._can_leave_temple():
            self._return_to_forest()
            return

        if self._can_enter_outskirts():
            self._enter_outskirts()
            return

        if self._can_enter_forest():
            self._enter_forest()
            return

        if self._can_enter_temple():
            self._enter_temple()
            return

        self.active_npc = self._nearby_npc()

    def _close_dialog(self):
        """关闭当前对话，并根据土地公对话推进任务状态。"""
        npc = self.active_npc
        self.active_npc = None
        if not self._is_temple_gate_npc(npc):
            return

        if self.quest.stage == QuestStage.NOT_ACCEPTED:
            self.quest.accept()
        elif self.quest.stage == QuestStage.RETURNED:
            self.quest.complete()
            self.complete_message_visible = True
            self._sync_state()

    # --- 四场景连接：村庄 <-> 郊外 <-> 森林 <-> 观音院 ---
    # 正向：村庄(土地公)-> 原郊外(向右)-> 森林(向右)-> 观音院
    # 返程：观音院(向左)-> 森林(向左)-> 原郊外(向左)-> 村庄
    # 接受土地公任务后即可在相邻地图之间来回穿梭，但不能跳过中间场景。

    def _can_travel_between_maps(self):
        """土地公交代任务后，允许玩家在相邻地图之间穿梭。"""
        return self.quest.stage in (QuestStage.ACCEPTED, QuestStage.CLEARED)

    def _can_enter_outskirts(self):
        """是否可以从村庄经土地公进入郊外。"""
        if self.scene.name != "village" or not self._can_travel_between_maps():
            return False
        return self._is_temple_gate_npc(self._nearby_npc())

    def _can_enter_forest(self):
        """是否可以从原郊外右侧出口进入森林。"""
        return (
            self.scene.name == "outskirts"
            and self._can_travel_between_maps()
            and self.player.hitbox.colliderect(self._outskirts_right_exit_rect())
        )

    def _can_enter_temple(self):
        """是否可以从森林右侧出口进入寺庙。"""
        return (
            self.scene.name == "forest"
            and self._can_travel_between_maps()
            and self.player.hitbox.colliderect(self._outskirts_right_exit_rect())
        )

    def _can_leave_temple(self):
        """是否可以从寺庙返回森林。"""
        return self.scene.name == "temple" and self._can_travel_between_maps()

    def _can_return_to_outskirts(self):
        """是否可以从森林左侧出口返回原郊外。"""
        return (
            self.scene.name == "forest"
            and self._can_travel_between_maps()
            and self.player.hitbox.colliderect(self._outskirts_left_exit_rect())
        )

    def _can_return_to_village(self):
        """是否可以从原郊外左侧出口回村复命。"""
        return (
            self.scene.name == "outskirts"
            and self._can_travel_between_maps()
            and self.player.hitbox.colliderect(self._outskirts_left_exit_rect())
        )

    def _outskirts_right_exit_rect(self):
        """当前过渡场景右侧出口矩形，用于前往下一张相邻地图。"""
        map_width, map_height = self.scene.pixel_size
        return pygame.Rect(map_width - OUTSKIRTS_EXIT_BAND, 0, OUTSKIRTS_EXIT_BAND, map_height)

    def _outskirts_left_exit_rect(self):
        """当前过渡场景左侧出口矩形，用于返回上一张相邻地图。"""
        _, map_height = self.scene.pixel_size
        return pygame.Rect(0, 0, OUTSKIRTS_EXIT_BAND, map_height)

    def _is_temple_gate_npc(self, npc):
        """判断一个 NPC 是否是村庄中负责推进任务的土地公。"""
        return bool(npc and self.scene.name == "village" and npc.layer_name == "god")

    def _enter_scene(self, scene, spawn, state):
        """切换到新场景，并重建玩家、摄像机和临时交互状态。"""
        self.scene = scene
        self.player = Player(SWK_DIR, spawn)
        self.camera = Camera(WINDOW_SIZE, self.scene.pixel_size)
        self.camera.update(self.player.rect)
        self.active_npc = None
        self.battle = None
        self.battle_blocked_monster = None
        self.state = state
        if self.player.load_error:
            print(f"Player image load failed, using placeholder: {self.player.load_error}")

    def _enter_outskirts(self):
        """从村庄进入原郊外。"""
        self._enter_scene(
            self._create_outskirts_scene(),
            DEFAULT_OUTSKIRTS_SPAWN,
            GameState.OUTSKIRTS_EXPLORING,
        )

    def _enter_forest(self):
        """从原郊外进入森林。"""
        self._enter_scene(
            self._create_forest_scene(),
            DEFAULT_FOREST_SPAWN,
            GameState.FOREST_EXPLORING,
        )

    def _return_to_forest(self):
        """从寺庙返回森林，并把玩家放到森林右上方安全道路。"""
        scene = self._create_forest_scene()
        self._enter_scene(scene, FOREST_RETURN_FROM_TEMPLE_SPAWN, GameState.FOREST_EXPLORING)

    def _return_to_outskirts(self):
        """从森林返回原郊外，并把玩家放到原郊外右侧附近。"""
        scene = self._create_outskirts_scene()
        map_width, map_height = scene.pixel_size
        spawn = (map_width - OUTSKIRTS_EXIT_BAND - 64, map_height // 2)
        self._enter_scene(scene, spawn, GameState.OUTSKIRTS_EXPLORING)

    def _enter_temple(self):
        """从森林进入寺庙，并加载寺庙怪物。"""
        scene = self._create_temple_scene()
        self._enter_scene(scene, scene.player_spawn, GameState.TEMPLE_EXPLORING)
        self._report_monster_load_issues()

    def _return_to_village(self):
        """从郊外回到村庄；只有清怪后返回才推进到复命阶段。"""
        scene = self._create_village_scene()
        self._enter_scene(scene, self._village_return_spawn(scene), GameState.VILLAGE_EXPLORING)
        self.quest.mark_returned()
        self._report_npc_load_issues()

    def _village_return_spawn(self, scene):
        """回村复命时优先把玩家放到土地公旁边。"""
        god = next((npc for npc in scene.npcs if npc.layer_name == "god"), None)
        if god is None:
            return scene.player_spawn
        return (god.position.x, god.position.y + 48)

    def _nearby_npc(self):
        """查找玩家交互范围内最近的 NPC。"""
        player_range = self.player.hitbox.inflate(
            NPC_INTERACTION_PADDING,
            NPC_INTERACTION_PADDING,
        )
        nearby = [npc for npc in self.scene.npcs if player_range.colliderect(npc.interaction_rect)]
        if not nearby:
            return None

        return min(
            nearby,
            key=lambda npc: (
                (self.player.hitbox.centerx - npc.rect.centerx) ** 2
                + (self.player.hitbox.centery - npc.rect.centery) ** 2
            ),
        )

    def _update(self, dt):
        """每帧更新游戏逻辑；开始、帮助、暂停状态不更新地图对象。"""
        if self.state in (GameState.START, GameState.HELP, GameState.PAUSED):
            return

        if self.boss_banner_timer > 0:
            self.boss_banner_timer = max(0.0, self.boss_banner_timer - dt)

        if self.battle:
            self._sync_state()
            self.battle.update(dt)
            if self.battle.player_defeated:
                self._enter_battle_failure("defeated")
            elif self.battle.escaped:
                self._exit_battle_escape()
            elif self.battle.finished:
                self.battle = None
                self._check_final_completion()
            return

        if self.complete_message_visible or self.failure_message_visible:
            self._sync_state()
            return

        self.scene.update_npcs(dt)
        self.scene.update_monsters(dt, self.player.hitbox)
        self._check_final_completion()
        if self.complete_message_visible:
            return

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.scene.pixel_size, self.scene.obstacle_rects)
        self.camera.update(self.player.rect)
        self._update_battle_trigger()
        self._sync_state()

    def _update_battle_trigger(self):
        """检测玩家是否碰到寺庙怪物，满足条件则创建 Battle。"""
        if self.scene.name != "temple":
            return

        if self.battle_blocked_monster:
            if self.battle_blocked_monster.defeated:
                self.battle_blocked_monster = None
            elif not self.player.hitbox.colliderect(self.battle_blocked_monster.trigger_rect):
                self.battle_blocked_monster = None

        for monster in self.scene.active_monsters:
            if monster is self.battle_blocked_monster:
                continue
            if monster.defeated:
                continue
            if self.player.hitbox.colliderect(monster.trigger_rect):
                self.battle = Battle(monster, FONT_PATH, WINDOW_SIZE)
                if self.battle.font_error:
                    print(f"Battle font load failed, using default font: {self.battle.font_error}")
                if self.battle.effect_error:
                    print(f"Battle effect load failed, continuing without effect: {self.battle.effect_error}")
                if self.battle.attack_animation_error:
                    print(
                        "SWK2 attack animation load failed, continuing without it: "
                        f"{self.battle.attack_animation_error}"
                    )
                break

    def _check_final_completion(self):
        """检查寺庙是否清空怪物；先生成 Boss，Boss 也击败后推进任务。"""
        if self.scene.name == "temple" and not self.scene.active_monsters:
            if not self.scene.boss_spawned:
                self._spawn_boss()
            else:
                self.quest.clear_monsters()
        self._sync_state()

    def _spawn_boss(self):
        """在寺庙中生成牛魔王 Boss，并显示短暂登场横幅。"""
        spawn = self.scene.boss_spawn
        if spawn is None:
            self.scene.boss_spawned = True
            return

        x, y, width, height = spawn
        boss = Boss("boss", x, y, width, height)
        self.scene.spawn_boss(boss)
        self.boss_banner_timer = BOSS_BANNER_SECONDS
        if boss.load_error:
            print(f"Boss image load failed, using placeholder: {boss.load_error}")
        for state_name, error in boss.animation_errors.items():
            print(f"Boss animation load failed for {state_name}, using fallback: {error}")

    def _sync_state(self):
        """根据当前场景、对话、战斗、失败和完成标记同步 GameState。"""
        if self.failure_message_visible:
            self.state = GameState.FAILED
        elif self.complete_message_visible or self.quest.is_complete:
            self.state = GameState.COMPLETE
        elif self.battle and self.battle.victory:
            self.state = GameState.BATTLE_VICTORY
        elif self.battle:
            self.state = GameState.BATTLE
        elif self.scene.name == "village":
            self.state = GameState.VILLAGE_EXPLORING
        elif self.scene.name == "outskirts":
            self.state = GameState.OUTSKIRTS_EXPLORING
        elif self.scene.name == "forest":
            self.state = GameState.FOREST_EXPLORING
        else:
            self.state = GameState.TEMPLE_EXPLORING

    def _draw(self):
        """根据当前状态绘制开始/帮助界面，或绘制地图、对象和覆盖层。"""
        if self.state == GameState.START:
            self.ui.draw_start(self.screen)
            pygame.display.flip()
            return

        if self.state == GameState.HELP:
            self.ui.draw_help(self.screen)
            pygame.display.flip()
            return

        self.screen.fill((0, 0, 0))
        self.scene.draw_map(self.screen, self.camera)
        drawables = [*self.scene.npcs, *self.scene.active_monsters, self.player]
        for drawable in sorted(drawables, key=lambda item: item.rect.bottom):
            drawable.draw(self.screen, self.camera)

        if self.active_npc:
            self.dialog_box.draw(
                self.screen,
                self.active_npc,
                self.quest.dialog_for(self.active_npc.layer_name),
            )
        if self.battle:
            self.battle.draw(self.screen)
        if self._can_enter_outskirts():
            self.ui.draw_temple_prompt(self.screen, "按 E / 空格 出村前往郊外")
        if self._can_enter_forest():
            self.ui.draw_temple_prompt(self.screen, "按 E / 空格 穿过郊外")
        if self._can_enter_temple():
            self.ui.draw_temple_prompt(self.screen)
        if self._can_leave_temple():
            if self.quest.stage == QuestStage.CLEARED:
                self.ui.draw_return_prompt(self.screen, "妖王已除，按 E / 空格 踏上归途")
            else:
                self.ui.draw_return_prompt(self.screen, "按 E / 空格 返回森林")
        if self._can_return_to_outskirts():
            self.ui.draw_return_prompt(self.screen, "按 E / 空格 返回郊外小路")
        if self._can_return_to_village():
            if self.quest.stage == QuestStage.CLEARED:
                self.ui.draw_return_prompt(self.screen, "按 E / 空格 回到村庄复命")
            else:
                self.ui.draw_return_prompt(self.screen, "按 E / 空格 返回村庄")
        if self.boss_banner_timer > 0:
            self.ui.draw_banner(self.screen, "妖王 牛魔王 现身！")
        if self.complete_message_visible:
            self._draw_complete_overlay()
        if self.failure_message_visible:
            self._draw_failure_overlay()
        if self.state == GameState.PAUSED:
            self.ui.draw_pause(self.screen)
        else:
            self.ui.draw_controls_hint(self.screen, self.audio.muted)

        pygame.display.flip()

    def _draw_complete_overlay(self):
        """绘制最终完成界面。"""
        self.ui.draw_result(
            self.screen,
            self.win_image,
            "妖怪已被击败，观音院危机解除！",
            ["恭喜完成西游记观音院冒险。"],
            "按 Esc 退出游戏",
            [("no", "按 Esc 退出")],
        )

    def _draw_failure_overlay(self):
        """绘制失败或撤退界面，并给出重试/退出操作。"""
        if self.failure_reason == "defeated":
            title = "挑战失败"
            lines = ["你被妖怪击败了。", "按 R 重整旗鼓，再次挑战。"]
        else:
            title = "暂离战斗"
            lines = ["你撤出了与妖怪的战斗。", "按 R 重新挑战当前妖怪。"]
        self.ui.draw_result(
            self.screen,
            self.fail_image,
            title,
            lines,
            "按 R 重新挑战  按 Esc 退出",
            [("ok", "按 R 重新挑战"), ("no", "按 Esc 退出")],
        )

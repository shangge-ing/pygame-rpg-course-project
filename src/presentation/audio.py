"""音频管理模块。

本模块把背景音乐、攻击音效、胜利音效统一封装起来。这样主游戏逻辑只需要
调用 `play_attack`、`play_victory` 或 `toggle_mute`，不需要关心 mixer 初始化、
音频文件是否缺失、设备是否可用等细节。
"""

import pygame


class AudioManager:
    """管理游戏中的背景音乐和短音效。"""

    def __init__(self, music_path, attack_sound_path, victory_sound_path, music_volume, sound_volume):
        """初始化音频系统，并尽量加载背景音乐、攻击音效和胜利音效。

        如果当前电脑没有可用音频设备，或者某个音频文件加载失败，游戏不会崩溃，
        只会打印提示并继续运行。
        """
        self.available = False
        self.muted = False
        self.music_volume = music_volume
        self.sound_volume = sound_volume
        self.attack_sound = None
        self.victory_sound = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.available = True
        except Exception as exc:
            print(f"Audio unavailable, continuing without sound: {exc}")
            return

        self._load_music(music_path)
        self.attack_sound = self._load_sound(attack_sound_path, "attack")
        self.victory_sound = self._load_sound(victory_sound_path, "victory")

    def _load_music(self, music_path):
        """加载并循环播放背景音乐。"""
        try:
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except Exception as exc:
            print(f"Background music load failed, continuing without music: {exc}")

    def _load_sound(self, sound_path, label):
        """加载一个短音效，失败时返回 None。"""
        try:
            sound = pygame.mixer.Sound(str(sound_path))
            sound.set_volume(self.sound_volume)
            return sound
        except Exception as exc:
            print(f"{label.capitalize()} sound load failed, continuing without it: {exc}")
            return None

    def toggle_mute(self):
        """切换静音状态，并同步调整背景音乐和音效音量。"""
        self.muted = not self.muted
        if not self.available:
            return self.muted

        pygame.mixer.music.set_volume(0 if self.muted else self.music_volume)
        for sound in (self.attack_sound, self.victory_sound):
            if sound:
                sound.set_volume(0 if self.muted else self.sound_volume)
        return self.muted

    def play_attack(self):
        """播放玩家攻击音效。"""
        self._play(self.attack_sound)

    def play_victory(self):
        """播放战斗胜利或通关提示音效。"""
        self._play(self.victory_sound)

    def _play(self, sound):
        """安全播放音效，避免音频异常中断游戏主流程。"""
        if not self.available or self.muted or not sound:
            return

        try:
            sound.play()
        except Exception as exc:
            print(f"Sound playback failed: {exc}")

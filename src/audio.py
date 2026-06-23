import pygame


class AudioManager:
    def __init__(self, music_path, attack_sound_path, victory_sound_path, music_volume, sound_volume):
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
        try:
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
        except Exception as exc:
            print(f"Background music load failed, continuing without music: {exc}")

    def _load_sound(self, sound_path, label):
        try:
            sound = pygame.mixer.Sound(str(sound_path))
            sound.set_volume(self.sound_volume)
            return sound
        except Exception as exc:
            print(f"{label.capitalize()} sound load failed, continuing without it: {exc}")
            return None

    def toggle_mute(self):
        self.muted = not self.muted
        if not self.available:
            return self.muted

        pygame.mixer.music.set_volume(0 if self.muted else self.music_volume)
        for sound in (self.attack_sound, self.victory_sound):
            if sound:
                sound.set_volume(0 if self.muted else self.sound_volume)
        return self.muted

    def play_attack(self):
        self._play(self.attack_sound)

    def play_victory(self):
        self._play(self.victory_sound)

    def _play(self, sound):
        if not self.available or self.muted or not sound:
            return

        try:
            sound.play()
        except Exception as exc:
            print(f"Sound playback failed: {exc}")

import pygame


class UI:
    def __init__(self, font_path, window_size, start_background_path=None, button_paths=None):
        self.window_width, self.window_height = window_size
        self.window_size = window_size
        self.font_error = None
        self.start_background_error = None
        self.button_errors = {}
        self.title_font = self._load_font(font_path, 46)
        self.large_font = self._load_font(font_path, 34)
        self.text_font = self._load_font(font_path, 26)
        self.small_font = self._load_font(font_path, 22)
        self.start_background = self._load_background(start_background_path)
        self.buttons = self._load_buttons(button_paths or {})

    def _load_font(self, font_path, size):
        try:
            return pygame.font.Font(str(font_path), size)
        except Exception as exc:
            self.font_error = str(exc)
            return pygame.font.Font(None, size)

    def _load_background(self, path):
        if path is None:
            return None

        try:
            image = pygame.image.load(path).convert()
            return pygame.transform.smoothscale(image, self.window_size)
        except Exception as exc:
            self.start_background_error = str(exc)
            return None

    def _load_buttons(self, button_paths):
        buttons = {}
        for name, path in button_paths.items():
            try:
                buttons[name] = pygame.image.load(path).convert_alpha()
            except Exception as exc:
                self.button_errors[name] = str(exc)
        return buttons

    def draw_start(self, surface):
        self._draw_full_background(surface, self.start_background, (23, 28, 34), 95)
        self._draw_image_center(surface, "village", (self.window_width // 2, 92), 210, 58)
        self._draw_center_text(surface, self.title_font, "西游记观音院", 160, (255, 232, 150))
        self._draw_button_hint(surface, "ok", "按 Enter 开始游戏", 266)
        self._draw_center_text(surface, self.text_font, "按 H 查看操作说明", 312, (235, 235, 235))
        self._draw_button_hint(surface, "no", "按 Esc 退出", 358)

    def draw_help(self, surface):
        surface.fill((20, 24, 30))
        self._draw_center_text(surface, self.large_font, "操作说明", 92, (255, 232, 150))
        lines = [
            "方向键：移动",
            "E / 空格：对话 / 交互",
            "J：战斗攻击",
            "M：静音 / 恢复音频",
            "P：暂停游戏",
            "Esc：返回 / 退出",
        ]
        self._draw_panel_lines(surface, lines, 150, line_height=42)
        self._draw_button_hint(surface, "no", "按 Esc 返回开始界面", 520, font=self.small_font)

    def draw_pause(self, surface):
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(170, 185, self.window_width - 340, 190)
        pygame.draw.rect(surface, (24, 28, 34), panel)
        pygame.draw.rect(surface, (232, 214, 160), panel, 3)
        self._draw_center_text(surface, self.large_font, "游戏已暂停", panel.top + 44, (255, 232, 150))
        self._draw_button_hint(surface, "ok", "按 P 继续", panel.top + 104)
        self._draw_button_hint(surface, "no", "按 Esc 退出", panel.top + 148, font=self.small_font)

    def draw_controls_hint(self, surface, muted):
        mute_text = "静音" if muted else "音频开"
        hint = f"方向键移动  E/空格对话  J攻击  P暂停  M静音  Esc退出  [{mute_text}]"
        text_surface = self.small_font.render(hint, True, (255, 255, 255))
        bg_rect = text_surface.get_rect(topleft=(12, 10)).inflate(16, 8)
        bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        surface.blit(bg, bg_rect.topleft)
        surface.blit(text_surface, (bg_rect.left + 8, bg_rect.top + 4))

    def draw_temple_prompt(self, surface, text="按 E / 空格进入观音院"):
        panel = pygame.Rect(214, self.window_height - 110, self.window_width - 428, 76)
        prompt = pygame.Surface(panel.size, pygame.SRCALPHA)
        prompt.fill((0, 0, 0, 145))
        pygame.draw.rect(prompt, (232, 214, 160), prompt.get_rect(), 2)
        surface.blit(prompt, panel.topleft)

        self._draw_image_center(surface, "temple", (panel.left + 70, panel.centery), 116, 42)
        self._draw_image_center(surface, "small_temple", (panel.right - 44, panel.centery), 44, 44)
        self._draw_text(surface, self.small_font, text, panel.left + 128, panel.centery - 12, (255, 245, 215))

    def draw_return_prompt(self, surface, text="妖怪已除，按 E / 空格返回村庄复命"):
        panel = pygame.Rect(196, self.window_height - 110, self.window_width - 392, 76)
        prompt = pygame.Surface(panel.size, pygame.SRCALPHA)
        prompt.fill((0, 0, 0, 145))
        pygame.draw.rect(prompt, (232, 214, 160), prompt.get_rect(), 2)
        surface.blit(prompt, panel.topleft)

        self._draw_image_center(surface, "village", (panel.left + 70, panel.centery), 116, 42)
        self._draw_text(surface, self.small_font, text, panel.left + 132, panel.centery - 12, (255, 245, 215))

    def draw_banner(self, surface, text):
        panel = pygame.Rect(0, 150, self.window_width, 70)
        banner = pygame.Surface(panel.size, pygame.SRCALPHA)
        banner.fill((90, 0, 0, 190))
        surface.blit(banner, panel.topleft)
        pygame.draw.rect(surface, (235, 90, 80), panel, 3)
        self._draw_center_text(surface, self.large_font, text, panel.centery, (255, 226, 150))

    def draw_result(self, surface, image, title, lines, hint, actions=None):
        self._draw_full_background(surface, image, (18, 18, 24), 170)
        panel = pygame.Rect(86, 160, self.window_width - 172, 250)
        pygame.draw.rect(surface, (24, 28, 32), panel)
        pygame.draw.rect(surface, (232, 214, 160), panel, 3)
        self._draw_center_text(surface, self.large_font, title, panel.top + 44, (255, 232, 150))

        y = panel.top + 104
        for line in lines:
            self._draw_center_text(surface, self.text_font, line, y, (245, 245, 245))
            y += 42

        if actions:
            self._draw_action_row(surface, actions, panel.bottom - 34)
        else:
            self._draw_center_text(surface, self.small_font, hint, panel.bottom - 34, (215, 215, 215))

    def _draw_full_background(self, surface, image, fallback_color, overlay_alpha):
        if image:
            surface.blit(image, (0, 0))
        else:
            surface.fill(fallback_color)

        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, overlay_alpha))
        surface.blit(overlay, (0, 0))

    def _draw_panel_lines(self, surface, lines, start_y, line_height):
        panel = pygame.Rect(150, start_y - 24, self.window_width - 300, len(lines) * line_height + 46)
        pygame.draw.rect(surface, (29, 34, 40), panel)
        pygame.draw.rect(surface, (232, 214, 160), panel, 2)
        y = start_y
        for line in lines:
            self._draw_center_text(surface, self.text_font, line, y, (245, 245, 245))
            y += line_height

    def _draw_action_row(self, surface, actions, y):
        total_width = sum(190 for _ in actions) + max(0, len(actions) - 1) * 24
        x = (self.window_width - total_width) // 2
        for button_name, text in actions:
            self._draw_button_hint(surface, button_name, text, y, center_x=x + 95, font=self.small_font)
            x += 214

    def _draw_button_hint(self, surface, button_name, text, y, center_x=None, font=None):
        font = font or self.text_font
        center_x = center_x or self.window_width // 2
        text_surface = font.render(text, True, (245, 245, 245))
        button = self._scaled_image(button_name, 42, 32)
        width = text_surface.get_width() + 14
        if button:
            width += button.get_width() + 10

        rect = pygame.Rect(0, 0, width + 24, max(42, text_surface.get_height() + 16))
        rect.center = (center_x, y)
        pygame.draw.rect(surface, (28, 32, 38), rect)
        pygame.draw.rect(surface, (232, 214, 160), rect, 2)

        x = rect.left + 12
        if button:
            button_rect = button.get_rect(midleft=(x, rect.centery))
            surface.blit(button, button_rect)
            x = button_rect.right + 10
        else:
            fallback_rect = pygame.Rect(x, rect.centery - 14, 34, 28)
            pygame.draw.rect(surface, (75, 83, 92), fallback_rect)
            pygame.draw.rect(surface, (232, 214, 160), fallback_rect, 1)
            x = fallback_rect.right + 10

        text_rect = text_surface.get_rect(midleft=(x, rect.centery))
        surface.blit(text_surface, text_rect)

    def _draw_image_center(self, surface, image_name, center, max_width, max_height):
        image = self._scaled_image(image_name, max_width, max_height)
        if image:
            surface.blit(image, image.get_rect(center=center))

    def _scaled_image(self, image_name, max_width, max_height):
        image = self.buttons.get(image_name)
        if not image:
            return None

        scale = min(max_width / image.get_width(), max_height / image.get_height(), 1)
        size = (
            max(1, round(image.get_width() * scale)),
            max(1, round(image.get_height() * scale)),
        )
        if size == image.get_size():
            return image
        return pygame.transform.smoothscale(image, size)

    def _draw_text(self, surface, font, text, x, y, color):
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, (x, y))

    def _draw_center_text(self, surface, font, text, y, color):
        text_surface = font.render(text, True, color)
        rect = text_surface.get_rect(center=(self.window_width // 2, y))
        surface.blit(text_surface, rect)

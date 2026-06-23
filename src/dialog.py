import pygame

from .settings import DIALOG_IMAGE_PATH


class DialogBox:
    def __init__(self, font_path, window_size):
        self.window_width, self.window_height = window_size
        self.font_error = None
        self.image_error = None
        self.name_font = self._load_font(font_path, 28)
        self.text_font = self._load_font(font_path, 24)
        self.padding = 24
        self.box_rect = pygame.Rect(
            24,
            self.window_height - 184,
            self.window_width - 48,
            160,
        )
        self.background = self._load_background()

    def _load_font(self, font_path, size):
        try:
            return pygame.font.Font(str(font_path), size)
        except Exception as exc:
            self.font_error = str(exc)
            return pygame.font.Font(None, size)

    def _load_background(self):
        try:
            image = pygame.image.load(DIALOG_IMAGE_PATH).convert_alpha()
            return pygame.transform.smoothscale(image, self.box_rect.size)
        except Exception as exc:
            self.image_error = str(exc)
            return None

    def draw(self, surface, npc, text=None):
        dialog_text = text if text is not None else npc.dialog_text
        if self.background:
            surface.blit(self.background, self.box_rect.topleft)
        else:
            overlay = pygame.Surface(self.box_rect.size, pygame.SRCALPHA)
            overlay.fill((18, 18, 24, 220))
            pygame.draw.rect(overlay, (230, 216, 172), overlay.get_rect(), 3)
            surface.blit(overlay, self.box_rect.topleft)

        x = self.box_rect.left + self.padding
        y = self.box_rect.top + 18
        name_surface = self.name_font.render(npc.display_name, True, (255, 232, 150))
        surface.blit(name_surface, (x, y))

        text_y = y + 44
        max_width = self.box_rect.width - self.padding * 2
        for line in self._wrap_text(dialog_text, max_width):
            text_surface = self.text_font.render(line, True, (245, 245, 245))
            surface.blit(text_surface, (x, text_y))
            text_y += self.text_font.get_linesize()

    def _wrap_text(self, text, max_width):
        lines = []
        current = ""
        for char in text:
            candidate = current + char
            if current and self.text_font.size(candidate)[0] > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate

        if current:
            lines.append(current)
        return lines

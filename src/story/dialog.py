"""对话框绘制模块。

DialogBox 负责在屏幕底部显示 NPC 名字和对话内容。字体、背景图片和自动换行
都集中在这里处理，方便后续继续扩展多句对话或剧情文本。
"""

import pygame

from ..config.settings import DIALOG_IMAGE_PATH, GOD_DIALOG_PORTRAIT_PATH


class DialogBox:
    """绘制底部 NPC 对话框。"""

    def __init__(self, font_path, window_size):
        """加载中文字体和对话框背景，并计算对话框位置。"""
        self.window_width, self.window_height = window_size
        self.font_error = None
        self.image_error = None
        self.name_font = self._load_font(font_path, 28)
        self.text_font = self._load_font(font_path, 24)
        self.padding = 24
        self.portrait_error = None
        self.box_rect = pygame.Rect(
            24,
            self.window_height - 184,
            self.window_width - 48,
            160,
        )
        self.background = self._load_background()
        self.god_portrait = self._load_god_portrait()

    def _load_font(self, font_path, size):
        """优先加载项目字体，失败时退回 pygame 默认字体。"""
        try:
            return pygame.font.Font(str(font_path), size)
        except Exception as exc:
            self.font_error = str(exc)
            return pygame.font.Font(None, size)

    def _load_background(self):
        """加载 resource/img/dialog/dialog.png 作为对话框背景。"""
        try:
            image = pygame.image.load(DIALOG_IMAGE_PATH).convert_alpha()
            return pygame.transform.smoothscale(image, self.box_rect.size)
        except Exception as exc:
            self.image_error = str(exc)
            return None

    def _load_god_portrait(self):
        """加载土地公对话头像，失败时只隐藏头像，不影响对话框。"""
        try:
            image = pygame.image.load(GOD_DIALOG_PORTRAIT_PATH).convert_alpha()
            rect = image.get_bounding_rect(min_alpha=8)
            if rect.width > 0 and rect.height > 0:
                image = image.subsurface(rect).copy()

            max_size = 112
            scale = min(max_size / image.get_width(), max_size / image.get_height())
            size = (
                max(1, int(image.get_width() * scale)),
                max(1, int(image.get_height() * scale)),
            )
            return pygame.transform.smoothscale(image, size)
        except Exception as exc:
            self.portrait_error = str(exc)
            return None

    def draw(self, surface, npc, text=None):
        """把指定 NPC 的名字和对话内容绘制到屏幕底部。"""
        dialog_text = text if text is not None else npc.dialog_text
        if self.background:
            surface.blit(self.background, self.box_rect.topleft)
        else:
            overlay = pygame.Surface(self.box_rect.size, pygame.SRCALPHA)
            overlay.fill((18, 18, 24, 220))
            pygame.draw.rect(overlay, (230, 216, 172), overlay.get_rect(), 3)
            surface.blit(overlay, self.box_rect.topleft)

        x = self.box_rect.left + self.padding
        text_width = self.box_rect.width - self.padding * 2
        portrait = self._portrait_for(npc)
        if portrait:
            portrait_rect = portrait.get_rect(
                midleft=(self.box_rect.left + self.padding, self.box_rect.centery)
            )
            frame_rect = portrait_rect.inflate(10, 10)
            frame = pygame.Surface(frame_rect.size, pygame.SRCALPHA)
            frame.fill((25, 20, 18, 150))
            pygame.draw.rect(frame, (239, 211, 143), frame.get_rect(), 2, border_radius=6)
            surface.blit(frame, frame_rect.topleft)
            surface.blit(portrait, portrait_rect)
            x = frame_rect.right + 18
            text_width = self.box_rect.right - self.padding - x

        y = self.box_rect.top + 18
        name_surface = self.name_font.render(npc.display_name, True, (255, 232, 150))
        surface.blit(name_surface, (x, y))

        text_y = y + 44
        for line in self._wrap_text(dialog_text, text_width):
            text_surface = self.text_font.render(line, True, (245, 245, 245))
            surface.blit(text_surface, (x, text_y))
            text_y += self.text_font.get_linesize()

    def _portrait_for(self, npc):
        """当前只给土地公显示头像，其他 NPC 保持原来的纯文字对话框。"""
        if getattr(npc, "layer_name", None) == "god":
            return self.god_portrait
        return None

    def _wrap_text(self, text, max_width):
        """按像素宽度把中文文本拆成多行，避免文字超出对话框。"""
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

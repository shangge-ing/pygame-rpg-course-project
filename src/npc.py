"""Stage 2 NPC 模块：读取对象层 NPC，显示图片并提供对话。"""

import pygame

from .settings import ELDER_DIR, GOD_DIR, NPC_INTERACTION_PADDING


class NPC:
    """村庄 NPC，包括土地公、老人和孩童。"""

    DIALOGS = {
        "god": ("土地公", "大圣，前方就是观音院，小心妖怪。"),
        "elder": ("老人", "村里最近不太安宁。"),
        "child": ("孩童", "我好像看到有妖怪往寺庙方向去了。"),
    }

    def __init__(self, layer_name, object_name, position):
        self.layer_name = layer_name
        self.object_name = object_name
        self.position = pygame.Vector2(position)
        self.display_name, self.dialog_text = self.DIALOGS.get(
            layer_name,
            (object_name or "村民", "……"),
        )
        self.load_error = None
        self.image = self._load_image()
        self.rect = self.image.get_rect(midbottom=self.position)

    def _load_image(self):
        """按 NPC 类型加载图片，孩童使用 pygame 绘制简单形象。"""
        if self.layer_name == "child":
            return self._child_image()

        image_path = None
        if self.layer_name == "god":
            image_path = GOD_DIR / "0214-16505471-00000.tga"
        elif self.layer_name == "elder" and self.object_name:
            path = ELDER_DIR / f"{self.object_name}-00000.tga"
            image_path = path if path.exists() else None

        try:
            if image_path is None:
                raise FileNotFoundError(f"no image for {self.layer_name}:{self.object_name}")
            return pygame.image.load(image_path).convert_alpha()
        except Exception as exc:
            self.load_error = str(exc)
            return self._placeholder_image()

    def _child_image(self):
        """没有孩童素材时，用代码画一个简单孩童形象。"""
        image = pygame.Surface((40, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(image, (245, 205, 150), (9, 2, 22, 22))
        pygame.draw.circle(image, (45, 35, 30), (16, 13), 2)
        pygame.draw.circle(image, (45, 35, 30), (24, 13), 2)
        pygame.draw.polygon(image, (92, 178, 118), [(12, 25), (28, 25), (34, 50), (6, 50)])
        pygame.draw.rect(image, (70, 95, 135), (11, 49, 7, 8))
        pygame.draw.rect(image, (70, 95, 135), (22, 49, 7, 8))
        return image

    def _placeholder_image(self):
        """资源缺失时显示彩色占位图。"""
        color = {"god": (230, 190, 75), "elder": (120, 170, 230)}.get(self.layer_name, (110, 210, 140))
        image = pygame.Surface((42, 58), pygame.SRCALPHA)
        image.fill(color)
        pygame.draw.rect(image, (255, 255, 255), image.get_rect(), 2)
        return image

    @property
    def interaction_rect(self):
        """比图片更大的交互范围，便于玩家靠近后对话。"""
        return self.rect.inflate(NPC_INTERACTION_PADDING, NPC_INTERACTION_PADDING)

    def draw(self, surface, camera):
        """按摄像机偏移绘制 NPC。"""
        surface.blit(self.image, camera.apply_rect(self.rect))

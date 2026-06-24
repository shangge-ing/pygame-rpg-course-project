import pygame

from .animation import Animation
from .settings import (
    ELDER_DIR,
    GOD_DIR,
    NPC_IDLE_FRAME_LIMIT,
    NPC_IDLE_FRAME_TIME,
    NPC_INTERACTION_PADDING,
)


class NPC:
    """村庄 NPC：保存位置、显示图片、待机动画和对话内容。"""

    # 按图层的兜底对话（找不到具体角色台词时使用）。
    DIALOGS = {
        "god": ("土地公", "大圣，前方就是观音院，小心妖怪。"),
        "elder": ("老人", "村里最近不太安宁。"),
        "child": ("孩童", "我好像看到有妖怪往寺庙方向去了。"),
    }

    # 按对象名的专属对话，让每个村民各有性格。
    OBJECT_DIALOGS = {
        # 老人们
        "elder1": ("张老汉", "听闻观音院的禅师都被妖怪掳走了，大圣可要救救他们啊。"),
        "elder2": ("王婆婆", "老身年轻时也见过妖怪作乱，那回还是一位高僧把妖降住的。"),
        "elder3": ("李大爷", "这几日夜里总听见院子那头传来怪叫，娃娃都吓得不敢睡。"),
        "elder4": ("赵老伯", "大圣若要进观音院，记得先找土地公问个明白。"),
        # 孩童们
        "boy1": ("小石头", "大圣大圣！你真会七十二变吗？变只猴子给俺瞧瞧嘛！"),
        "boy2": ("二娃", "俺哥说那妖怪有两只大角，可吓人了，你打得过它吗？"),
        "girl1": ("阿香", "我的花猫昨天跑去观音院就没回来，你能帮我找找它吗？"),
        "girl2": ("翠儿", "娘说天黑了不许出门，因为妖怪会抓小孩呢……"),
        "girl3": ("莲妹", "大圣加油！打跑了妖怪，我就给你摘最甜的桃子！"),
    }

    def __init__(self, layer_name, object_name, position):
        """根据 TMX 对象层信息创建 NPC。"""
        self.layer_name = layer_name
        self.object_name = object_name
        self.position = pygame.Vector2(position)
        self.display_name, self.dialog_text = self._resolve_dialog(layer_name, object_name)
        self.load_error = None
        self.animation_error = None
        self.frame_paths = []
        self.animation = self._load_animation()
        self.image = self.animation.current_frame
        self.base_rect = self.image.get_rect(midbottom=self.position)
        self.rect = self.base_rect.copy()

    def _resolve_dialog(self, layer_name, object_name):
        """根据对象名优先匹配专属台词，找不到时使用图层默认台词。"""
        if object_name in self.OBJECT_DIALOGS:
            return self.OBJECT_DIALOGS[object_name]
        if layer_name in self.DIALOGS:
            return self.DIALOGS[layer_name]
        return (object_name or "村民", "……")

    def _load_animation(self):
        """加载 NPC 待机动画；没有多帧资源时退回静态图片。"""
        frame_paths = self._animation_paths()
        if not frame_paths:
            return Animation([self._load_static_image()], NPC_IDLE_FRAME_TIME)

        frames = []
        try:
            for path in frame_paths[:NPC_IDLE_FRAME_LIMIT]:
                frames.append(pygame.image.load(path).convert_alpha())
        except Exception as exc:
            self.animation_error = str(exc)
            frames = []

        if not frames:
            return Animation([self._load_static_image()], NPC_IDLE_FRAME_TIME)

        self.frame_paths = frame_paths[: len(frames)]
        return Animation(frames, NPC_IDLE_FRAME_TIME)

    def _animation_paths(self):
        """按 NPC 类型和对象名寻找对应的待机动画帧。"""
        if self.layer_name == "god":
            return sorted(GOD_DIR.glob("0214-16505471-000*.tga"))

        if self.layer_name == "elder" and self.object_name:
            return sorted(ELDER_DIR.glob(f"{self.object_name}-*.tga"))

        return []

    def _load_static_image(self):
        """加载单帧 NPC 图片；孩童没有素材时使用代码绘制形象。"""
        image_path = self._image_path()
        if image_path is None and self.layer_name == "child":
            return self._child_image()

        try:
            if image_path is None:
                raise FileNotFoundError(f"no configured image for {self.layer_name}:{self.object_name}")
            return pygame.image.load(image_path).convert_alpha()
        except Exception as exc:
            self.load_error = str(exc)
            return self._placeholder_image()

    def _image_path(self):
        """获取 NPC 的默认静态图片路径。"""
        if self.layer_name == "god":
            return GOD_DIR / "0214-16505471-00000.tga"

        if self.layer_name == "elder" and self.object_name:
            path = ELDER_DIR / f"{self.object_name}-00000.tga"
            if path.exists():
                return path

        return None

    def _child_image(self):
        """用 pygame 绘制简单孩童形象，避免孩童 NPC 只是普通矩形。"""
        image = pygame.Surface((40, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(image, (245, 205, 150), (9, 2, 22, 22))
        pygame.draw.arc(image, (65, 45, 35), (8, 0, 24, 18), 3.2, 6.1, 3)
        pygame.draw.circle(image, (45, 35, 30), (16, 13), 2)
        pygame.draw.circle(image, (45, 35, 30), (24, 13), 2)
        pygame.draw.arc(image, (130, 64, 50), (15, 12, 10, 7), 0.2, 2.9, 1)
        pygame.draw.polygon(image, (92, 178, 118), [(12, 25), (28, 25), (34, 50), (6, 50)])
        pygame.draw.line(image, (235, 220, 150), (20, 27), (20, 48), 2)
        pygame.draw.rect(image, (70, 95, 135), (11, 49, 7, 8))
        pygame.draw.rect(image, (70, 95, 135), (22, 49, 7, 8))
        pygame.draw.line(image, (80, 55, 40), (18, 57), (14, 57), 2)
        pygame.draw.line(image, (80, 55, 40), (26, 57), (30, 57), 2)
        return image

    def _placeholder_image(self):
        """资源加载失败时使用彩色占位图，保证 NPC 仍然可见。"""
        colors = {
            "god": (230, 190, 75),
            "elder": (120, 170, 230),
            "child": (110, 210, 140),
        }
        image = pygame.Surface((42, 58), pygame.SRCALPHA)
        image.fill(colors.get(self.layer_name, (190, 120, 210)))
        pygame.draw.rect(image, (255, 255, 255), image.get_rect(), 2)
        return image

    def relocate(self, position):
        """把 NPC 移到新的落脚点，通常用于修正站在障碍物中的对象。"""
        # 把 NPC 移到新的落脚点（用于把站在障碍里的 NPC 挪到可走处）。
        self.position = pygame.Vector2(position)
        self.base_rect = self.image.get_rect(midbottom=self.position)
        self.rect = self.base_rect.copy()

    @property
    def interaction_rect(self):
        """NPC 的交互范围，比图片矩形更大，方便玩家靠近后按键对话。"""
        return self.base_rect.inflate(NPC_INTERACTION_PADDING, NPC_INTERACTION_PADDING)

    def update(self, dt):
        """更新 NPC 待机动画，不改变世界坐标和交互范围。"""
        self.animation.update(dt)
        self.image = self.animation.current_frame
        self.rect = self.image.get_rect(midbottom=self.position)

    def draw(self, surface, camera):
        """按摄像机偏移绘制 NPC。"""
        surface.blit(self.image, camera.apply_rect(self.rect))

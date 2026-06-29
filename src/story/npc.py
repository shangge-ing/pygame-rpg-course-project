import pygame

from ..presentation.animation import Animation
from ..config.settings import (
    CHILD_DIR,
    CHILD_IMAGE_NAME_MARKER,
    CHILD_SPRITE_HEIGHT,
    ELDER_DIR,
    GOD_DIR,
    GOD_PATROL_RADIUS,
    GOD_PATROL_SPEED,
    NPC_IDLE_FRAME_LIMIT,
    NPC_IDLE_FRAME_TIME,
    NPC_INTERACTION_PADDING,
)


class NPC:
    """村庄 NPC：保存位置、显示图片、待机动画和对话内容。"""

    CHILD_IMAGE_ORDER = ("boy1", "boy2", "girl1", "girl2", "girl3")
    GOD_DIRECTION_PREFIXES = {
        "down": "000",
        "left": "010",
        "up": "020",
        "right": "030",
    }

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
        self.home_position = pygame.Vector2(position)
        self.patrol_target_index = 0
        self.facing = "down"
        self.direction_animations = {}
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
        if self.layer_name == "god":
            self.direction_animations = self._load_god_direction_animations()
            if self.direction_animations:
                return self.direction_animations.get(self.facing) or next(iter(self.direction_animations.values()))

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

    def _load_god_direction_animations(self):
        """加载土地公四方向帧，移动时根据方向切换动画。"""
        animations = {}
        loaded_paths = []
        try:
            for direction, prefix in self.GOD_DIRECTION_PREFIXES.items():
                paths = sorted(GOD_DIR.glob(f"0214-16505471-{prefix}*.tga"))[:NPC_IDLE_FRAME_LIMIT]
                frames = [pygame.image.load(path).convert_alpha() for path in paths]
                if frames:
                    animations[direction] = Animation(frames, NPC_IDLE_FRAME_TIME)
                    loaded_paths.extend(paths)
        except Exception as exc:
            self.animation_error = str(exc)
            return {}

        self.frame_paths = loaded_paths
        return animations

    def _animation_paths(self):
        """按 NPC 类型和对象名寻找对应的待机动画帧。"""
        if self.layer_name == "god":
            return sorted(GOD_DIR.glob("0214-16505471-000*.tga"))

        if self.layer_name == "elder" and self.object_name:
            return sorted(ELDER_DIR.glob(f"{self.object_name}-*.tga"))

        return []

    def _load_static_image(self):
        """加载单帧 NPC 图片；孩童优先使用 resource/img/child 中的新素材。"""
        image_path = self._image_path()
        try:
            if image_path is None:
                raise FileNotFoundError(f"no configured image for {self.layer_name}:{self.object_name}")
            image = pygame.image.load(image_path).convert_alpha()
            if self.layer_name == "child":
                image = self._prepare_child_sprite(image)
            return image
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

        if self.layer_name == "child":
            child_paths = self._child_image_paths()
            if not child_paths:
                return None
            try:
                index = self.CHILD_IMAGE_ORDER.index(self.object_name)
            except ValueError:
                index = 0
            return child_paths[index % len(child_paths)]

        return None

    def _child_image_paths(self):
        """优先使用新加入的一批孩童图片，找不到时再退回全部 child 素材。"""
        all_paths = sorted(
            path
            for pattern in ("*.png", "*.jpg", "*.jpeg", "*.tga")
            for path in CHILD_DIR.glob(pattern)
            if path.is_file()
        )
        preferred_paths = [path for path in all_paths if CHILD_IMAGE_NAME_MARKER in path.name]
        if len(preferred_paths) >= len(self.CHILD_IMAGE_ORDER):
            return preferred_paths
        return all_paths

    def _prepare_child_sprite(self, image):
        """Remove the generated checkerboard background, crop blank space, and scale."""
        image = self._remove_checker_background(image)
        rect = image.get_bounding_rect(min_alpha=8)
        if rect.width > 0 and rect.height > 0:
            image = image.subsurface(rect).copy()

        if image.get_height() > CHILD_SPRITE_HEIGHT:
            scale = CHILD_SPRITE_HEIGHT / image.get_height()
            size = (max(1, int(image.get_width() * scale)), CHILD_SPRITE_HEIGHT)
            image = pygame.transform.smoothscale(image, size)
        return image

    def _remove_checker_background(self, image):
        """Treat the light checkerboard export background as transparent."""
        image = image.copy()
        width, height = image.get_size()
        for y in range(height):
            for x in range(width):
                color = image.get_at((x, y))
                if self._is_checker_background(color):
                    image.set_at((x, y), (color.r, color.g, color.b, 0))
        return image

    @staticmethod
    def _is_checker_background(color):
        """Detect the bright grey/white checkerboard around generated child images."""
        return (
            color.r >= 222
            and color.g >= 222
            and color.b >= 222
            and abs(color.r - color.g) <= 10
            and abs(color.r - color.b) <= 10
            and abs(color.g - color.b) <= 10
        )

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
        self.home_position = pygame.Vector2(position)
        self.base_rect = self.image.get_rect(midbottom=self.position)
        self.rect = self.base_rect.copy()

    @property
    def interaction_rect(self):
        """NPC 的交互范围，比图片矩形更大，方便玩家靠近后按键对话。"""
        return self.base_rect.inflate(NPC_INTERACTION_PADDING, NPC_INTERACTION_PADDING)

    def update(self, dt):
        """更新 NPC 待机动画和少量巡逻移动。"""
        self.animation.update(dt)
        self._update_patrol(dt)
        self.image = self.animation.current_frame
        self.rect = self.image.get_rect(midbottom=self.position)
        self.base_rect = self.rect.copy()

    def _update_patrol(self, dt):
        """让土地公在出生点附近按小方形路线巡逻，其他 NPC 保持原地。"""
        if self.layer_name != "god" or GOD_PATROL_RADIUS <= 0 or GOD_PATROL_SPEED <= 0:
            return

        patrol_points = self._god_patrol_points()
        target = patrol_points[self.patrol_target_index]
        to_target = target - self.position
        step = GOD_PATROL_SPEED * dt

        if to_target.length() <= step:
            self.position.update(target)
            self.patrol_target_index = (self.patrol_target_index + 1) % len(patrol_points)
            next_delta = patrol_points[self.patrol_target_index] - self.position
            self._set_facing_from_motion(next_delta)
            return

        movement = to_target.normalize() * step
        self.position += movement
        self._set_facing_from_motion(movement)

    def _god_patrol_points(self):
        """返回土地公围绕出生点移动的一圈目标点。"""
        radius = GOD_PATROL_RADIUS
        home = self.home_position
        return [
            pygame.Vector2(home.x + radius, home.y),
            pygame.Vector2(home.x + radius, home.y + radius),
            pygame.Vector2(home.x - radius, home.y + radius),
            pygame.Vector2(home.x - radius, home.y - radius),
            pygame.Vector2(home.x + radius, home.y - radius),
        ]

    def _set_facing_from_motion(self, motion):
        """根据本帧移动方向选择土地公朝向。"""
        if motion.length_squared() == 0:
            return

        if abs(motion.x) >= abs(motion.y):
            direction = "right" if motion.x > 0 else "left"
        else:
            direction = "down" if motion.y > 0 else "up"
        self._set_facing(direction)

    def _set_facing(self, direction):
        """切换到指定方向动画，缺帧时保持当前动画。"""
        if direction == self.facing or direction not in self.direction_animations:
            return

        self.facing = direction
        self.animation = self.direction_animations[direction]
        self.animation.reset()

    def draw(self, surface, camera):
        """按摄像机偏移绘制 NPC。"""
        surface.blit(self.image, camera.apply_rect(self.rect))

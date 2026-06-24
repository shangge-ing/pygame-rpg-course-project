from .monster import Monster
from .settings import (
    BOSS_ATTACK_COOLDOWN,
    BOSS_ATTACK_DAMAGE,
    BOSS_ENRAGE_HEALTH_RATIO,
    BOSS_ENRAGED_ATTACK_COOLDOWN,
    BOSS_ENRAGED_ATTACK_DAMAGE,
    BOSS_MAX_HEALTH,
    BOSS_SCALE,
)


"""Boss 模块。

Boss 继承 Monster，复用怪物动画、血量、死亡和消失流程，只调整血量、攻击力、
攻击间隔和半血暴怒机制。
"""


class Boss(Monster):
    """牛魔王：复用 Monster 的动画 / 巡逻 / 战斗逻辑，只覆写数值与阶段变化。

    阶段变化：血量降到 BOSS_ENRAGE_HEALTH_RATIO 以下进入暴怒，攻击更强更快。
    沿用 cattle / magic 素材，不复制怪物逻辑。
    """

    def __init__(self, object_name, x, y, width, height):
        """创建牛魔王 Boss，并覆盖普通怪物的基础数值。"""
        super().__init__(object_name, x, y, width, height, scale=BOSS_SCALE)
        self.title = "牛魔王"
        self.max_health = BOSS_MAX_HEALTH
        self.health = BOSS_MAX_HEALTH
        self.attack_damage = BOSS_ATTACK_DAMAGE
        self.attack_cooldown = BOSS_ATTACK_COOLDOWN
        self.enraged = False

    def take_damage(self, amount):
        """Boss 受伤后检查是否进入半血暴怒阶段。"""
        super().take_damage(amount)
        if (
            not self.defeated
            and not self.enraged
            and self.health <= self.max_health * BOSS_ENRAGE_HEALTH_RATIO
        ):
            self._enter_enraged_phase()

    def _enter_enraged_phase(self):
        """进入暴怒阶段：提高攻击伤害并缩短攻击冷却。"""
        self.enraged = True
        self.attack_damage = BOSS_ENRAGED_ATTACK_DAMAGE
        self.attack_cooldown = BOSS_ENRAGED_ATTACK_COOLDOWN

    def reset_for_retry(self):
        """玩家失败重试时，把 Boss 状态和数值恢复到初始状态。"""
        super().reset_for_retry()
        self.enraged = False
        self.attack_damage = BOSS_ATTACK_DAMAGE
        self.attack_cooldown = BOSS_ATTACK_COOLDOWN

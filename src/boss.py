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


class Boss(Monster):
    """牛魔王：复用 Monster 的动画 / 巡逻 / 战斗逻辑，只覆写数值与阶段变化。

    阶段变化：血量降到 BOSS_ENRAGE_HEALTH_RATIO 以下进入暴怒，攻击更强更快。
    沿用 cattle / magic 素材，不复制怪物逻辑。
    """

    def __init__(self, object_name, x, y, width, height):
        super().__init__(object_name, x, y, width, height, scale=BOSS_SCALE)
        self.title = "牛魔王"
        self.max_health = BOSS_MAX_HEALTH
        self.health = BOSS_MAX_HEALTH
        self.attack_damage = BOSS_ATTACK_DAMAGE
        self.attack_cooldown = BOSS_ATTACK_COOLDOWN
        self.enraged = False

    def take_damage(self, amount):
        super().take_damage(amount)
        if (
            not self.defeated
            and not self.enraged
            and self.health <= self.max_health * BOSS_ENRAGE_HEALTH_RATIO
        ):
            self._enter_enraged_phase()

    def _enter_enraged_phase(self):
        self.enraged = True
        self.attack_damage = BOSS_ENRAGED_ATTACK_DAMAGE
        self.attack_cooldown = BOSS_ENRAGED_ATTACK_COOLDOWN

    def reset_for_retry(self):
        super().reset_for_retry()
        self.enraged = False
        self.attack_damage = BOSS_ATTACK_DAMAGE
        self.attack_cooldown = BOSS_ATTACK_COOLDOWN

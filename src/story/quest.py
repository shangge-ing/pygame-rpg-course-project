from enum import Enum, auto


"""主线任务状态模块。

QuestManager 只负责记录“接任务 -> 清怪 -> 返回 -> 完成”的剧情进度。
Game 根据这些状态决定是否允许进寺庙、是否生成 Boss、是否显示完成界面。
"""


class QuestStage(Enum):
    """观音院主线任务的各个阶段。"""

    NOT_ACCEPTED = auto()
    ACCEPTED = auto()
    CLEARED = auto()
    RETURNED = auto()
    COMPLETE = auto()


class QuestManager:
    """西游记观音院主线任务状态机。

    流程：土地公给任务 -> 进入观音院 -> 击败妖怪 -> 返回村庄复命 -> 结局。
    剧情推进集中在此处，Game 只负责在合适时机调用并查询状态，
    避免剧情逻辑散落在交互代码里。
    """

    DIALOGS = {
        "god": {
            QuestStage.NOT_ACCEPTED: "大圣，观音院近日妖气缠身，恳请您前去降妖除魔！",
            QuestStage.ACCEPTED: "观音院就在前方，万望大圣多加小心。",
            QuestStage.CLEARED: "观音院就在前方，万望大圣多加小心。",
            QuestStage.RETURNED: "大圣可是降妖归来？快与老朽说说经过。",
            QuestStage.COMPLETE: "妖患已除，观音院重归安宁，多谢大圣！",
        },
    }

    def __init__(self):
        """任务初始状态：玩家还没有向土地公接任务。"""
        self.stage = QuestStage.NOT_ACCEPTED

    def accept(self):
        """土地公交代任务后，进入已接任务状态。"""
        if self.stage == QuestStage.NOT_ACCEPTED:
            self.stage = QuestStage.ACCEPTED

    def clear_monsters(self):
        """寺庙怪物清完后，标记为等待回村复命。"""
        if self.stage == QuestStage.ACCEPTED:
            self.stage = QuestStage.CLEARED

    def mark_returned(self):
        """玩家从寺庙返回村庄后，进入复命阶段。"""
        if self.stage == QuestStage.CLEARED:
            self.stage = QuestStage.RETURNED

    def complete(self):
        """和土地公交任务后，主线完成。"""
        if self.stage == QuestStage.RETURNED:
            self.stage = QuestStage.COMPLETE

    @property
    def can_enter_temple(self):
        """是否允许玩家从郊外进入寺庙。"""
        return self.stage in (QuestStage.ACCEPTED, QuestStage.CLEARED)

    @property
    def should_return_to_village(self):
        """是否到了清怪后应该回村复命的阶段。"""
        return self.stage == QuestStage.CLEARED

    @property
    def is_complete(self):
        """主线任务是否已经完成。"""
        return self.stage == QuestStage.COMPLETE

    def dialog_for(self, layer_name):
        """返回指定 NPC 在当前任务阶段应该说的话，没有阶段台词时返回 None。"""
        stage_dialogs = self.DIALOGS.get(layer_name)
        if not stage_dialogs:
            return None
        return stage_dialogs.get(self.stage)

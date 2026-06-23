from enum import Enum, auto


class QuestStage(Enum):
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
        self.stage = QuestStage.NOT_ACCEPTED

    def accept(self):
        if self.stage == QuestStage.NOT_ACCEPTED:
            self.stage = QuestStage.ACCEPTED

    def clear_monsters(self):
        if self.stage == QuestStage.ACCEPTED:
            self.stage = QuestStage.CLEARED

    def mark_returned(self):
        if self.stage == QuestStage.CLEARED:
            self.stage = QuestStage.RETURNED

    def complete(self):
        if self.stage == QuestStage.RETURNED:
            self.stage = QuestStage.COMPLETE

    @property
    def can_enter_temple(self):
        return self.stage in (QuestStage.ACCEPTED, QuestStage.CLEARED)

    @property
    def should_return_to_village(self):
        return self.stage == QuestStage.CLEARED

    @property
    def is_complete(self):
        return self.stage == QuestStage.COMPLETE

    def dialog_for(self, layer_name):
        """返回当前阶段下该 NPC 的台词，没有阶段台词时返回 None（由调用方回退到默认台词）。"""
        stage_dialogs = self.DIALOGS.get(layer_name)
        if not stage_dialogs:
            return None
        return stage_dialogs.get(self.stage)

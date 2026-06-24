"""通用帧动画工具。

角色、NPC、怪物和特效都可以使用 Animation 保存一组图片帧，并按时间
自动切换当前帧。它只负责“哪一帧该显示”，不负责具体绘制位置。
"""

class Animation:
    """按固定时间间隔播放一组 Surface 帧。"""

    def __init__(self, frames, frame_time, loop=True):
        """保存动画帧、每帧时长，以及是否循环播放。"""
        self.frames = frames
        self.frame_time = frame_time
        self.loop = loop
        self.frame_index = 0
        self.elapsed = 0.0
        self.finished = False

    @property
    def current_frame(self):
        """返回当前应该显示的图片帧。"""
        return self.frames[self.frame_index]

    def reset(self):
        """把动画重置到第一帧，常用于攻击、死亡等动作重新播放。"""
        self.frame_index = 0
        self.elapsed = 0.0
        self.finished = False

    def update(self, dt):
        """根据经过的时间 dt 推进动画帧。"""
        if self.finished or len(self.frames) <= 1:
            return

        self.elapsed += dt
        if self.elapsed < self.frame_time:
            return

        self.elapsed = 0.0
        self.frame_index += 1
        if self.frame_index < len(self.frames):
            return

        if self.loop:
            self.frame_index = 0
        else:
            self.frame_index = len(self.frames) - 1
            self.finished = True

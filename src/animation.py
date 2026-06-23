class Animation:
    def __init__(self, frames, frame_time, loop=True):
        self.frames = frames
        self.frame_time = frame_time
        self.loop = loop
        self.frame_index = 0
        self.elapsed = 0.0
        self.finished = False

    @property
    def current_frame(self):
        return self.frames[self.frame_index]

    def reset(self):
        self.frame_index = 0
        self.elapsed = 0.0
        self.finished = False

    def update(self, dt):
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

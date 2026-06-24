"""游戏启动入口。

这个文件只负责创建 Game 对象并启动主循环。真正的游戏逻辑都在
src/game.py 中，答辩或讲解项目时可以把 main.py 理解为“打开游戏的开关”。
"""

from src.game import Game


def main():
    """创建游戏对象并开始运行。"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

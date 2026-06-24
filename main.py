"""项目入口：启动基础 Pygame RPG。"""

from src.game import Game


def main():
    """创建游戏对象并进入主循环。"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

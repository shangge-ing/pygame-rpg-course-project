# Claude Code 项目交接说明

本文档用于让 Claude Code 或其他代码助手快速理解当前项目状态。当前代码已经是
课程展示用的完整 Pygame RPG 版本，不需要再从聊天记录中还原开发过程。

## 项目概述

项目名称：西游记观音院

项目类型：基于 Python、Pygame、PyTMX 和 Tiled 地图资源的 2D RPG 小游戏。

当前入口：

```powershell
python main.py
```

或双击：

```text
start_game.bat
```

## 当前功能状态

- 开始界面、操作说明界面、暂停界面。
- 村庄、郊外、寺庙多场景流程。
- 孙悟空移动、摄像机跟随、地图边界和 obstacle 碰撞。
- NPC 加载、NPC 待机动画、对话框和任务推进。
- 村庄接任务、进入郊外、进入寺庙、清怪、Boss、返回村庄复命。
- 怪物动画、死亡动画和消失特效。
- 回合制战斗系统：
  - `J` / `1` 普通攻击；
  - `K` / `2` 技能攻击；
  - `D` / `3` 防御；
  - `Esc` 撤退。
- 孙悟空 `swk2` 战斗攻击动画。
- 背景音乐、攻击音效、胜利音效和 `M` 静音控制。
- 胜利、失败、重新挑战和最终完成界面。

## 主要目录

```text
main.py              游戏入口
start_game.bat       Windows 一键启动脚本
src/                 游戏源码
resource/            地图、图片、音频和字体资源
docs/                辅助文档和预览图
requirements.txt     Python 依赖
```

## 重要模块

- `src/game.py`：主循环、输入分发、场景切换、任务推进。
- `src/battle.py`：回合制战斗状态机和战斗 UI。
- `src/scene.py`：地图、NPC、怪物和 Boss 的场景组织。
- `src/player.py`：孙悟空移动、动画、碰撞。
- `src/monster.py`：怪物动画、巡逻、死亡和消失。
- `src/npc.py`：NPC 图片、动画、对话信息。
- `src/ui.py`：开始、帮助、暂停、胜利和失败界面。
- `src/audio.py`：背景音乐、攻击音效、胜利音效和静音。
- `src/settings.py`：资源路径和核心数值配置。

## 注意事项

- 不要移动、删除或重命名 `resource/`。
- 不要修改 `.tmx` 地图文件，除非明确需要重新编辑地图。
- 不要提交 `.venv/`、`.idea/`、zip 文件或 Tiled 安装包。
- 当前 Git 历史中的 v1/v2/v3 是答辩前按阶段整理出的版本记录，不代表真实逐日开发历史。

# 西游记观音院 Pygame RPG

一个使用 Python、Pygame 和 Tiled 地图制作的 2D RPG 小游戏。玩家扮演孙悟空，从村庄出发前往观音院，击败妖怪并完成冒险。

## 游戏内容

- 探索村庄、郊外、森林和观音院四个场景
- 与土地公、老人、孩童等 NPC 对话
- 接取主线任务并前往观音院
- 与牛怪小怪战斗
- 击败 Boss 牛魔王
- 回到村庄完成冒险
- 支持背景音乐、攻击音效、胜利音效和静音切换

## 运行环境

- Python 3.11
- pygame
- pytmx

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

启动游戏：

```powershell
python main.py
```

如果使用本地虚拟环境：

```powershell
.\.venv\Scripts\python.exe main.py
```

## 操作方式

| 按键 | 功能 |
| --- | --- |
| `Enter` | 开始游戏 |
| `H` | 查看操作说明 |
| 方向键 | 移动 |
| `E` / 空格 | 对话、交互、场景切换 |
| `J` | 战斗攻击 |
| `P` | 暂停 / 继续 |
| `M` | 静音 / 恢复音频 |
| `R` | 战斗失败后重新挑战 |
| `Esc` | 返回、撤退或退出 |

## 游戏流程

```text
开始界面
-> 村庄
-> 与土地公对话
-> 前往郊外
-> 穿过森林
-> 进入观音院
-> 击败小怪
-> 挑战牛魔王
-> 返回村庄
-> 完成冒险
```

## 项目结构

```text
project-root/
  main.py                 # 游戏入口
  requirements.txt        # Python 依赖
  smoke_test.py           # 地图加载测试脚本
  tiled_render.py         # 早期 TMX 渲染辅助脚本
  README.md               # 项目说明
  docs/
    swk2_preview.png      # 孙悟空动作帧预览
  resource/
    font/                 # 字体资源
    img/                  # 图片、角色、怪物、UI、特效资源
    sound/                # 音频资源
    tmx/                  # Tiled 地图文件
  src/
    animation.py          # 通用动画
    audio.py              # 音频管理
    battle.py             # 战斗系统
    boss.py               # Boss 牛魔王
    camera.py             # 摄像机
    dialog.py             # 对话框
    game.py               # 游戏主循环
    game_state.py         # 游戏状态
    monster.py            # 怪物逻辑
    npc.py                # NPC 逻辑
    player.py             # 玩家逻辑
    quest.py              # 主线任务状态
    scene.py              # 场景加载与管理
    settings.py           # 配置和资源路径
    swk2_preview.py       # 动作帧预览图生成脚本
    tmx_map.py            # TMX 地图加载
    ui.py                 # 界面绘制
```

## 资源说明

游戏运行依赖 `resource/` 目录中的地图、图片、音频和字体资源。请保持该目录结构不变，不要移动或重命名其中的文件。

主要使用的资源包括：

- `resource/tmx/village1.tmx`
- `resource/tmx/scene.tmx`
- `resource/tmx/forest.tmx`
- `resource/tmx/temple1.tmx`
- `resource/img/郊外.jpg`
- `resource/img/swk`
- `resource/img/swk2`
- `resource/img/god`
- `resource/img/elder`
- `resource/img/cattle`
- `resource/img/magic`
- `resource/img/dialog/dialog.png`
- `resource/sound`
- `resource/font/newfont.TTF`

## 开发说明

本项目是一个轻量级 Pygame RPG 示例，代码按照概要设计中的分层结构组织在 `src/` 目录下：

- `src/core/`：入口调度层，包含 `Game` 主控制器和 `GameState` 状态枚举。
- `src/config/`：配置与资源层，集中保存地图、图片、音频路径和核心数值。
- `src/world/`：地图与场景层，负责 TMX 地图加载、对象层解析和场景对象组织。
- `src/character/`：玩家与摄像机层，负责孙悟空移动、碰撞和镜头跟随。
- `src/story/`：NPC 与剧情层，负责 NPC、对话框和主线任务状态。
- `src/combat/`：怪物与战斗层，负责小怪、Boss、战斗流程和胜负判定。
- `src/presentation/`：表现层，负责 UI、音频和通用帧动画。
- `src/tools/`：辅助工具脚本，例如孙悟空动作帧预览图生成。

核心流程由 `src/core/game.py` 统一调度，地图和对象信息来自 Tiled `.tmx` 文件，角色、怪物和 UI 都基于 Pygame Surface 绘制。

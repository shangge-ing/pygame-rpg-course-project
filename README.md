# 西游记观音院 Pygame RPG

这是一个基于 Python + Pygame + PyTMX + Tiled 的 2D RPG 课程项目。项目主题为“西游记观音院”，玩家控制孙悟空在村庄接取任务，前往观音院击败妖怪和 Boss 牛魔王，最后回村复命完成冒险。

## 运行环境

- Python 3.11.9
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

如果使用项目虚拟环境：

```powershell
.\.venv\Scripts\python.exe main.py
```

## 操作说明

- `Enter`：开始游戏
- `H`：查看操作说明
- 方向键：移动孙悟空
- `E` / 空格：对话、交互、场景切换
- `J`：战斗攻击
- `P`：暂停 / 继续
- `M`：静音 / 恢复音频
- `R`：失败后重新挑战
- `Esc`：返回、撤退或退出

## 当前完整流程

```text
开始界面
-> 村庄
-> 与土地公对话接任务
-> 郊外
-> 寺庙 / 观音院
-> 4 个小怪战斗
-> Boss 牛魔王
-> 回到郊外
-> 回村复命
-> 完成界面
```

## 已实现功能

- 开始界面、操作说明界面、暂停界面
- 村庄、郊外、寺庙三个场景
- Tiled `.tmx` 地图加载与渲染
- 玩家孙悟空显示、方向键移动、摄像机跟随
- 地图障碍物碰撞与边界限制
- 土地公、老人、孩童 NPC
- NPC 对话框与中文字体显示
- 土地公和老人待机动画
- 孩童 NPC 的 Pygame 绘制形象
- 村庄 -> 郊外 -> 寺庙 -> 郊外 -> 村庄的主线流程
- 牛怪小怪加载、巡逻、警戒、追击、返回与战斗触发
- 小怪战斗、怪物反击、玩家失败与重新挑战
- 小怪全部击败后生成 Boss 牛魔王
- Boss 牛魔王战斗、暴怒阶段与任务推进
- 孙悟空 `swk2` 战斗攻击动画
- 命中特效、怪物死亡动画和消失特效
- 背景音乐、攻击音效、胜利音效与静音控制
- 胜利 / 失败 / 最终完成界面
- `docs/swk2_preview.png` 动作帧预览图

## 已知简化点与答辩风险

- 郊外场景主要作为村庄和寺庙之间的过渡场景，当前没有障碍物和 NPC。
- 寺庙清除 Boss 后，返回郊外的交互限制较宽，不强制玩家走到固定出口。
- 战斗系统是课程演示用的简化战斗：核心操作是按 `J` 攻击，怪物按冷却反击，没有复杂技能、背包、装备或存档系统。
- Boss 使用现有牛怪素材和数值强化实现，没有单独 Boss 专属美术资源。
- `test.tmx` 不作为正式流程地图使用。
- 运行前需要确保 `resource/` 目录完整保留，不能移动或重命名资源文件。

## 项目结构

```text
project-root/
  main.py                 # 正式游戏入口
  requirements.txt        # Python 依赖
  smoke_test.py           # 早期地图加载冒烟测试
  tiled_render.py         # 早期 TMX 渲染辅助
  CLAUDE_HANDOFF.md       # 给 Claude / 后续维护者的交接说明
  docs/
    swk2_preview.png      # 孙悟空 swk2 动作帧预览
  resource/
    font/                 # 中文字体
    img/                  # 角色、怪物、UI、特效图片
    sound/                # 背景音乐和音效
    tmx/                  # Tiled 地图
  src/
    animation.py          # 通用帧动画
    audio.py              # 音频管理
    battle.py             # 战斗系统
    boss.py               # Boss 牛魔王
    camera.py             # 摄像机
    dialog.py             # 对话框
    game.py               # 游戏主循环与流程协调
    game_state.py         # 游戏状态枚举
    monster.py            # 牛怪实体与 AI
    npc.py                # NPC 实体
    player.py             # 玩家孙悟空
    quest.py              # 主线任务状态
    scene.py              # 场景封装
    settings.py           # 配置与资源路径
    swk2_preview.py       # swk2 预览图生成脚本
    tmx_map.py            # TMX 地图加载与对象层读取
    ui.py                 # 开始、帮助、暂停、提示和结果界面
```

## 最终验收记录

自动化验收结果显示：村庄加载 10 个 NPC 和 146 个障碍物；寺庙加载 4 个小怪和 165 个障碍物；清除 4 个小怪后生成 Boss 牛魔王；Boss 击败后任务进入 `CLEARED`；返回村庄复命后进入 `COMPLETE` 并显示完成界面。

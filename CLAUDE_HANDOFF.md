# Claude Code 项目交接说明

本文档用于让 Claude Project / Claude Code 在不阅读完整聊天记录的情况下接手当前课程项目。当前仓库目标是保存一份已经验收通过的 Pygame RPG 答辩演示版，不建议继续在此版本上大幅扩展功能。

## 项目概况

- 项目名称：西游记观音院 Pygame RPG
- 项目类型：基于 Pygame 的 2D RPG 角色扮演小游戏
- 开发语言：Python 3.11.9
- 主要依赖：pygame、pytmx
- 正式入口：`main.py`
- 资源目录：`resource/`

当前主流程：

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

## 运行方法

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

`.venv/` 是本机虚拟环境，不应提交到 GitHub。其他机器接手时应重新创建虚拟环境并安装 `requirements.txt`。

## 目录结构

```text
main.py
requirements.txt
smoke_test.py
tiled_render.py
README.md
CLAUDE_HANDOFF.md
docs/
  swk2_preview.png
resource/
  font/
  img/
  sound/
  tmx/
src/
  animation.py
  audio.py
  battle.py
  boss.py
  camera.py
  dialog.py
  game.py
  game_state.py
  monster.py
  npc.py
  player.py
  quest.py
  scene.py
  settings.py
  swk2_preview.py
  tmx_map.py
  ui.py
```

## 核心文件说明

- `main.py`：正式入口，只负责创建并运行 `Game`。
- `src/game.py`：游戏主循环、事件处理、状态切换、场景切换、任务推进和整体协调。
- `src/game_state.py`：开始、帮助、暂停、村庄探索、郊外探索、寺庙探索、战斗、完成、失败等状态。
- `src/scene.py`：封装村庄、郊外和寺庙场景，加载地图、NPC、怪物和 Boss 出生点。
- `src/tmx_map.py`：加载 Tiled `.tmx` 地图，渲染静态图层，读取对象层和障碍物矩形。
- `src/player.py`：孙悟空行走动画、移动、地图边界和障碍物碰撞。
- `src/npc.py`：土地公、老人、孩童 NPC；土地公和老人待机动画；孩童由 Pygame 绘制。
- `src/dialog.py`：底部对话框，使用 `resource/img/dialog/dialog.png` 和中文字体。
- `src/quest.py`：主线任务状态机，负责接任务、清怪、回村、完成。
- `src/monster.py`：牛怪实体、动画状态、巡逻、警戒、追击、返回、受击、死亡和消失。
- `src/boss.py`：Boss 牛魔王，继承牛怪逻辑，增加高血量、强化攻击和暴怒阶段。
- `src/battle.py`：简化战斗系统，玩家按 `J` 攻击，怪物按冷却反击，支持失败和胜利。
- `src/audio.py`：背景音乐、攻击音效、胜利音效和静音控制。
- `src/ui.py`：开始界面、帮助界面、暂停界面、场景提示、胜利/失败/完成界面。
- `src/settings.py`：窗口、速度、血量、动画参数和资源路径。
- `src/swk2_preview.py`：生成 `docs/swk2_preview.png` 的工具脚本，不是正式游戏入口。

## 当前已实现功能

- 开始界面、操作说明界面、暂停界面
- 村庄、郊外、寺庙三个场景
- Tiled 地图加载和静态图层渲染
- 玩家孙悟空显示、移动、摄像机跟随
- 障碍物碰撞和地图边界限制
- 土地公、老人、孩童 NPC
- NPC 对话与主线任务触发
- 土地公和老人待机动画
- 孩童 NPC 的简单绘制形象
- 村庄到郊外、郊外到寺庙、寺庙回郊外、郊外回村庄的流程
- 寺庙 4 个牛怪小怪
- 牛怪待机、观察、巡逻、追击、返回、战斗、死亡和消失动画
- 小怪战斗、怪物反击、玩家失败、按 `R` 重新挑战
- 小怪全部击败后生成 Boss 牛魔王
- Boss 牛魔王战斗、暴怒阶段、击败后推进任务
- 孙悟空 `swk2` 战斗攻击动画
- 命中特效、死亡特效、消失特效
- 背景音乐、攻击音效、胜利音效、静音控制
- 胜利/失败/最终完成界面
- `docs/swk2_preview.png` 动作帧预览图

## 当前使用资源

地图：

- `resource/tmx/village1.tmx`
- `resource/tmx/scene.tmx`
- `resource/tmx/temple1.tmx`
- `resource/tmx/temple.tmx` 作为寺庙 fallback

图片：

- `resource/img/swk`
- `resource/img/swk2` 中第 33 到 40 帧用于战斗攻击动画
- `resource/img/god`
- `resource/img/elder`
- `resource/img/cattle/station`
- `resource/img/cattle/look`
- `resource/img/cattle/walk1`
- `resource/img/cattle/walk2`
- `resource/img/cattle/run`
- `resource/img/cattle/back`
- `resource/img/cattle/fight`
- `resource/img/cattle/die`
- `resource/img/magic/appear`
- `resource/img/magic/disappear`
- `resource/img/dialog/dialog.png`
- `resource/img/button/ok.png`
- `resource/img/button/no.png`
- `resource/img/button/temple_button.png`
- `resource/img/village_button.png`
- `resource/img/temple_button.png`
- `resource/img/pic.jpg`
- `resource/img/win.jpg`
- `resource/img/fail.jpg`

音频：

- `resource/sound/nmw.mp3`：背景音乐
- `resource/sound/swk.wav`：攻击音效
- `resource/sound/aigei.mp3`：胜利音效

字体：

- `resource/font/newfont.TTF`

## 已知简化点

- 郊外场景主要作为村庄和寺庙之间的过渡场景，当前没有 NPC、怪物和障碍物。
- 寺庙清除 Boss 后，返回郊外的交互限制较宽，不强制玩家走到固定出口。
- 战斗系统是课程演示用的简化战斗，没有复杂技能、背包、装备、等级、存档或任务列表。
- Boss 使用现有牛怪素材和数值强化实现，没有独立 Boss 专属美术资源。
- `test.tmx` 不作为正式流程地图使用。
- `resource/` 目录必须保持原结构，不能移动、删除或重命名资源文件。

## 最终验收记录

已执行基础检查：

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m compileall -q main.py src
```

自动化流程验收结果：

- 初始状态：`START`
- 村庄地图尺寸：`(3780, 2395)`
- 村庄 NPC 数量：`10`
- 村庄障碍物数量：`146`
- 郊外地图尺寸：`(1376, 768)`
- 寺庙地图尺寸：`(1999, 1495)`
- 寺庙出生点：`(686.333, 1032.67)`
- 寺庙障碍物数量：`165`
- 寺庙初始小怪数量：`4`
- 清除 4 个小怪后生成 Boss 牛魔王
- Boss 击败后任务进入 `CLEARED`
- 回村复命后任务进入 `COMPLETE`
- 最终完成提示可显示
- 字体、按钮、开始背景、胜利图、失败图、怪物动画、战斗特效和 swk2 攻击动画未发现资源加载错误

## 后续建议

当前版本建议冻结为课程答辩可演示版。后续如果继续开发，优先级应是：

1. 做人工通关截图和答辩材料。
2. 整理课程报告、演示脚本和功能说明。
3. 小修 UI 文案或路线提示，不要大改主流程。
4. 如需扩展，再单独开新分支实现技能、背包、存档或更复杂 Boss 机制。

## 注意事项

- 不要提交 `.venv/`。
- 不要提交 `resource.zip`、Tiled 安装包、课件目录或本地 IDE 配置。
- 不要移动 `resource/`。
- 不要修改 `.tmx` 文件，除非明确进入地图编辑阶段。
- 不要把 `journey to the west/` 当作当前主项目。
- 不要继续把功能堆进冻结版；答辩前优先保证稳定。

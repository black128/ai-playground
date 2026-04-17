# Python Snake Game

一个使用 Python 标准库实现的贪吃蛇游戏，包含：

- 产品化浏览器图形界面，由 Python 本地启动并在浏览器中渲染
- 稳定可用的终端模式，包含动态状态栏和节奏动画
- 可测试的独立游戏引擎
- 随等级递增的难度和速度曲线
- 最高分持久化存储
- 单元测试
- 详细设计文档
- Bug 修复文档

## 运行方式

```bash
python3 main.py
```

默认启动终端版，兼容性最好。

如果需要图形界面版：

```bash
python3 main.py --mode gui
```

该模式会启动一个本地 Python 服务，并自动在浏览器中打开可视化界面。

## 游戏操作

- 方向键 / `WASD`：控制蛇移动
- `Enter`：开始新一局
- `Space`：暂停 / 继续
- `R`：重新开始
- `Q`：退出终端版
- 关闭浏览器标签页后，可在启动它的终端中按 `Ctrl+C` 结束图形版服务

## 产品特性

- 分数系统：每次吃到食物获得 `10` 分
- 难度系统：每吃 `4` 个食物提升 `1` 级，蛇会继续加速直到最小速度阈值
- 动画表现：浏览器图形版包含食物脉冲、等级横幅、吃食物粒子效果
- 最高分：自动保存在本机 `~/.snake_game/scores.json`

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```

## 项目结构

```text
.
├── main.py
├── README.md
├── snake_game
│   ├── __init__.py
│   ├── app.py
│   ├── engine.py
│   ├── storage.py
│   └── terminal_app.py
└── tests
    ├── test_engine.py
    ├── test_storage.py
    └── test_terminal_app.py
```

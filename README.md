# Python Snake Game

一个使用 Python 标准库实现的贪吃蛇游戏，包含：

- 可直接运行的 `tkinter` 图形界面
- 可测试的独立游戏引擎
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

## 游戏操作

- 方向键 / `WASD`：控制蛇移动
- `Space`：暂停 / 继续
- `R`：重新开始
- `Q`：退出终端版

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
│   └── terminal_app.py
└── tests
    ├── test_engine.py
    └── test_terminal_app.py
```

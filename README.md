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

## 游戏操作

- 方向键：控制蛇移动
- `Space`：暂停 / 继续
- `R`：重新开始

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
│   └── engine.py
└── tests
    └── test_engine.py
```

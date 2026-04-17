# 贪吃蛇游戏 Bug 修复文档

## 1. 文档目的

本文档用于记录开发和测试阶段关注的典型缺陷风险，以及对应的修复与规避方案，帮助后续维护时快速理解设计原因。

## 2. 已处理问题与修复方案

### 2.1 反向移动导致瞬时自撞

问题描述：

如果允许蛇在向右移动时立即向左移动，会出现蛇头直接撞向自身的情况。

修复方案：

- 在 `set_direction()` 中拦截与当前方向相反的输入
- 保持原方向不变，避免非法转向

验证方式：

- 单元测试 `test_reverse_direction_is_ignored`

### 2.2 尾巴位置误判为碰撞

问题描述：

蛇在未吃到食物时，尾巴会在当前步被移除。如果碰撞检测仍然把旧尾巴位置算作身体，会把本来合法的移动错误判定为失败。

修复方案：

- 在 `tick()` 中区分“增长”和“非增长”两种情况
- 非增长时，碰撞检测只检查 `snake[:-1]`

验证方式：

- 单元测试 `test_moving_into_old_tail_position_is_allowed`

### 2.3 食物生成到蛇身体上

问题描述：

若食物随机生成在蛇身体上，会导致玩家无法正常吃到该食物，造成逻辑错误。

修复方案：

- 在 `_spawn_food()` 中仅从空闲格子集合中随机选择位置

验证方式：

- 单元测试 `test_reset_initializes_snake_and_food`
- 单元测试 `test_eating_food_increases_score_and_length`

### 2.4 棋盘填满后的异常状态

问题描述：

当蛇吃掉最后一个食物后，如果棋盘已经没有空格，继续生成食物会失败，若不处理会导致状态不一致。

修复方案：

- `_spawn_food()` 在无可用位置时返回 `None`
- `tick()` 检测到 `food is None` 后标记 `won = True`

验证方式：

- 单元测试 `test_win_when_board_is_filled`

### 2.5 非法配置未被提前拦截

问题描述：

如果初始蛇长度大于地图宽度，初始化布局会越界，导致异常状态。

修复方案：

- 在 `reset()` 中加入参数校验
- 对不合法配置直接抛出 `ValueError`

验证方式：

- 单元测试 `test_invalid_initial_length_raises`

### 2.6 图形界面在当前环境中不可稳定显示

问题描述：

在当前机器环境下，`tkinter` 图形窗口可以被创建，但实际显示内容不稳定，导致用户看到空白窗口，影响可用性。

修复方案：

- 将图形版切换为“Python 启动、本地浏览器渲染”的实现
- 保留基于 `curses` 的终端版作为默认启动模式
- 将浏览器版作为 `python3 main.py --mode gui` 的稳定可视化入口

验证方式：

- 浏览器版接口烟测通过
- 实际启动后浏览器可见完整游戏界面

### 2.7 终端环境不支持隐藏光标导致启动崩溃

问题描述：

部分终端环境不支持 `curses.curs_set(0)`，直接调用会抛出 `_curses.error`，导致终端版启动失败。

修复方案：

- 对 `curses.curs_set(0)` 增加异常兼容处理
- 当终端不支持该能力时，忽略该错误并继续运行

验证方式：

- 实际启动 `python3 main.py`
- 确认程序不再因为 `curs_set()` 报错退出

## 3. 回归测试策略

每次修改核心逻辑后，至少执行以下验证：

```bash
python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/tmp/python-cache python3 -m compileall .
```

## 4. 结论

当前版本重点修复了方向控制、碰撞判定、食物生成、胜利判定和配置边界等核心风险点，并通过自动化测试进行回归验证。

## 2.8 难度递增后速度失控或不生效

问题描述：

加入等级系统后，如果速度曲线没有最小值保护，后期可能快到不可玩；如果升级逻辑写错，又会出现等级变化但速度不变的问题。

修复方案：

- 在 `GameConfig` 中增加 `base_speed_ms`、`speed_step_ms` 和 `min_speed_ms`
- 在 `SnakeGame.speed_ms` 中统一计算速度，并强制应用最小阈值
- 使用 `foods_per_level` 控制升级节奏，避免界面层重复计算

验证方式：

- 单元测试 `test_level_increases_and_speed_gets_faster`
- 单元测试 `test_speed_respects_minimum_value`

## 2.9 最高分文件异常导致程序不可用

问题描述：

产品化后加入最高分持久化，如果文件不存在、格式损坏或读取失败，程序启动时可能直接报错。

修复方案：

- 新增 `ScoreStorage`
- 对文件不存在、JSON 损坏和数据类型异常统一回退为 `0`
- 保存时仅在新分数更高时覆盖原记录

验证方式：

- 单元测试 `test_missing_file_returns_zero`
- 单元测试 `test_invalid_json_returns_zero`
- 单元测试 `test_save_best_score_persists_highest_value`

## 2.10 动画层与游戏逻辑耦合导致节奏异常

问题描述：

如果将动画刷新和游戏移动绑定在同一个时钟上，随着等级提升，界面会变得过快且难以阅读；暂停时也无法保持动画和界面提示。

修复方案：

- GUI 模式拆分为逻辑时钟和渲染时钟
- 终端模式使用固定刷新频率，并基于时间戳决定何时真正推进游戏
- 引擎通过 `TickResult` 向界面层暴露“吃到食物”“升级”等事件，避免界面重复推断

验证方式：

- GUI 启动烟测
- 终端实际运行烟测

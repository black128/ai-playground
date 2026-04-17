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

## 3. 回归测试策略

每次修改核心逻辑后，至少执行以下验证：

```bash
python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/tmp/python-cache python3 -m compileall .
```

## 4. 结论

当前版本重点修复了方向控制、碰撞判定、食物生成、胜利判定和配置边界等核心风险点，并通过自动化测试进行回归验证。

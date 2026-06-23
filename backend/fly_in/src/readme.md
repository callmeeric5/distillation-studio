下面按代码流程解释：先寻路，再调度。

**整体流程**

`main.py` 里大概是：

```python
config = Parser(path).parse()
graph = Graph(config)
paths = Solver(graph).solve_all()
scheduler = Scheduler(graph, paths)
scheduler.run()
```

也就是说：

1. `Parser` 读地图文件。
2. `Graph` 把 zones/connections 变成图结构。
3. `Solver` 给每架 drone 分配一条路径。
4. `Scheduler` 按 turn 模拟移动，输出每回合发生的动作。

**寻路算法**

核心在 [src/algo.py](/Users/ericwindsor/Downloads/Fly_In/src/algo.py:22)。

有两个层次。

第一层是 `solve()`，它找单条最低成本路径：

```python
priority_queue: list[tuple[float, str]] = []
distance: dict[str, float] = {self.graph.start: 0}
```

这里用的是 Dijkstra 思路：

- 从 `start` 开始。
- 每次从优先队列里取当前总成本最低的 zone。
- 遍历它的 neighbor。
- 如果 neighbor 是 `blocked`，跳过。
- 否则计算新成本。
- 如果新成本更低，就更新 `previous` 和 `distance`。

成本由 `_cost()` 决定：

```python
restricted -> 2
priority -> 0.5
normal -> 1
```

也就是说：

- `restricted` 慢，所以成本高。
- `priority` 是推荐路径，所以寻路时成本更低。
- `blocked` 完全不能走。

`previous` 用来最后反向还原路径，比如：

```text
goal <- waypoint2 <- waypoint1 <- start
```

最终变成：

```text
start -> waypoint1 -> waypoint2 -> goal
```

第二层是 `find_paths()`，它不是只找一条路径，而是找多条候选路径。

位置：[src/algo.py](/Users/ericwindsor/Downloads/Fly_In/src/algo.py:46)

```python
queue = [(0, 0, [self.graph.start])]
```

队列里存的是：

```python
(cost, path_length, path)
```

例如：

```python
(3, 4, ["start", "a", "b", "goal"])
```

它的逻辑是：

1. 从最低成本 path 开始扩展。
2. 当前 path 的最后一个 zone 如果是 `end`，保存为可用路径。
3. 否则继续扩展 neighbor。
4. 不允许重复进入已经在 path 里的 zone，避免 loop。
5. 不允许进入 blocked zone。
6. 找到的候选路径数量够分配给 drones 后停止；如果没有更多路径，队列会自然为空。

邻居排序在 `_ordered_neighbors()`：

```python
key=lambda name: (
    self._cost(name),
    distance_to_end,
    name,
)
```

意思是优先尝试：

1. 成本低的 zone。
2. 坐标上更靠近终点的 zone。
3. 名字排序稳定输出。

所以它不是暴力 DFS，而是“优先扩展看起来更好的路径”。

**路径分配算法**

位置：[src/algo.py](/Users/ericwindsor/Downloads/Fly_In/src/algo.py:78)

```python
def solve_all(self) -> list[list[str]]:
```

这个函数给每架 drone 分配路径。

它先拿到候选路径：

```python
paths = self.find_paths()
```

然后维护每条路径已经分配了多少 drone：

```python
loads = [0 for _ in paths]
```

每次给一个 drone 选路径时，会选预计完成时间最小的路径：

```python
index = min(
    range(len(paths)),
    key=lambda i: self._estimated_finish(paths[i], loads[i]),
)
```

预计完成时间在这里：

```python
return self.graph.path_cost(path) + (assigned / capacity)
```

意思是：

```text
路径本身成本 + 当前已经分配的 drone 数 / 路径瓶颈容量
```

举例：

```text
path A 成本 4，容量 1，已经分配 3 架
estimated = 4 + 3 / 1 = 7

path B 成本 5，容量 3，已经分配 3 架
estimated = 5 + 3 / 3 = 6
```

虽然 B 路径更长，但容量更大，所以可能更适合继续分配。

路径容量来自 [src/graph.py](/Users/ericwindsor/Downloads/Fly_In/src/graph.py:47)：

```python
return max(1, min(capacities, default=self.nb_drones))
```

也就是一条路径的容量等于它所有 zone capacity 和 link capacity 里的最小值，也就是瓶颈。

**调度算法**

核心在 [src/scheduler.py](/Users/ericwindsor/Downloads/Fly_In/src/scheduler.py:35)。

`Scheduler` 拿到的是：

```python
graph
paths
```

然后创建 drones：

```python
self.drones = [
    Drone(path=path, id=index + 1)
    for index, path in enumerate(paths)
]
```

每架 drone 有自己的 path，例如：

```python
Drone(
    id=1,
    path=["start", "waypoint1", "waypoint2", "goal"],
    pos=0,
)
```

`pos` 表示当前在 path 的第几个位置。

例如：

```text
pos = 0 -> start
pos = 1 -> waypoint1
pos = 2 -> waypoint2
```

**每回合发生什么**

位置：[src/scheduler.py](/Users/ericwindsor/Downloads/Fly_In/src/scheduler.py:35)

```python
while not self._all_delivered():
    turn += 1
    self._advance_transit()
    moves = self._move_available_drones()
```

每一回合分两步：

1. 先处理已经在路上的 drone 是否到达。
2. 再尝试让可以移动的 drone 出发。

为什么要先 `_advance_transit()`？

因为 `restricted` zone 需要 2 turn 才能到达。Drone 可能上一回合已经出发了，这一回合要先减少它的剩余移动时间。

**Drone 状态**

在 [src/drone.py](/Users/ericwindsor/Downloads/Fly_In/src/drone.py:5)：

```python
ACTIVE
IN_TRANSIT
DELIVERED
```

含义：

- `ACTIVE`：在某个 zone 里，可以尝试移动。
- `IN_TRANSIT`：正在 connection 上移动，还没到目标 zone。
- `DELIVERED`：已经到达 end，不再参与调度。

开始移动时：

```python
drone.start_move(duration)
```

位置：[src/drone.py](/Users/ericwindsor/Downloads/Fly_In/src/drone.py:31)

它会设置：

```python
status = IN_TRANSIT
remaining_turns = duration
destination_index = pos + 1
```

如果目标 zone 是 normal/priority，`duration = 1`。

如果目标 zone 是 restricted，`duration = 2`。

每回合调用：

```python
drone.advance_transit()
```

位置：[src/drone.py](/Users/ericwindsor/Downloads/Fly_In/src/drone.py:41)

它会：

```python
remaining_turns -= 1
```

如果还没到，就继续 `IN_TRANSIT`。

如果到达了：

```python
pos = destination_index
status = ACTIVE
```

如果到达的是 end，`Scheduler` 会改成：

```python
DELIVERED
```

**移动顺序**

位置：[src/scheduler.py](/Users/ericwindsor/Downloads/Fly_In/src/scheduler.py:64)

```python
drones = sorted(self.drones, key=lambda drone: drone.pos, reverse=True)
```

这里很重要。

它让靠近终点的 drone 先移动。

例如路径：

```text
start -> A -> B -> goal
```

如果 D1 在 B，D2 在 A：

```text
D1 先从 B 去 goal
D2 再从 A 去 B
```

这样 B 被 D1 让出来后，D2 同一回合可以进入 B。

这符合 subject：

> Drones moving out of a zone free up capacity for that turn.

**每架 drone 移动前检查什么**

位置：[src/scheduler.py](/Users/ericwindsor/Downloads/Fly_In/src/scheduler.py:68)

每架 drone 依次检查：

1. 如果不是 `ACTIVE`，跳过。
2. 如果没有 `next_zone`，说明已经到路径末尾，标记 delivered。
3. 如果目标 zone 是 `blocked`，跳过。
4. 检查 connection capacity。
5. 检查 zone capacity。
6. 通过后，开始移动。

对应代码：

```python
if drone.status is not DroneStatus.ACTIVE:
    continue

destination = drone.next_zone

if destination is None:
    drone.status = DroneStatus.DELIVERED
    continue

if self.graph.get_zone(destination).zone_type == ZoneType.BLOCKED:
    continue
```

然后检查连接容量：

```python
link_capacity = self.graph.get_connection(
    (drone.current_zone, destination)
).max_link_capacity

link_load = self._link_load(drone.current_zone, destination)

if link_load >= link_capacity:
    continue
```

`_link_load()` 统计当前这条 connection 上有多少 drone 正在移动。

如果已经达到 `max_link_capacity`，这一回合不能再有 drone 走这条连接。

然后检查 zone 容量：

```python
if self._zone_load(destination) >= self.graph.zone_capacity(destination):
    continue
```

`_zone_load()` 统计：

1. 当前已经在这个 zone 的 active drone。
2. 已经在路上、目标是这个 zone 的 drone。

这样可以避免两个 drone 同时冲进同一个容量为 1 的 zone。

**为什么 end 可以无限进**

在 [src/scheduler.py](/Users/ericwindsor/Downloads/Fly_In/src/scheduler.py:105)：

```python
if zone_name == self.graph.end:
    return 0
```

end zone 不限制容量。到达 end 的 drone 会被标记 `DELIVERED`，不再占普通 zone 容量。

start/end 特殊容量也在 [src/graph.py](/Users/ericwindsor/Downloads/Fly_In/src/graph.py:39)：

```python
if zone_name in {self.start, self.end}:
    return self.nb_drones
```

**输出格式**

当一架 drone 成功开始移动后：

```python
moves.append(f"D{drone.id}-{destination}")
```

例如：

```text
D1-waypoint1
```

每回合的所有移动会组合成一行：

```python
" ".join(...)
```

所以输出类似：

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

这正好符合 subject 的格式。

**一句话总结**

寻路部分做的是：

```text
找多条低成本路径 -> 根据路径成本和瓶颈容量给 drones 分配路径
```

调度部分做的是：

```text
每回合先处理到达 -> 从靠近终点的 drone 开始尝试移动 -> 检查 blocked/link capacity/zone capacity -> 输出本回合移动
```

这个算法不是严格全局最优搜索，但结构清晰，能处理：

- 多 drone
- 多路径分配
- blocked zone
- restricted zone 多回合移动
- priority zone 优先寻路
- zone capacity
- connection capacity
- subject 要求的 turn-by-turn 输出

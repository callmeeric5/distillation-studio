*This activity has been created as part of the 42 curriculum by ziwang*

# Fly-in

## Description

Fly-in solves the problem of routing N drones from a start zone to an end zone through a network of interconnected zones, each with capacity constraints. The goal is to minimize the total number of simulation turns required for all drones to reach the destination.

The project parses a map file describing the network topology (zones, connections, capacities, special zone types), computes optimal routing paths using a modified Dijkstra algorithm, then runs a turn-based simulation where drones move through the network respecting all capacity constraints.

### Zone Types

- **Normal**: standard zone, 1 turn to traverse
- **Restricted**: slow zone, 2 turns to traverse (1 turn in transit on the connection, then arrival)
- **Priority**: preferred zone, 1 turn to traverse but weighted lower in pathfinding
- **Blocked**: impassable, drones cannot enter

### Constraints

- Each zone has a maximum drone capacity (default 1), except start and end zones (unlimited)
- Each connection has a maximum simultaneous usage capacity (default 1)
- Drones move simultaneously each turn, respecting all capacity limits

## Instructions
### Installation

```bash
make install
```

### Running

```bash
make run
make run MAP=maps/medium/01_dead_end_trap.txt
```

## Resources

- Python documentation: https://docs.python.org/3/
- Pydantic documentation: https://docs.pydantic.dev/
- Dijkstra algorithm overview: https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- AI usage: AI assistance was used to compare the implementation against the
  subject PDF, identify missing simulation requirements, and help draft tests
  and documentation. The parser, pathfinding, scheduling, and validation logic
  remain reviewable Python code in this repository.

## Algorithm

The solution is split into four object-oriented parts:

- `Parser` reads the map format, validates hubs, metadata, capacities, and
  connections, then returns a typed `Config`.
- `Graph` stores zones, bidirectional connections, adjacency lists, movement
  costs, and capacity helpers.
- `Solver` first uses Dijkstra-style weighted search for the best single path.
  For the full simulation it enumerates low-cost simple paths with a bounded
  priority queue, ignores blocked zones, gives priority zones a lower planning
  weight, and assigns drones to paths based on estimated finish time and path
  bottleneck capacity.
- `Scheduler` runs the discrete turn simulation. It moves drones from the end
  of their paths backward each turn so zones vacated by downstream drones can
  be reused immediately. It checks zone capacity, link capacity, blocked zones,
  delivered drones, and multi-turn movement into restricted zones.

The output follows the subject format: each printed line is one turn, and each
movement is printed as `D<ID>-<zone>`. Drones that wait are omitted from that
turn.

## Visual Representation

When output is connected to a terminal, movements are colored with ANSI escape
codes based on the destination zone color metadata. This keeps the required
text format intact for automated checks while still making the simulation easier
to follow during manual review.

## Benchmarks

Current example map results:

| Map | Turns |
| --- | ---: |
| `maps/easy/01_linear_path.txt` | 4 |
| `maps/easy/02_simple_fork.txt` | 5 |
| `maps/easy/03_basic_capacity.txt` | 6 |
| `maps/medium/01_dead_end_trap.txt` | 8 |
| `maps/medium/02_circular_loop.txt` | 20 |
| `maps/medium/03_priority_puzzle.txt` | 7 |
| `maps/hard/01_maze_nightmare.txt` | 14 |
| `maps/hard/02_capacity_hell.txt` | 18 |
| `maps/hard/03_ultimate_challenge.txt` | 29 |
| `maps/challenger/01_the_impossible_dream.txt` | 52 |

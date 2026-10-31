*This activity has been created as part of the 42 curriculum by ziwang, lcoant--.*

# TAP - The Answer Protocol

## Description

TAP is a small shared-world text adventure written in Rust. A TCP server owns the game state, while a command-line client and a graphical `egui` client let several players explore, chat, form groups, move unique items, fight an enemy, and complete quests in real time.

The implementation intentionally favors ordinary Rust types and short functions over framework-heavy abstractions. 

## Features

- Line-based UTF-8 TCP protocol with asynchronous events
- Nine-room map with loops and an optional cave branch
- Unique movable items, four NPC roles, two quests, and deterministic combat
- Global, room, and group chat
- CLI and native GUI clients
- Structured JSON server logs and basic abuse monitoring

## Architecture

The server uses one reader thread and one writer thread per TCP connection. The complete game state is stored in `Arc<Mutex<GameState>>`. A command locks that state only while it validates and changes data. It produces a response and a list of event deliveries, then releases the lock before sending network messages. This keeps a slow or disconnected client from blocking the world.

The command dispatcher is a normal Rust `match` over the `Command` enum. The CLI and GUI share the small connection helper in `src/client.rs`. That helper uses one background reader, one background writer, and standard `mpsc` channels, so both interfaces remain responsive while events arrive.

## Protocol Implementation

The server follows RFC 42TAP: TCP, UTF-8, LF framing, the greeting `OK hello proto=1`, case-insensitive command names, RFC success formats, and ROOM/GLOBAL/GROUP/STATS events. LOOK and the state-oriented commands use compact single-line JSON. WHO returns exactly `OK players=<count>`. Lines are limited to 1024 bytes, incomplete TCP packets are buffered, and coalesced commands are processed independently.

The RFC leaves several failure cases undefined. This implementation uses `ERR 400 <reason>` for malformed input and invalid connection/combat state. It also adds these descriptive group errors: `403 NOT_GROUP_LEADER`, `403 NOT_INVITED`, `404 PLAYER_NOT_FOUND`, and `404 GROUP_NOT_FOUND`.

Two documented protocol extensions support the required turn-based combat design:

- `DEFEND` - spend a turn and receive half of the enemy's normal counter damage.
- `FLEE` - end combat and return to the safe starting room.

The CLI sends TAP syntax directly instead of translating a second command language.

## Combat System

Players begin with 100 HP. `ATTACK <npc>` is one complete round: the player always acts first for 10 damage, then a surviving enemy counter-attacks using the damage value in the world file. This fixed initiative and deterministic formula make the behavior easy to understand.

`DEFEND` consumes a round and rounds half damage upward. `FLEE` always succeeds. A player reduced to zero HP respawns in Village Square with 50 HP. Defeated enemies remain defeated until the server restarts. Combat responses contain JSON state and combat activity is logged and broadcast to the room.

## Quest System

`QUEST <npc>` first accepts that NPC's quest. `QUESTS` lists progress. After meeting the objective, the player returns to the giver and uses `QUEST` again to validate completion and receive the reward. The herb quest checks that the unique herb is in the player's inventory and consumes it. The goblin quest records which player delivered the defeating blow. Reward items begin outside the map and become unique inventory items when awarded.

## World Design

The world contains Village Square, Warm Bakery, Old Bridge, Forest Path, Ancient Ruins, Guard Post, Herb Garden, Lakeside, and Goblin Cave. The first eight form several circuits; Goblin Cave is the optional branch. The healer is a fetch-quest giver, the guard is a combat-quest giver, the baker is a dialogue NPC, and the goblin is an enemy. Six item definitions cover four in-world items and two quest rewards.

World data lives in `data/world.json`. Startup validation checks room count, reachability, all exits and references, positive NPC health, quest targets and rewards, and duplicate item placement.

## Server Logging

Every log entry is one JSON object with an RFC 3339 timestamp, level, event name, and fields. INFO and WARN records go to stdout; ERROR records go to stderr. The server records connections, disconnects, commands, responses, send failures, and successful world-changing commands. It warns after more than 20 commands per second on one connection or more than 10 connections from one IP in five seconds. Logging uses a small mutex so lines from different threads do not interleave.

## Instructions

Install the current stable Rust toolchain. On Linux, the GUI may also require the normal X11/Wayland development packages used by `eframe`.

```sh
make install
make build
```

No database or external service is needed.

## Building and Running

Start the server, then open one or more clients in other terminals:

```sh
make run-server
make run-client
make run-client-gui
```

Equivalent direct commands are:

```sh
cargo run --bin server -- data/world.json 127.0.0.1:4242
cargo run --bin cli -- 127.0.0.1:4242
cargo run --bin gui
```

The server arguments are `[world-file] [address]`; the CLI argument is `[address]`. Both default to the values above. Useful CLI commands include `LOOK`, `MOVE east`, `TAKE Healing Herbs`, `CHAT ROOM hello`, `GROUP CREATE`, `ATTACK Cave Goblin`, `QUEST Village Healer`, and `QUIT`.

Other Make targets are `lint` and `clean`.

## Manual Verification

Check formatting and common Rust mistakes with:

```sh
make lint
```

For a manual multiplayer check, start the server and two clients. Move both players into the same room, try ROOM chat and presence events, create/invite/join a group, and race for an item. Use the GUI to check that the room, inventory, counters, chat, and protocol log update independently. The two complete quest routes are:

1. At Herb Garden, accept the healer's quest, take the herbs, then use QUEST on the healer again.
2. At Guard Post, accept the guard's quest, travel north/east/south into the cave, defeat the goblin, return to the guard, and use QUEST again.

## Group Contributions

- `ziwang`: server, protocol parser, CLI client, combat and quest systems.
- `lcoant--`: GUI client, world design, and documentation.

The curriculum requires two or three distinct learners. The duplicate login above is retained exactly as requested and should be corrected before formal submission if it does not represent two valid contributors.

## Resources

- The supplied RFC 42TAP document, `protocol-rfc.html`
- [The Rust Book](https://doc.rust-lang.org/book/)
- [Rust standard library networking](https://doc.rust-lang.org/std/net/)
- [Rust shared-state concurrency](https://doc.rust-lang.org/book/ch16-03-shared-state.html)
- [egui documentation](https://docs.rs/egui/)
- [Serde documentation](https://serde.rs/)

AI was used to help interpret the supplied requirements, propose the simple thread-and-channel architecture, and draft initial Rust code and documentation. The generated work was compiled, linted, and reviewed against the RFC; project members remain responsible for understanding and validating it.

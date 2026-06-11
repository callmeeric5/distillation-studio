import { useCallback, useEffect, useRef, useState } from 'react';

import {
  fetchPacmanConfig,
  fetchPacmanLevel,
  fetchPacmanScores,
  submitPacmanScore,
  type PacmanCell,
  type PacmanConfig,
  type PacmanLevel,
  type PacmanScore,
} from './api/pacman';
import { CollapsibleDescription } from './components/CollapsibleDescription';

type Direction = 'up' | 'down' | 'left' | 'right';
type GameStatus = 'idle' | 'loading' | 'playing' | 'paused' | 'advancing' | 'won' | 'lost' | 'error';
type GhostMode = 'chase' | 'frighten' | 'eaten';

type Entity = {
  row: number;
  col: number;
  direction: Direction;
  pos: { row: number; col: number };
  target: { row: number; col: number } | null;
};

type Ghost = Entity & {
  color: string;
  home: { row: number; col: number };
  mode: GhostMode;
};

type Collectible = {
  points: number;
  row: number;
  col: number;
};

type Game = {
  cheatMode: boolean;
  cheatUsed: boolean;
  elapsedSeconds: number;
  frightenedUntil: number;
  ghosts: Ghost[];
  level: PacmanLevel;
  levelCount: number;
  levelIndex: number;
  lives: number;
  pacgums: Map<string, Collectible>;
  player: Entity;
  playerName: string;
  requestedDirection: Direction;
  score: number;
  status: GameStatus;
  superPacgums: Map<string, Collectible>;
  timeLeft: number;
  totalElapsedSeconds: number;
};

type Snapshot = {
  cheatMode: boolean;
  cheatUsed: boolean;
  completed: boolean;
  elapsedSeconds: number;
  level: number;
  levelCount: number;
  lives: number;
  playerName: string;
  score: number;
  status: GameStatus;
  statusText: string;
  timeLeft: number;
};

const WALL_NORTH = 1;
const WALL_EAST = 2;
const WALL_SOUTH = 4;
const WALL_WEST = 8;
const ghostColors = ['#d95f4f', '#6da6b6', '#d38a4a', '#b47ab0'];

const directions: Record<Direction, { row: number; col: number; wall: number; opposite: number }> = {
  down: { row: 1, col: 0, wall: WALL_SOUTH, opposite: WALL_NORTH },
  left: { row: 0, col: -1, wall: WALL_WEST, opposite: WALL_EAST },
  right: { row: 0, col: 1, wall: WALL_EAST, opposite: WALL_WEST },
  up: { row: -1, col: 0, wall: WALL_NORTH, opposite: WALL_SOUTH },
};
const preferredDirections: Direction[] = ['up', 'down', 'left', 'right'];
const frightenedDuration = 10;

const emptySnapshot: Snapshot = {
  cheatMode: false,
  cheatUsed: false,
  completed: false,
  elapsedSeconds: 0,
  level: 1,
  levelCount: 10,
  lives: 3,
  playerName: '',
  score: 0,
  status: 'idle',
  statusText: 'Enter your name to start.',
  timeLeft: 90,
};

function keyOf(row: number, col: number) {
  return `${row}:${col}`;
}

function mapCollectibles(items: Collectible[]) {
  return new Map(items.map((item) => [keyOf(item.row, item.col), item]));
}

function availableDirections(level: PacmanLevel, pos: { row: number; col: number }) {
  return preferredDirections.filter((direction) => canMove(level, pos, direction));
}

function initialDirection(level: PacmanLevel, pos: { row: number; col: number }) {
  return availableDirections(level, pos)[0] ?? 'right';
}

function createGame({
  config,
  level,
  playerName,
  previous,
  cheatMode,
}: {
  cheatMode: boolean;
  config: PacmanConfig;
  level: PacmanLevel;
  playerName: string;
  previous?: Game;
}): Game {
  const playerPos = { row: level.player.row, col: level.player.col };
  const playerDirection = initialDirection(level, playerPos);
  return {
    cheatMode,
    cheatUsed: previous?.cheatUsed || cheatMode,
    elapsedSeconds: 0,
    frightenedUntil: 0,
    ghosts: level.ghosts.map((ghost, index) => ({
      col: ghost.col,
      color: ghostColors[index % ghostColors.length],
      direction: initialDirection(level, { row: ghost.row, col: ghost.col }),
      home: { row: ghost.home_row, col: ghost.home_col },
      mode: ghost.state === 'frighten' || ghost.state === 'eaten' ? ghost.state : 'chase',
      pos: { row: ghost.row, col: ghost.col },
      row: ghost.row,
      target: null,
    })),
    level,
    levelCount: config.levels.length,
    levelIndex: level.level_index,
    lives: previous?.lives ?? config.lives,
    pacgums: mapCollectibles(level.pacgums),
    player: {
      col: level.player.col,
      direction: playerDirection,
      pos: playerPos,
      row: level.player.row,
      target: null,
    },
    playerName,
    requestedDirection: playerDirection,
    score: previous?.score ?? 0,
    status: 'playing',
    superPacgums: mapCollectibles(level.super_pacgums),
    timeLeft: level.time_limit,
    totalElapsedSeconds: previous?.totalElapsedSeconds ?? 0,
  };
}

function snapshotGame(game: Game | null, fallback = emptySnapshot): Snapshot {
  if (!game) return fallback;
  const statusText =
    game.status === 'won'
      ? 'Run complete'
      : game.status === 'lost'
        ? 'Game over'
        : game.status === 'paused'
          ? 'Paused'
          : game.status === 'advancing'
            ? 'Loading next level'
            : 'Playing';
  return {
    completed: game.status === 'won',
    cheatMode: game.cheatMode,
    cheatUsed: game.cheatUsed,
    elapsedSeconds: Math.round(game.totalElapsedSeconds),
    level: game.levelIndex + 1,
    levelCount: game.levelCount,
    lives: game.lives,
    playerName: game.playerName,
    score: game.score,
    status: game.status,
    statusText,
    timeLeft: Math.ceil(game.timeLeft),
  };
}

function canMove(level: PacmanLevel, pos: { row: number; col: number }, direction: Direction) {
  if (pos.row < 0 || pos.row >= level.height || pos.col < 0 || pos.col >= level.width) return false;
  const movement = directions[direction];
  const nextRow = pos.row + movement.row;
  const nextCol = pos.col + movement.col;
  if (nextRow < 0 || nextRow >= level.height || nextCol < 0 || nextCol >= level.width) return false;
  const cell = level.cells[pos.row][pos.col];
  const nextCell = level.cells[nextRow][nextCol];
  return !cell.is_42_pattern && !nextCell.is_42_pattern && (cell.walls & movement.wall) === 0;
}

function nextPosition(entity: Entity, direction: Direction) {
  const movement = directions[direction];
  return {
    col: entity.pos.col + movement.col,
    row: entity.pos.row + movement.row,
  };
}

function assignTarget(entity: Entity, level: PacmanLevel, direction: Direction) {
  if (!canMove(level, entity.pos, direction)) return false;
  entity.direction = direction;
  entity.target = nextPosition(entity, direction);
  return true;
}

function moveEntityToTarget(entity: Entity, distance: number) {
  if (!entity.target) return 0;
  const rowDistance = entity.target.row - entity.row;
  const colDistance = entity.target.col - entity.col;
  const targetDistance = Math.abs(rowDistance) + Math.abs(colDistance);

  if (targetDistance <= distance) {
    const leftover = distance - targetDistance;
    entity.pos = entity.target;
    entity.row = entity.target.row;
    entity.col = entity.target.col;
    entity.target = null;
    return leftover;
  }

  const ratio = distance / targetDistance;
  entity.row += rowDistance * ratio;
  entity.col += colDistance * ratio;
  return 0;
}

function chooseGhostDirection(game: Game, ghost: Ghost) {
  const available = (Object.keys(directions) as Direction[]).filter((direction) => canMove(game.level, ghost.pos, direction));
  const opposite = directionFromWall(directions[ghost.direction].opposite);
  const options = available.length <= 1 ? available : available.filter((direction) => direction !== opposite);
  if (options.length === 0) return ghost.direction;
  const target =
    ghost.mode === 'eaten'
      ? ghost.home
      : ghost.mode === 'frighten'
        ? game.player.pos
        : game.player.pos;
  return options
    .map((direction) => ({
      direction,
      distance: distanceAfterMove(ghost, direction, target),
      order: direction === ghost.direction ? -1 : preferredDirections.indexOf(direction),
    }))
    .sort((first, second) => {
      const distanceDelta =
        ghost.mode === 'frighten' ? second.distance - first.distance : first.distance - second.distance;
      return distanceDelta || first.order - second.order;
    })[0].direction;
}

function distanceAfterMove(entity: Entity, direction: Direction, target: { row: number; col: number }) {
  const nextPos = nextPosition(entity, direction);
  return Math.abs(nextPos.row - target.row) + Math.abs(nextPos.col - target.col);
}

function directionFromWall(wall: number) {
  return (Object.keys(directions) as Direction[]).find((direction) => directions[direction].wall === wall) ?? 'right';
}

function samePosition(first: { row: number; col: number }, second: { row: number; col: number }) {
  return first.row === second.row && first.col === second.col;
}

function resetGhostAtHome(ghost: Ghost) {
  ghost.mode = 'chase';
  ghost.direction = 'right';
  ghost.pos = { ...ghost.home };
  ghost.row = ghost.home.row;
  ghost.col = ghost.home.col;
  ghost.target = null;
}

function resetPositions(game: Game) {
  const playerPos = { row: game.level.player.row, col: game.level.player.col };
  const playerDirection = initialDirection(game.level, playerPos);
  game.player = {
    col: game.level.player.col,
    direction: playerDirection,
    pos: playerPos,
    row: game.level.player.row,
    target: null,
  };
  game.requestedDirection = playerDirection;
  game.ghosts = game.level.ghosts.map((ghost, index) => ({
    col: ghost.col,
    color: ghostColors[index % ghostColors.length],
    direction: initialDirection(game.level, { row: ghost.row, col: ghost.col }),
    home: { row: ghost.home_row, col: ghost.home_col },
    mode: 'chase',
    pos: { row: ghost.row, col: ghost.col },
    row: ghost.row,
    target: null,
  }));
  game.frightenedUntil = 0;
}

function updateGame(game: Game, deltaSeconds: number) {
  if (game.status !== 'playing') return;
  const playerSpeed = 4;
  const ghostSpeed = game.levelIndex < 5 ? 3 : 3.4;

  game.elapsedSeconds += deltaSeconds;
  game.totalElapsedSeconds += deltaSeconds;
  if (!game.cheatMode) {
    game.timeLeft = Math.max(0, game.timeLeft - deltaSeconds);
  }
  if (!game.cheatMode && game.timeLeft <= 0) {
    game.status = 'lost';
    return;
  }

  let playerDistance = playerSpeed * deltaSeconds;
  while (playerDistance > 0) {
    if (!game.player.target) {
      if (canMove(game.level, game.player.pos, game.requestedDirection)) {
        game.player.direction = game.requestedDirection;
      }
      if (!assignTarget(game.player, game.level, game.player.direction)) break;
    }
    playerDistance = moveEntityToTarget(game.player, playerDistance);
  }

  for (const ghost of game.ghosts) {
    if (ghost.mode === 'frighten' && game.elapsedSeconds > game.frightenedUntil) {
      ghost.mode = 'chase';
      ghost.target = null;
    }
    let ghostDistance = (ghost.mode === 'eaten' ? ghostSpeed * 1.45 : ghostSpeed) * deltaSeconds;
    while (ghostDistance > 0) {
      if (!ghost.target) {
        if (ghost.mode === 'eaten' && samePosition(ghost.pos, ghost.home)) {
          resetGhostAtHome(ghost);
          break;
        }
        const direction = chooseGhostDirection(game, ghost);
        if (!assignTarget(ghost, game.level, direction)) break;
      }
      ghostDistance = moveEntityToTarget(ghost, ghostDistance);
      if (ghost.mode === 'eaten' && samePosition(ghost.pos, ghost.home)) {
        resetGhostAtHome(ghost);
        break;
      }
    }
  }

  const playerKey = keyOf(game.player.pos.row, game.player.pos.col);
  const pacgum = game.pacgums.get(playerKey);
  if (pacgum) {
    game.score += pacgum.points;
    game.pacgums.delete(playerKey);
  }
  const superPacgum = game.superPacgums.get(playerKey);
  if (superPacgum) {
    game.score += superPacgum.points;
    game.superPacgums.delete(playerKey);
    game.frightenedUntil = game.elapsedSeconds + frightenedDuration;
    for (const ghost of game.ghosts) {
      if (ghost.mode !== 'eaten') {
        ghost.mode = 'frighten';
        ghost.target = null;
      }
    }
  }

  for (const ghost of game.ghosts) {
    if (!samePosition(game.player.pos, ghost.pos)) continue;
    if (ghost.mode === 'frighten') {
      ghost.mode = 'eaten';
      ghost.target = null;
      game.score += game.level.points.ghost;
      continue;
    }
    if (ghost.mode !== 'chase') continue;
    if (game.cheatMode) continue;
    game.lives -= 1;
    if (game.lives <= 0) {
      game.status = 'lost';
      return;
    }
    resetPositions(game);
    return;
  }

  if (game.pacgums.size === 0 && game.superPacgums.size === 0) {
    game.status = game.levelIndex >= game.levelCount - 1 ? 'won' : 'advancing';
  }
}

function drawGame(canvas: HTMLCanvasElement, game: Game | null) {
  const context = canvas.getContext('2d');
  if (!context) return;
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(360, Math.floor(rect.width || 960));
  const height = Math.max(360, Math.floor(rect.height || width * 0.625));
  const ratio = window.devicePixelRatio || 1;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);

  const isDark =
    document.documentElement.classList.contains('theme-dark') ||
    document.documentElement.dataset.theme === 'dark';
  context.fillStyle = isDark ? '#171715' : '#fffdf8';
  context.fillRect(0, 0, width, height);

  if (!game) {
    context.fillStyle = isDark ? '#b8afa3' : '#8b8174';
    context.font = '600 20px Inter, sans-serif';
    context.textAlign = 'center';
    context.fillText('Enter your name to start Pac_Man', width / 2, height / 2);
    return;
  }

  const padding = 22;
  const boardSize = Math.min(width - padding * 2, height - padding * 2);
  const cellSize = boardSize / Math.max(game.level.width, game.level.height);
  const offsetX = (width - game.level.width * cellSize) / 2;
  const offsetY = (height - game.level.height * cellSize) / 2;

  context.lineWidth = Math.max(2, cellSize * 0.12);
  context.strokeStyle = isDark ? '#7a9f91' : '#668f80';
  context.lineCap = 'round';
  for (const row of game.level.cells) {
    for (const cell of row) {
      drawCell(context, cell, offsetX, offsetY, cellSize, isDark);
    }
  }

  for (const pellet of game.pacgums.values()) {
    drawCircle(context, offsetX + (pellet.col + 0.5) * cellSize, offsetY + (pellet.row + 0.5) * cellSize, cellSize * 0.1, '#d4b16a');
  }
  for (const pellet of game.superPacgums.values()) {
    drawCircle(context, offsetX + (pellet.col + 0.5) * cellSize, offsetY + (pellet.row + 0.5) * cellSize, cellSize * 0.23, '#d96d4a');
  }

  drawPacman(context, offsetX + (game.player.col + 0.5) * cellSize, offsetY + (game.player.row + 0.5) * cellSize, cellSize * 0.35, game.player.direction);
  for (const ghost of game.ghosts) {
    const color = ghost.mode === 'frighten' ? '#7da9c5' : ghost.mode === 'eaten' ? '#9b9488' : ghost.color;
    drawGhost(context, offsetX + (ghost.col + 0.5) * cellSize, offsetY + (ghost.row + 0.5) * cellSize, cellSize * 0.35, color);
  }
}

function drawCell(
  context: CanvasRenderingContext2D,
  cell: PacmanCell,
  offsetX: number,
  offsetY: number,
  cellSize: number,
  isDark: boolean,
) {
  const x = offsetX + cell.col * cellSize;
  const y = offsetY + cell.row * cellSize;
  if (cell.is_42_pattern) {
    context.fillStyle = isDark ? '#3b2b25' : '#f3dfd2';
    context.fillRect(x + 2, y + 2, cellSize - 4, cellSize - 4);
  }
  context.beginPath();
  if (cell.walls & WALL_NORTH) {
    context.moveTo(x, y);
    context.lineTo(x + cellSize, y);
  }
  if (cell.walls & WALL_EAST) {
    context.moveTo(x + cellSize, y);
    context.lineTo(x + cellSize, y + cellSize);
  }
  if (cell.walls & WALL_SOUTH) {
    context.moveTo(x, y + cellSize);
    context.lineTo(x + cellSize, y + cellSize);
  }
  if (cell.walls & WALL_WEST) {
    context.moveTo(x, y);
    context.lineTo(x, y + cellSize);
  }
  context.stroke();
}

function drawCircle(context: CanvasRenderingContext2D, x: number, y: number, radius: number, color: string) {
  context.beginPath();
  context.fillStyle = color;
  context.arc(x, y, radius, 0, Math.PI * 2);
  context.fill();
}

function drawPacman(context: CanvasRenderingContext2D, x: number, y: number, radius: number, direction: Direction) {
  const rotation = { down: Math.PI / 2, left: Math.PI, right: 0, up: -Math.PI / 2 }[direction];
  context.beginPath();
  context.fillStyle = '#e0b73e';
  context.moveTo(x, y);
  context.arc(x, y, radius, rotation + 0.35, rotation + Math.PI * 2 - 0.35);
  context.closePath();
  context.fill();
}

function drawGhost(context: CanvasRenderingContext2D, x: number, y: number, radius: number, color: string) {
  context.fillStyle = color;
  context.beginPath();
  context.arc(x, y - radius * 0.15, radius, Math.PI, 0);
  context.lineTo(x + radius, y + radius * 0.85);
  context.lineTo(x + radius * 0.35, y + radius * 0.55);
  context.lineTo(x, y + radius * 0.85);
  context.lineTo(x - radius * 0.35, y + radius * 0.55);
  context.lineTo(x - radius, y + radius * 0.85);
  context.closePath();
  context.fill();
  drawCircle(context, x - radius * 0.35, y - radius * 0.15, radius * 0.13, '#fffdf8');
  drawCircle(context, x + radius * 0.35, y - radius * 0.15, radius * 0.13, '#fffdf8');
}

export function PacManStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const gameRef = useRef<Game | null>(null);
  const configRef = useRef<PacmanConfig | null>(null);
  const frameRef = useRef<number | null>(null);
  const lastTickRef = useRef<number | null>(null);
  const loadingNextLevelRef = useRef(false);
  const [snapshot, setSnapshot] = useState(emptySnapshot);
  const [scores, setScores] = useState<PacmanScore[]>([]);
  const [playerName, setPlayerName] = useState('');
  const [cheatMode, setCheatMode] = useState(false);
  const [message, setMessage] = useState('Enter your name before starting.');

  const refreshScores = useCallback(async () => {
    try {
      setScores(await fetchPacmanScores(10));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not load leaderboard.');
    }
  }, []);

  const loadLevel = useCallback(async (levelIndex: number, player: string, previous?: Game, nextCheatMode = cheatMode) => {
    loadingNextLevelRef.current = true;
    setMessage(levelIndex === 0 ? 'Loading game...' : 'Loading next level...');
    try {
      const config = configRef.current ?? (await fetchPacmanConfig());
      configRef.current = config;
      const level = await fetchPacmanLevel(levelIndex);
      const game = createGame({ cheatMode: nextCheatMode, config, level, playerName: player, previous });
      gameRef.current = game;
      setSnapshot(snapshotGame(game));
      setMessage('Use Arrow keys or WASD.');
    } catch (error) {
      gameRef.current = null;
      setSnapshot({ ...emptySnapshot, status: 'error', statusText: 'Could not start game' });
      setMessage(error instanceof Error ? error.message : 'Could not load Pac-Man.');
    } finally {
      loadingNextLevelRef.current = false;
    }
  }, [cheatMode]);

  const startRun = useCallback(() => {
    const cleanName = playerName.trim();
    if (!cleanName) {
      setMessage('Enter your name before starting.');
      return;
    }
    void loadLevel(0, cleanName);
  }, [loadLevel, playerName]);

  const restart = useCallback(() => {
    const activeName = gameRef.current?.playerName ?? playerName.trim();
    if (!activeName) {
      setMessage('Enter your name before restarting.');
      return;
    }
    void loadLevel(0, activeName);
  }, [loadLevel, playerName]);

  const togglePause = useCallback(() => {
    const game = gameRef.current;
    if (!game || game.status === 'won' || game.status === 'lost') return;
    game.status = game.status === 'paused' ? 'playing' : 'paused';
    setSnapshot(snapshotGame(game));
  }, []);

  const submitFinalScore = useCallback(async () => {
    const game = gameRef.current;
    if (!game || (game.status !== 'won' && game.status !== 'lost')) return;
    if (game.cheatUsed) {
      setMessage('Cheat runs are not saved to the leaderboard.');
      return;
    }
    try {
      await submitPacmanScore({
        completed: game.status === 'won',
        elapsed_seconds: Math.round(game.totalElapsedSeconds),
        level_reached: game.levelIndex + 1,
        player_name: game.playerName,
        score: game.score,
      });
      setMessage('Score saved.');
      await refreshScores();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not submit score.');
    }
  }, [refreshScores]);

  const toggleCheatMode = useCallback(() => {
    setCheatMode((current) => {
      const next = !current;
      const game = gameRef.current;
      if (game && game.status !== 'won' && game.status !== 'lost') {
        game.cheatMode = next;
        game.cheatUsed = game.cheatUsed || next;
        setSnapshot(snapshotGame(game));
      }
      setMessage(next ? 'Cheat mode enabled: no timer or life loss.' : 'Cheat mode disabled.');
      return next;
    });
  }, []);

  const setDirection = useCallback((direction: Direction) => {
    const game = gameRef.current;
    if (!game) return;
    game.requestedDirection = direction;
    if (game.status === 'paused') game.status = 'playing';
  }, []);

  useEffect(() => {
    let isActive = true;
    const loadScores = async () => {
      try {
        const loadedScores = await fetchPacmanScores(10);
        if (isActive) setScores(loadedScores);
      } catch (error) {
        if (isActive) setMessage(error instanceof Error ? error.message : 'Could not load leaderboard.');
      }
    };
    void loadScores();
    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target;
      const isEditableTarget =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement ||
        (target instanceof HTMLElement && target.isContentEditable);
      const keyMap: Record<string, Direction | undefined> = {
        ArrowDown: 'down',
        ArrowLeft: 'left',
        ArrowRight: 'right',
        ArrowUp: 'up',
        KeyA: 'left',
        KeyD: 'right',
        KeyS: 'down',
        KeyW: 'up',
      };
      const direction = keyMap[event.code];
      if (isEditableTarget) return;
      if (!direction) {
        if (event.code === 'Space') togglePause();
        return;
      }
      event.preventDefault();
      setDirection(direction);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setDirection, togglePause]);

  useEffect(() => {
    const tick = (timestamp: number) => {
      const game = gameRef.current;
      const lastTick = lastTickRef.current ?? timestamp;
      lastTickRef.current = timestamp;
      const deltaSeconds = Math.min(0.05, (timestamp - lastTick) / 1000);

      if (game) {
        updateGame(game, deltaSeconds);
        if (game.status === 'advancing' && !loadingNextLevelRef.current) {
          void loadLevel(game.levelIndex + 1, game.playerName, game, game.cheatMode);
        }
        setSnapshot(snapshotGame(gameRef.current));
      }
      if (canvasRef.current) drawGame(canvasRef.current, gameRef.current);
      frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    };
  }, [loadLevel]);

  const runEnded = snapshot.status === 'won' || snapshot.status === 'lost';
  const canStart = playerName.trim().length > 0 && snapshot.status !== 'loading';

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <div className="border-b border-[#ece8dc] p-5 lg:p-7">
        <button
          className="rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#5e5d59] transition hover:bg-white"
          onClick={onBack}
          type="button"
        >
          Back to gallery
        </button>
        <div className="mt-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-[#c96442]">Playable browser game</p>
            <h2 className="mt-2 font-serif text-5xl leading-none text-[#171715] sm:text-6xl">Pac_Man</h2>
          </div>
          <div className="rounded-full border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#5e5d59]">
            Level {snapshot.level} / {snapshot.levelCount}
          </div>
        </div>
        <CollapsibleDescription
          className="mt-5"
          fullText={fullDescription ?? description}
          previewText={description}
        />
      </div>

      <div className="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_340px] lg:p-7">
        <section className="relative mx-auto aspect-square w-full max-w-[620px] overflow-hidden rounded-2xl border border-[#d8d1c2] bg-[#fffdf8] shadow-sm">
          <canvas
            aria-label="Pac-Man playable maze"
            className="block h-full w-full bg-[#fffdf8]"
            ref={canvasRef}
          />

          {snapshot.status === 'idle' || snapshot.status === 'error' ? (
            <div className="absolute inset-0 flex items-center justify-center bg-[#171715]/60 p-5 backdrop-blur-sm">
              <div className="w-full max-w-md rounded-2xl border border-[#e8e3d6] bg-[#fffdf8] p-5 shadow-xl">
                <p className="text-sm font-semibold text-[#c96442]">New run</p>
                <h3 className="mt-2 font-serif text-4xl text-[#171715]">Enter your name</h3>
                <p className="mt-3 text-sm leading-6 text-[#5e5d59]">
                  Your name is required before the game starts and will be used for the leaderboard.
                </p>
                <div className="mt-5 flex gap-2">
                  <input
                    className="min-h-11 min-w-0 flex-1 rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-3 text-sm text-[#30302e] outline-none transition focus:border-[#c96442]"
                    maxLength={32}
                    onChange={(event) => setPlayerName(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') startRun();
                    }}
                    placeholder="Your name"
                    value={playerName}
                  />
                  <button
                    className="min-h-11 rounded-lg bg-[#c96442] px-5 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334] disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={!canStart}
                    onClick={startRun}
                    type="button"
                  >
                    Start
                  </button>
                </div>
                <p className="mt-3 text-xs font-semibold text-[#8b8174]">{message}</p>
              </div>
            </div>
          ) : null}

          {runEnded ? (
            <div className="absolute inset-0 flex items-center justify-center bg-[#171715]/60 p-5 backdrop-blur-sm">
              <div className="w-full max-w-lg rounded-2xl border border-[#e8e3d6] bg-[#fffdf8] p-5 shadow-xl">
                <p className="text-sm font-semibold text-[#c96442]">{snapshot.statusText}</p>
                <h3 className="mt-2 font-serif text-4xl text-[#171715]">
                  {snapshot.score.toLocaleString()} points
                </h3>
                <p className="mt-3 text-sm leading-6 text-[#5e5d59]">
                  Level {snapshot.level} reached in {snapshot.elapsedSeconds}s.
                </p>
                {snapshot.cheatUsed ? (
                  <p className="mt-2 text-sm font-semibold text-[#8a4429]">
                    Cheat runs are not saved to the leaderboard.
                  </p>
                ) : null}
                <div className="mt-5 flex flex-wrap gap-2">
                  <button
                    className="min-h-11 rounded-lg bg-[#30302e] px-5 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#171715] disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={snapshot.cheatUsed}
                    onClick={submitFinalScore}
                    type="button"
                  >
                    Save score
                  </button>
                  <button
                    className="min-h-11 rounded-lg bg-[#c96442] px-5 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334]"
                    onClick={restart}
                    type="button"
                  >
                    Restart
                  </button>
                </div>
                <p className="mt-3 text-xs font-semibold text-[#8b8174]">{message}</p>
              </div>
            </div>
          ) : null}
        </section>

        <aside className="grid content-start gap-4">
          <div className="rounded-2xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-[#c96442]">Run status</p>
              <span className="rounded-full bg-[#30302e] px-3 py-1 text-xs font-bold uppercase tracking-wide text-[#faf9f5]">
                {snapshot.statusText}
              </span>
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Player" value={snapshot.playerName || 'Waiting'} />
              <Metric label="Level" value={`${snapshot.level}/${snapshot.levelCount}`} />
              <Metric label="Score" value={snapshot.score.toLocaleString()} />
              <Metric label="Lives" value={snapshot.lives.toString()} />
              <Metric label="Time" value={snapshot.cheatMode ? '∞' : `${snapshot.timeLeft}s`} />
              <Metric label="Elapsed" value={`${snapshot.elapsedSeconds}s`} />
            </dl>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                className="min-h-10 rounded-lg bg-[#c96442] px-4 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334]"
                onClick={restart}
                type="button"
              >
                Restart
              </button>
              <button
                className="min-h-10 rounded-lg border border-[#d8e3ce] bg-[#7f9f6f] px-4 text-sm font-semibold text-[#fffdf8] transition hover:bg-[#6f8f5f] disabled:cursor-not-allowed disabled:opacity-50"
                disabled={snapshot.status === 'idle' || snapshot.status === 'error' || runEnded}
                onClick={togglePause}
                type="button"
              >
                {snapshot.status === 'paused' ? 'Resume' : 'Pause'}
              </button>
              <button
                aria-pressed={cheatMode}
                className={`min-h-10 rounded-lg border px-4 text-sm font-semibold transition ${
                  cheatMode
                    ? 'border-[#c96442] bg-[#c96442] text-[#faf9f5] hover:bg-[#b65334]'
                    : 'border-[#e8e3d6] bg-[#fffdf8] text-[#5e5d59] hover:bg-white'
                }`}
                onClick={toggleCheatMode}
                type="button"
              >
                Cheat mode
              </button>
            </div>
            <p className="mt-3 text-xs font-semibold text-[#8b8174]">{message}</p>
          </div>

          <div className="rounded-2xl border border-[#e8e3d6] bg-[#fffdf8] p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-[#171715]">Leaderboard</p>
              <button
                className="text-xs font-bold text-[#8a4429] underline-offset-4 hover:underline"
                onClick={() => void refreshScores()}
                type="button"
              >
                Refresh
              </button>
            </div>
            <ol className="mt-3 grid gap-2">
              {scores.slice(0, 10).map((score, index) => (
                <li
                  className="grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-3 py-2 text-sm"
                  key={score.id}
                >
                  <span className="font-semibold text-[#8b8174]">{index + 1}</span>
                  <span className="min-w-0 truncate font-semibold text-[#171715]">{score.player_name}</span>
                  <span className="font-mono text-[#8a4429]">{score.score}</span>
                </li>
              ))}
              {scores.length === 0 ? (
                <li className="rounded-lg border border-dashed border-[#d8d1c2] bg-[#f4f1e8] p-3 text-sm text-[#5e5d59]">
                  No scores yet.
                </li>
              ) : null}
            </ol>
          </div>
        </aside>
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[#e8e3d6] bg-[#fffdf8] p-3">
      <dt className="text-[11px] font-bold uppercase text-[#8b8174]">{label}</dt>
      <dd className="mt-1 truncate font-mono text-sm font-semibold text-[#171715]">{value}</dd>
    </div>
  );
}

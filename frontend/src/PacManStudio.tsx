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

const emptySnapshot: Snapshot = {
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

function createGame({
  config,
  level,
  playerName,
  previous,
}: {
  config: PacmanConfig;
  level: PacmanLevel;
  playerName: string;
  previous?: Game;
}): Game {
  return {
    elapsedSeconds: 0,
    frightenedUntil: 0,
    ghosts: level.ghosts.map((ghost, index) => ({
      col: ghost.col,
      color: ghostColors[index % ghostColors.length],
      direction: index % 2 === 0 ? 'right' : 'left',
      home: { row: ghost.home_row, col: ghost.home_col },
      mode: ghost.state === 'frighten' || ghost.state === 'eaten' ? ghost.state : 'chase',
      row: ghost.row,
    })),
    level,
    levelCount: config.levels.length,
    levelIndex: level.level_index,
    lives: previous?.lives ?? config.lives,
    pacgums: mapCollectibles(level.pacgums),
    player: {
      col: level.player.col,
      direction: 'right',
      row: level.player.row,
    },
    playerName,
    requestedDirection: 'right',
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

function canMove(level: PacmanLevel, row: number, col: number, direction: Direction) {
  const roundedRow = Math.round(row);
  const roundedCol = Math.round(col);
  if (roundedRow < 0 || roundedRow >= level.height || roundedCol < 0 || roundedCol >= level.width) return false;
  const movement = directions[direction];
  const nextRow = roundedRow + movement.row;
  const nextCol = roundedCol + movement.col;
  if (nextRow < 0 || nextRow >= level.height || nextCol < 0 || nextCol >= level.width) return false;
  const cell = level.cells[roundedRow][roundedCol];
  return !cell.is_42_pattern && (cell.walls & movement.wall) === 0;
}

function isCenter(entity: Entity) {
  return Math.abs(entity.row - Math.round(entity.row)) < 0.08 && Math.abs(entity.col - Math.round(entity.col)) < 0.08;
}

function moveEntity(entity: Entity, direction: Direction, speed: number, deltaSeconds: number) {
  const movement = directions[direction];
  entity.row += movement.row * speed * deltaSeconds;
  entity.col += movement.col * speed * deltaSeconds;
}

function chooseGhostDirection(game: Game, ghost: Ghost) {
  const options = (Object.keys(directions) as Direction[]).filter((direction) =>
    canMove(game.level, ghost.row, ghost.col, direction),
  );
  if (options.length === 0) return ghost.direction;
  const target =
    ghost.mode === 'eaten'
      ? ghost.home
      : ghost.mode === 'frighten'
        ? { row: game.level.height - game.player.row - 1, col: game.level.width - game.player.col - 1 }
        : game.player;
  return options.sort((first, second) => {
    const firstDistance = distanceAfterMove(ghost, first, target);
    const secondDistance = distanceAfterMove(ghost, second, target);
    return ghost.mode === 'frighten' ? secondDistance - firstDistance : firstDistance - secondDistance;
  })[0];
}

function distanceAfterMove(entity: Entity, direction: Direction, target: { row: number; col: number }) {
  const movement = directions[direction];
  return Math.abs(entity.row + movement.row - target.row) + Math.abs(entity.col + movement.col - target.col);
}

function resetPositions(game: Game) {
  game.player = {
    col: game.level.player.col,
    direction: 'right',
    row: game.level.player.row,
  };
  game.requestedDirection = 'right';
  game.ghosts = game.level.ghosts.map((ghost, index) => ({
    col: ghost.col,
    color: ghostColors[index % ghostColors.length],
    direction: index % 2 === 0 ? 'right' : 'left',
    home: { row: ghost.home_row, col: ghost.home_col },
    mode: 'chase',
    row: ghost.row,
  }));
  game.frightenedUntil = 0;
}

function updateGame(game: Game, deltaSeconds: number) {
  if (game.status !== 'playing') return;
  const playerSpeed = 4;
  const ghostSpeed = game.levelIndex < 5 ? 3 : 3.4;

  game.elapsedSeconds += deltaSeconds;
  game.totalElapsedSeconds += deltaSeconds;
  game.timeLeft = Math.max(0, game.timeLeft - deltaSeconds);
  if (game.timeLeft <= 0) {
    game.status = 'lost';
    return;
  }

  if (isCenter(game.player)) {
    game.player.row = Math.round(game.player.row);
    game.player.col = Math.round(game.player.col);
    if (canMove(game.level, game.player.row, game.player.col, game.requestedDirection)) {
      game.player.direction = game.requestedDirection;
    }
  }
  if (canMove(game.level, game.player.row, game.player.col, game.player.direction)) {
    moveEntity(game.player, game.player.direction, playerSpeed, deltaSeconds);
  }

  const playerKey = keyOf(Math.round(game.player.row), Math.round(game.player.col));
  const pacgum = game.pacgums.get(playerKey);
  if (pacgum) {
    game.score += pacgum.points;
    game.pacgums.delete(playerKey);
  }
  const superPacgum = game.superPacgums.get(playerKey);
  if (superPacgum) {
    game.score += superPacgum.points;
    game.superPacgums.delete(playerKey);
    game.frightenedUntil = game.elapsedSeconds + 10;
    for (const ghost of game.ghosts) {
      if (ghost.mode !== 'eaten') ghost.mode = 'frighten';
    }
  }

  for (const ghost of game.ghosts) {
    if (ghost.mode === 'frighten' && game.elapsedSeconds > game.frightenedUntil) ghost.mode = 'chase';
    if (isCenter(ghost)) {
      ghost.row = Math.round(ghost.row);
      ghost.col = Math.round(ghost.col);
      if (ghost.mode === 'eaten' && ghost.row === ghost.home.row && ghost.col === ghost.home.col) {
        ghost.mode = 'chase';
      }
      ghost.direction = chooseGhostDirection(game, ghost);
    }
    if (canMove(game.level, ghost.row, ghost.col, ghost.direction)) {
      moveEntity(ghost, ghost.direction, ghost.mode === 'eaten' ? ghostSpeed * 1.45 : ghostSpeed, deltaSeconds);
    }
  }

  for (const ghost of game.ghosts) {
    const distance = Math.hypot(game.player.row - ghost.row, game.player.col - ghost.col);
    if (distance > 0.45) continue;
    if (ghost.mode === 'frighten') {
      ghost.mode = 'eaten';
      game.score += game.level.points.ghost;
      continue;
    }
    if (ghost.mode !== 'chase') continue;
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
  const width = Math.max(640, Math.floor(rect.width || 960));
  const height = Math.max(420, Math.floor(width * 0.5625));
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

  const paddingTop = 74;
  const padding = 28;
  const boardSize = Math.min(width - padding * 2, height - paddingTop - padding);
  const cellSize = boardSize / Math.max(game.level.width, game.level.height);
  const offsetX = (width - game.level.width * cellSize) / 2;
  const offsetY = paddingTop + (height - paddingTop - game.level.height * cellSize) / 2;

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
  const [message, setMessage] = useState('Enter your name before starting.');

  const refreshScores = useCallback(async () => {
    try {
      setScores(await fetchPacmanScores(10));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not load leaderboard.');
    }
  }, []);

  const loadLevel = useCallback(async (levelIndex: number, player: string, previous?: Game) => {
    loadingNextLevelRef.current = true;
    setMessage(levelIndex === 0 ? 'Loading game...' : 'Loading next level...');
    try {
      const config = configRef.current ?? (await fetchPacmanConfig());
      configRef.current = config;
      const level = await fetchPacmanLevel(levelIndex);
      const game = createGame({ config, level, playerName: player, previous });
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
  }, []);

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
          void loadLevel(game.levelIndex + 1, game.playerName, game);
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

      <div className="p-5 lg:p-7">
        <section className="relative overflow-hidden rounded-2xl border border-[#d8d1c2] bg-[#171715] shadow-sm">
          <canvas
            aria-label="Pac-Man playable maze"
            className="block aspect-video w-full bg-[#fffdf8]"
            ref={canvasRef}
          />

          <div className="pointer-events-none absolute inset-x-0 top-0 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-b from-[#171715]/80 to-transparent p-4 text-[#faf9f5]">
            <div className="flex flex-wrap gap-2">
              <GamePill label="Player" value={snapshot.playerName || 'Waiting'} />
              <GamePill label="Score" value={snapshot.score.toLocaleString()} />
              <GamePill label="Lives" value={snapshot.lives.toString()} />
              <GamePill label="Time" value={`${snapshot.timeLeft}s`} />
            </div>
            <span className="rounded-full bg-[#faf9f5]/15 px-3 py-1 text-xs font-bold uppercase tracking-wide">
              {snapshot.statusText}
            </span>
          </div>

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
                <div className="mt-5 flex flex-wrap gap-2">
                  <button
                    className="min-h-11 rounded-lg bg-[#30302e] px-5 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#171715]"
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

          <div className="absolute bottom-4 left-4 right-4 grid gap-3 md:grid-cols-[auto_1fr]">
            <div className="flex flex-wrap gap-2">
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
            </div>
            <div className="min-w-0 rounded-xl border border-[#faf9f5]/20 bg-[#171715]/70 p-3 text-[#faf9f5] backdrop-blur">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-bold uppercase tracking-wide text-[#faf9f5]/70">Leaderboard</p>
                <button
                  className="text-xs font-bold text-[#f0b89d] underline-offset-4 hover:underline"
                  onClick={() => void refreshScores()}
                  type="button"
                >
                  Refresh
                </button>
              </div>
              <ol className="mt-2 grid gap-1 sm:grid-cols-2 lg:grid-cols-5">
                {scores.slice(0, 5).map((score, index) => (
                  <li className="min-w-0 rounded-lg bg-[#faf9f5]/10 px-2 py-1 text-xs" key={score.id}>
                    <span className="font-bold">{index + 1}. </span>
                    <span className="truncate">{score.player_name}</span>
                    <span className="ml-1 font-mono text-[#f0b89d]">{score.score}</span>
                  </li>
                ))}
                {scores.length === 0 ? (
                  <li className="rounded-lg bg-[#faf9f5]/10 px-2 py-1 text-xs text-[#faf9f5]/75">
                    No scores yet.
                  </li>
                ) : null}
              </ol>
            </div>
          </div>
        </section>
      </div>
    </article>
  );
}

function GamePill({ label, value }: { label: string; value: string }) {
  return (
    <span className="rounded-full bg-[#171715]/55 px-3 py-1 text-xs font-semibold ring-1 ring-[#faf9f5]/20 backdrop-blur">
      <span className="text-[#faf9f5]/60">{label}</span> {value}
    </span>
  );
}

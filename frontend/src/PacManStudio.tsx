import { useCallback, useEffect, useRef, useState } from 'react';

import {
  fetchPacmanScores,
  pacmanStreamUrl,
  restartPacmanRun,
  startPacmanRun,
  submitPacmanRunScore,
  updatePacmanRunInput,
  type PacmanCell,
  type PacmanRunFrame,
  type PacmanRunSnapshot,
  type PacmanStreamMessage,
  type PacmanScore,
} from './api/pacman';
import { CollapsibleDescription } from './components/CollapsibleDescription';

type Direction = 'up' | 'down' | 'left' | 'right';
type ViewStatus = PacmanRunSnapshot['status'] | 'idle' | 'loading' | 'error';

const WALL_NORTH = 1;
const WALL_EAST = 2;
const WALL_SOUTH = 4;
const WALL_WEST = 8;
const ghostColors = ['#d95f4f', '#6da6b6', '#d38a4a', '#b47ab0'];

const emptyMetrics = {
  cheatMode: false,
  cheatUsed: false,
  completed: false,
  elapsedSeconds: 0,
  level: 1,
  levelCount: 10,
  lives: 3,
  playerName: '',
  score: 0,
  scoreEligible: false,
  status: 'idle' as ViewStatus,
  statusText: 'Enter your name to start.',
  timeLeft: 90,
};

function metricsFromSnapshot(snapshot: PacmanRunSnapshot | null, viewStatus: ViewStatus) {
  if (!snapshot) return { ...emptyMetrics, status: viewStatus };
  return {
    cheatMode: snapshot.cheat_mode,
    cheatUsed: snapshot.cheat_used,
    completed: snapshot.completed,
    elapsedSeconds: snapshot.elapsed_seconds,
    level: snapshot.level,
    levelCount: snapshot.level_count,
    lives: snapshot.lives,
    playerName: snapshot.player_name,
    score: snapshot.score,
    scoreEligible: snapshot.score_eligible,
    status: snapshot.status as ViewStatus,
    statusText: snapshot.status_text,
    timeLeft: snapshot.time_left,
  };
}

function drawGame(canvas: HTMLCanvasElement, snapshot: PacmanRunSnapshot | null) {
  const context = canvas.getContext('2d');
  if (!context) return;

  const rect = canvas.getBoundingClientRect();
  const width = Math.max(340, Math.floor(rect.width || 620));
  const height = Math.max(340, Math.floor(rect.height || width));
  const ratio = window.devicePixelRatio || 1;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);

  const isDark =
    document.documentElement.classList.contains('theme-dark') ||
    document.documentElement.dataset.theme === 'dark';
  context.fillStyle = isDark ? '#171715' : '#fffdf8';
  context.fillRect(0, 0, width, height);

  if (!snapshot) {
    context.fillStyle = isDark ? '#b8afa3' : '#8b8174';
    context.font = '600 20px Inter, sans-serif';
    context.textAlign = 'center';
    context.fillText('Enter your name to start Pac_Man', width / 2, height / 2);
    return;
  }

  const padding = 22;
  const boardSize = Math.min(width - padding * 2, height - padding * 2);
  const cellSize = boardSize / Math.max(snapshot.width, snapshot.height);
  const offsetX = (width - snapshot.width * cellSize) / 2;
  const offsetY = (height - snapshot.height * cellSize) / 2;

  context.lineWidth = Math.max(2, cellSize * 0.12);
  context.strokeStyle = isDark ? '#7a9f91' : '#668f80';
  context.lineCap = 'round';
  for (const row of snapshot.cells) {
    for (const cell of row) drawCell(context, cell, offsetX, offsetY, cellSize, isDark);
  }

  for (const pellet of snapshot.pacgums) {
    drawCircle(context, offsetX + (pellet.col + 0.5) * cellSize, offsetY + (pellet.row + 0.5) * cellSize, cellSize * 0.1, '#d4b16a');
  }
  for (const pellet of snapshot.super_pacgums) {
    drawCircle(context, offsetX + (pellet.col + 0.5) * cellSize, offsetY + (pellet.row + 0.5) * cellSize, cellSize * 0.23, '#d96d4a');
  }

  drawPacman(
    context,
    offsetX + (snapshot.player.col + 0.5) * cellSize,
    offsetY + (snapshot.player.row + 0.5) * cellSize,
    cellSize * 0.35,
    normalizeDirection(snapshot.player.direction),
  );
  snapshot.ghosts.forEach((ghost, index) => {
    const color =
      ghost.state === 'frighten' ? '#7da9c5' : ghost.state === 'eaten' ? '#9b9488' : ghostColors[index % ghostColors.length];
    drawGhost(context, offsetX + (ghost.col + 0.5) * cellSize, offsetY + (ghost.row + 0.5) * cellSize, cellSize * 0.35, color);
  });
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

function normalizeDirection(direction: string): Direction {
  return direction === 'up' || direction === 'down' || direction === 'left' || direction === 'right'
    ? direction
    : 'right';
}

function interpolateSnapshot(
  previous: PacmanRunSnapshot | null,
  current: PacmanRunSnapshot | null,
  currentAt: number,
  now: number,
) {
  if (!current) return null;
  if (!previous || previous.level_index !== current.level_index) return current;
  const progress = Math.min(1, Math.max(0, (now - currentAt) / (1000 / 30)));
  return {
    ...current,
    ghosts: current.ghosts.map((ghost, index) => {
      const previousGhost = previous.ghosts[index];
      if (!previousGhost || previousGhost.state !== ghost.state) return ghost;
      return {
        ...ghost,
        col: previousGhost.col + (ghost.col - previousGhost.col) * progress,
        row: previousGhost.row + (ghost.row - previousGhost.row) * progress,
      };
    }),
    player: {
      ...current.player,
      col: previous.player.col + (current.player.col - previous.player.col) * progress,
      row: previous.player.row + (current.player.row - previous.player.row) * progress,
    },
  };
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
  const frameRef = useRef<number | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const snapshotRef = useRef<PacmanRunSnapshot | null>(null);
  const previousFrameRef = useRef<PacmanRunSnapshot | null>(null);
  const currentFrameRef = useRef<PacmanRunSnapshot | null>(null);
  const currentFrameAtRef = useRef(0);
  const [snapshot, setSnapshot] = useState<PacmanRunSnapshot | null>(null);
  const [viewStatus, setViewStatus] = useState<ViewStatus>('idle');
  const [scores, setScores] = useState<PacmanScore[]>([]);
  const [playerName, setPlayerName] = useState('');
  const [cheatMode, setCheatMode] = useState(false);
  const [message, setMessage] = useState('Enter your name before starting.');

  const metrics = metricsFromSnapshot(snapshot, viewStatus);
  const runEnded = metrics.status === 'won' || metrics.status === 'lost';
  const canStart = playerName.trim().length > 0 && viewStatus !== 'loading';

  const setRunSnapshot = useCallback((next: PacmanRunSnapshot) => {
    snapshotRef.current = next;
    previousFrameRef.current = currentFrameRef.current ?? next;
    currentFrameRef.current = next;
    currentFrameAtRef.current = performance.now();
    setSnapshot(next);
    setViewStatus(next.status);
    setCheatMode(next.cheat_mode);
  }, []);

  const applyFrame = useCallback((frame: PacmanRunFrame) => {
    const board = snapshotRef.current;
    if (!board) return;
    const next: PacmanRunSnapshot = { ...board, ...frame };
    snapshotRef.current = next;
    previousFrameRef.current = currentFrameRef.current ?? next;
    currentFrameRef.current = next;
    currentFrameAtRef.current = performance.now();
    setSnapshot(next);
    setViewStatus(next.status);
    setCheatMode(next.cheat_mode);
  }, []);

  const closeStream = useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
  }, []);

  const openStream = useCallback((runId: string) => {
    closeStream();
    const socket = new WebSocket(pacmanStreamUrl(runId));
    socketRef.current = socket;

    socket.onopen = () => {
      setMessage('Use Arrow keys or WASD.');
    };
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data as string) as PacmanStreamMessage;
        if (message.kind === 'snapshot') {
          setRunSnapshot(message.data);
          return;
        }
        if (message.kind === 'frame') {
          applyFrame(message.data);
          return;
        }
        setMessage(message.detail);
      } catch {
        setMessage('Pac-Man stream returned an invalid message.');
      }
    };
    socket.onerror = () => {
      setMessage('Pac-Man stream connection failed.');
    };
    socket.onclose = () => {
      if (socketRef.current === socket) socketRef.current = null;
    };
  }, [applyFrame, closeStream, setRunSnapshot]);

  const sendStreamMessage = useCallback((payload: { direction?: Direction; paused?: boolean; cheat_mode?: boolean }) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify(payload));
    return true;
  }, []);

  const refreshScores = useCallback(async () => {
    try {
      setScores(await fetchPacmanScores(10));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not load leaderboard.');
    }
  }, []);

  const startRun = useCallback(async () => {
    const cleanName = playerName.trim();
    if (!cleanName) {
      setMessage('Enter your name before starting.');
      return;
    }
    setViewStatus('loading');
    setMessage('Starting game...');
    try {
      const next = await startPacmanRun({ cheat_mode: cheatMode, player_name: cleanName });
      setRunSnapshot(next);
      openStream(next.run_id);
      setMessage('Use Arrow keys or WASD.');
    } catch (error) {
      setViewStatus('error');
      setMessage(error instanceof Error ? error.message : 'Could not start Pac-Man.');
    }
  }, [cheatMode, openStream, playerName, setRunSnapshot]);

  const restart = useCallback(async () => {
    const activeName = snapshotRef.current?.player_name ?? playerName.trim();
    if (!activeName) {
      setMessage('Enter your name before restarting.');
      return;
    }
    setViewStatus('loading');
    setMessage('Restarting...');
    try {
      const next = snapshotRef.current
        ? await restartPacmanRun(snapshotRef.current.run_id, { cheat_mode: cheatMode, player_name: activeName })
        : await startPacmanRun({ cheat_mode: cheatMode, player_name: activeName });
      setRunSnapshot(next);
      openStream(next.run_id);
      setMessage('Use Arrow keys or WASD.');
    } catch (error) {
      setViewStatus('error');
      setMessage(error instanceof Error ? error.message : 'Could not restart Pac-Man.');
    }
  }, [cheatMode, openStream, playerName, setRunSnapshot]);

  const updateInput = useCallback(async (payload: { direction?: Direction; paused?: boolean; cheat_mode?: boolean }) => {
    const active = snapshotRef.current;
    if (!active || active.status === 'won' || active.status === 'lost') return;
    if (sendStreamMessage(payload)) {
      if (payload.cheat_mode !== undefined) {
        setMessage(payload.cheat_mode ? 'Cheat mode enabled: no timer or life loss.' : 'Cheat mode disabled.');
      }
      return;
    }
    try {
      const next = await updatePacmanRunInput(active.run_id, payload);
      setRunSnapshot(next);
      if (payload.cheat_mode !== undefined) {
        setMessage(payload.cheat_mode ? 'Cheat mode enabled: no timer or life loss.' : 'Cheat mode disabled.');
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not update Pac-Man input.');
    }
  }, [sendStreamMessage, setRunSnapshot]);

  const togglePause = useCallback(() => {
    const active = snapshotRef.current;
    if (!active || active.status === 'won' || active.status === 'lost') return;
    void updateInput({ paused: active.status !== 'paused' });
  }, [updateInput]);

  const toggleCheatMode = useCallback(() => {
    const nextCheatMode = !cheatMode;
    setCheatMode(nextCheatMode);
    if (snapshotRef.current) void updateInput({ cheat_mode: nextCheatMode });
    else setMessage(nextCheatMode ? 'Cheat mode will be enabled when the run starts.' : 'Cheat mode disabled.');
  }, [cheatMode, updateInput]);

  const submitFinalScore = useCallback(async () => {
    const active = snapshotRef.current;
    if (!active || !runEnded) return;
    if (!active.score_eligible) {
      setMessage('Cheat runs are not saved to the leaderboard.');
      return;
    }
    try {
      await submitPacmanRunScore(active.run_id);
      setMessage('Score saved.');
      await refreshScores();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not submit score.');
    }
  }, [refreshScores, runEnded]);

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
      if (isEditableTarget) return;

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
      void updateInput({ direction });
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePause, updateInput]);

  useEffect(() => {
    const tick = (timestamp: number) => {
      if (canvasRef.current) {
        drawGame(
          canvasRef.current,
          interpolateSnapshot(
            previousFrameRef.current,
            currentFrameRef.current,
            currentFrameAtRef.current,
            timestamp,
          ),
        );
      }
      frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    };
  }, []);

  useEffect(() => closeStream, [closeStream]);

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
            <p className="text-sm font-semibold text-[#c96442]">Backend-driven browser game</p>
            <h2 className="mt-2 font-serif text-5xl leading-none text-[#171715] sm:text-6xl">Pac_Man</h2>
          </div>
          <div className="rounded-full border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#5e5d59]">
            Level {metrics.level} / {metrics.levelCount}
          </div>
        </div>
        <CollapsibleDescription
          className="mt-5"
          fullText={fullDescription ?? description}
          previewText={description}
        />
      </div>

      <div className="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_340px] lg:p-7">
        <section className="relative mx-auto aspect-square w-full max-w-[600px] overflow-hidden rounded-2xl border border-[#d8d1c2] bg-[#fffdf8] shadow-sm">
          <canvas
            aria-label="Pac-Man playable maze"
            className="block h-full w-full bg-[#fffdf8]"
            ref={canvasRef}
          />

          {metrics.status === 'idle' || metrics.status === 'error' ? (
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
                      if (event.key === 'Enter') void startRun();
                    }}
                    placeholder="Your name"
                    value={playerName}
                  />
                  <button
                    className="min-h-11 rounded-lg bg-[#c96442] px-5 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334] disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={!canStart}
                    onClick={() => void startRun()}
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
                <p className="text-sm font-semibold text-[#c96442]">{metrics.statusText}</p>
                <h3 className="mt-2 font-serif text-4xl text-[#171715]">
                  {metrics.score.toLocaleString()} points
                </h3>
                <p className="mt-3 text-sm leading-6 text-[#5e5d59]">
                  Level {metrics.level} reached in {metrics.elapsedSeconds}s.
                </p>
                {metrics.cheatUsed ? (
                  <p className="mt-2 text-sm font-semibold text-[#8a4429]">
                    Cheat runs are not saved to the leaderboard.
                  </p>
                ) : null}
                <div className="mt-5 flex flex-wrap gap-2">
                  <button
                    className="min-h-11 rounded-lg bg-[#30302e] px-5 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#171715] disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={!metrics.scoreEligible}
                    onClick={() => void submitFinalScore()}
                    type="button"
                  >
                    Save score
                  </button>
                  <button
                    className="min-h-11 rounded-lg bg-[#c96442] px-5 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334]"
                    onClick={() => void restart()}
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
                {metrics.statusText}
              </span>
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Player" value={metrics.playerName || 'Waiting'} />
              <Metric label="Level" value={`${metrics.level}/${metrics.levelCount}`} />
              <Metric label="Score" value={metrics.score.toLocaleString()} />
              <Metric label="Lives" value={metrics.lives.toString()} />
              <Metric label="Time" value={metrics.cheatMode ? '∞' : `${metrics.timeLeft}s`} />
              <Metric label="Elapsed" value={`${metrics.elapsedSeconds}s`} />
            </dl>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                className="min-h-10 rounded-lg bg-[#c96442] px-4 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334]"
                onClick={() => void restart()}
                type="button"
              >
                Restart
              </button>
              <button
                className="min-h-10 rounded-lg border border-[#d8e3ce] bg-[#7f9f6f] px-4 text-sm font-semibold text-[#fffdf8] transition hover:bg-[#6f8f5f] disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!snapshot || runEnded}
                onClick={togglePause}
                type="button"
              >
                {metrics.status === 'paused' ? 'Resume' : 'Pause'}
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

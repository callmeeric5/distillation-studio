import { useEffect, useMemo, useState } from 'react';

import {
  generateMaze,
  solveMaze,
  type Direction,
  type GenerateAlgorithm,
  type MazeCell,
  type MazeResponse,
  type MazeTheme,
  type MazeStep,
  type SolveAlgorithm,
} from './api/aMazeIng';

type MazeConfig = {
  width: number;
  height: number;
  entry: string;
  exit: string;
  display42: boolean;
  perfect: boolean;
  seed: number;
  generateAlgorithm: GenerateAlgorithm;
  solveAlgorithm: SolveAlgorithm;
  theme: MazeTheme;
  speed: number;
};

const opposite: Record<Direction, Direction> = {
  east: 'west',
  north: 'south',
  south: 'north',
  west: 'east',
};

const themeStyles: Record<
  MazeTheme,
  {
    background: string;
    wall: string;
    cell: string;
    blocked: string;
    generated: string;
    visited: string;
    path: string;
    entry: string;
    exit: string;
  }
> = {
  classic: {
    background: '#f4f1e8',
    wall: '#2f302d',
    cell: '#fffdf8',
    blocked: '#b8afa3',
    generated: '#f8eadf',
    visited: '#dfe8f0',
    path: '#c96442',
    entry: '#49603b',
    exit: '#8a4429',
  },
  ember: {
    background: '#211917',
    wall: '#f0dfcf',
    cell: '#35241f',
    blocked: '#6b5148',
    generated: '#4a2e25',
    visited: '#5b392e',
    path: '#ee9b72',
    entry: '#d5bb83',
    exit: '#f2d2bc',
  },
  forest: {
    background: '#182018',
    wall: '#d9e5cf',
    cell: '#243024',
    blocked: '#43523f',
    generated: '#2f3e2c',
    visited: '#354a3e',
    path: '#a7c97a',
    entry: '#d8d19b',
    exit: '#e8a979',
  },
  midnight: {
    background: '#171b21',
    wall: '#e8edf2',
    cell: '#222936',
    blocked: '#435066',
    generated: '#283448',
    visited: '#2f4962',
    path: '#8fbce6',
    entry: '#b8d48b',
    exit: '#e7a77f',
  },
};

function keyOf(row: number, col: number) {
  return `${row}:${col}`;
}

function allWalls(cell: MazeCell): MazeCell {
  return {
    ...cell,
    walls: {
      east: true,
      north: true,
      south: true,
      west: true,
    },
  };
}

function cloneCells(cells: MazeCell[]) {
  return cells.map((cell) => ({ ...cell, walls: { ...cell.walls } }));
}

function openWall(cells: MazeCell[], step: MazeStep) {
  const next = cloneCells(cells);
  const from = next.find((cell) => cell.row === step.from.row && cell.col === step.from.col);
  const to = next.find((cell) => cell.row === step.to.row && cell.col === step.to.col);
  if (from) from.walls[step.direction] = false;
  if (to) to.walls[opposite[step.direction]] = false;
  return next;
}

function parseTuple(value: string) {
  const match = value.trim().match(/^\(?\s*(\d+)\s*(?:,|\s)\s*(\d+)\s*\)?$/);
  if (!match) return null;
  return {
    row: Number(match[1]),
    col: Number(match[2]),
  };
}

function tupleIsInside(
  coord: { row: number; col: number } | null,
  height: number,
  width: number,
) {
  return Boolean(
    coord &&
      Number.isInteger(coord.row) &&
      Number.isInteger(coord.col) &&
      coord.row >= 0 &&
      coord.row < height &&
      coord.col >= 0 &&
      coord.col < width,
  );
}

export function AMazeIngStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const [config, setConfig] = useState<MazeConfig>({
    display42: false,
    entry: '(0, 0)',
    exit: '(14, 20)',
    generateAlgorithm: 'backtracking',
    height: 15,
    perfect: true,
    seed: 42,
    solveAlgorithm: 'astar',
    speed: 28,
    theme: 'classic',
    width: 21,
  });
  const [response, setResponse] = useState<MazeResponse | null>(null);
  const [visibleCells, setVisibleCells] = useState<MazeCell[]>([]);
  const [visited, setVisited] = useState<Set<string>>(new Set());
  const [path, setPath] = useState<Set<string>>(new Set());
  const [phase, setPhase] = useState<'idle' | 'generating' | 'solving' | 'done'>('idle');
  const [stepIndex, setStepIndex] = useState(0);
  const [status, setStatus] = useState('Configure a maze and generate it.');
  const [isBusy, setIsBusy] = useState(false);
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);

  const colors = themeStyles[config.theme];
  const canExpand = fullDescription && fullDescription !== description;
  const entryCoord = parseTuple(config.entry);
  const exitCoord = parseTuple(config.exit);
  const displayHeight = response?.stats.height ?? config.height;
  const displayWidth = response?.stats.width ?? config.width;
  const cellsByKey = useMemo(
    () => new Map(visibleCells.map((cell) => [keyOf(cell.row, cell.col), cell])),
    [visibleCells],
  );

  function updateConfig<K extends keyof MazeConfig>(key: K, value: MazeConfig[K]) {
    setConfig((current) => {
      return { ...current, [key]: value };
    });
  }

  function validatedEndpoints(height = config.height, width = config.width) {
    const parsedEntry = parseTuple(config.entry);
    const parsedExit = parseTuple(config.exit);
    if (!parsedEntry || !tupleIsInside(parsedEntry, height, width)) {
      setStatus(`Entry must be a tuple inside the ${height}x${width} maze.`);
      return null;
    }
    if (!parsedExit || !tupleIsInside(parsedExit, height, width)) {
      setStatus(`Exit must be a tuple inside the ${height}x${width} maze.`);
      return null;
    }
    if (parsedEntry.row === parsedExit.row && parsedEntry.col === parsedExit.col) {
      setStatus('Entry and exit must be different cells.');
      return null;
    }
    return { parsedEntry, parsedExit };
  }

  async function regenerateMaze() {
    const endpoints = validatedEndpoints();
    if (!endpoints) return;

    setIsBusy(true);
    setPhase('idle');
    setStepIndex(0);
    setVisited(new Set());
    setPath(new Set());
    setStatus('Generating maze trace...');
    try {
      const payload = {
        display_42: config.display42,
        entry: endpoints.parsedEntry,
        exit: endpoints.parsedExit,
        generate_algorithm: config.generateAlgorithm,
        height: config.height,
        perfect: config.perfect,
        seed: config.seed,
        solve_algorithm: config.solveAlgorithm,
        theme: config.theme,
        width: config.width,
      };
      const data = await generateMaze(payload);
      setResponse({
        ...data,
        path: [],
        solve_steps: [],
        stats: {
          ...data.stats,
          path_length: 0,
          visited_steps: 0,
        },
      });
      setVisibleCells(data.cells.map(allWalls));
      setPhase('generating');
      setStatus('Animating generation...');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not generate the maze.');
    } finally {
      setIsBusy(false);
    }
  }

  async function resolveMaze() {
    if (!response) return;
    const endpoints = validatedEndpoints(response.stats.height, response.stats.width);
    if (!endpoints) return;

    setIsBusy(true);
    setPhase('idle');
    setStepIndex(0);
    setVisited(new Set());
    setPath(new Set());
    setVisibleCells(response.cells);
    setStatus('Solving current maze...');
    try {
      const payload = {
        cells: response.cells,
        entry: endpoints.parsedEntry,
        exit: endpoints.parsedExit,
        height: response.stats.height,
        solve_algorithm: config.solveAlgorithm,
        width: response.stats.width,
      };
      const data = await solveMaze(payload);
      setResponse((current) => {
        if (!current) return current;
        return {
          ...current,
          path: data.path,
          solve_steps: data.solve_steps,
          stats: {
            ...current.stats,
            path_length: data.stats.path_length,
            visited_steps: data.stats.visited_steps,
          },
        };
      });
      setPhase('solving');
      setStatus('Animating solver...');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not solve the maze.');
    } finally {
      setIsBusy(false);
    }
  }

  useEffect(() => {
    if (!response || phase === 'idle' || phase === 'done') return undefined;
    const timer = window.setTimeout(() => {
      if (phase === 'generating') {
        const current = response.generation_steps[stepIndex];
        if (!current) {
          setVisibleCells(response.cells);
          setStepIndex(0);
          setPhase('done');
          setStatus('Maze generated. Choose a solve algorithm, then resolve.');
          return;
        }
        setVisibleCells((cells) => openWall(cells, current));
        setStepIndex((index) => index + 1);
      }

      if (phase === 'solving') {
        const current = response.solve_steps[stepIndex];
        if (!current) {
          setPath(new Set(response.path.map((cell) => keyOf(cell.row, cell.col))));
          setPhase('done');
          setStatus(`Solved with ${response.stats.path_length} path cells.`);
          return;
        }
        setVisited((currentVisited) => {
          const next = new Set(currentVisited);
          next.add(keyOf(current.row, current.col));
          return next;
        });
        setStepIndex((index) => index + 1);
      }
    }, config.speed);

    return () => window.clearTimeout(timer);
  }, [config.speed, phase, response, stepIndex]);

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <div className="grid min-h-[760px] lg:grid-cols-[minmax(0,1fr)_390px]">
        <section className="flex min-w-0 flex-col">
          <header className="flex flex-col gap-5 border-b border-[#ece8dc] p-5 lg:p-7">
            <div className="max-w-4xl">
              <button
                className="mb-5 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#30302e] transition hover:bg-[#faf9f5]"
                onClick={onBack}
                type="button"
              >
                Back to gallery
              </button>
              <p className="text-sm font-semibold text-[#c96442]">42 A_Maze_Ing</p>
              <h3 className="mt-2 font-serif text-4xl leading-tight text-[#171715] sm:text-5xl">
                A_Maze_Ing Studio
              </h3>
              <p className="mt-5 text-lg leading-8 text-[#5e5d59]">
                {isDescriptionExpanded || !canExpand ? (fullDescription ?? description) : description}
              </p>
              <div className="mt-3 flex flex-wrap gap-3">
                {canExpand ? (
                  <button
                    className="min-h-9 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 text-sm font-semibold text-[#8a4429] transition hover:bg-[#fffdf8]"
                    onClick={() => setIsDescriptionExpanded((current) => !current)}
                    type="button"
                  >
                    {isDescriptionExpanded ? 'Less' : 'More'}
                  </button>
                ) : null}
                <a
                  className="inline-flex min-h-9 items-center rounded-lg bg-[#c96442] px-4 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334]"
                  href="#a-maze-ing-config"
                >
                  Config
                </a>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 text-sm text-[#5e5d59]">
              <Metric label="cells" value={response?.stats.cells ?? config.width * config.height} />
              <Metric label="carves" value={response?.stats.generation_steps ?? 0} />
              <Metric label="visited" value={visited.size} />
              <Metric label="path" value={path.size || response?.stats.path_length || 0} />
            </div>
          </header>

          <div
            className="flex flex-1 items-center justify-center overflow-auto p-4 lg:p-6"
            style={{ backgroundColor: colors.background }}
          >
            <div
              className="grid"
              style={{
                gridTemplateColumns: `repeat(${displayWidth}, minmax(12px, 1fr))`,
                maxWidth: 'min(100%, 980px)',
                width: '100%',
              }}
            >
              {Array.from({ length: displayHeight * displayWidth }, (_, index) => {
                const row = Math.floor(index / displayWidth);
                const col = index % displayWidth;
                const cell = cellsByKey.get(keyOf(row, col));
                const isEntry = entryCoord?.row === row && entryCoord.col === col;
                const isExit = exitCoord?.row === row && exitCoord.col === col;
                const cellKey = keyOf(row, col);
                const isPath = path.has(cellKey);
                const isVisited = visited.has(cellKey);
                const walls = cell?.walls ?? { east: true, north: true, south: true, west: true };
                let backgroundColor = colors.cell;
                if (cell?.blocked) backgroundColor = colors.blocked;
                if (cell && !cell.blocked) backgroundColor = colors.generated;
                if (isVisited) backgroundColor = colors.visited;
                if (isPath) backgroundColor = colors.path;
                if (isEntry) backgroundColor = colors.entry;
                if (isExit) backgroundColor = colors.exit;

                return (
                  <div
                    aria-label={
                      isEntry
                        ? `entry row ${row} column ${col}`
                        : isExit
                          ? `exit row ${row} column ${col}`
                          : `row ${row} column ${col}`
                    }
                    className="relative flex aspect-square items-center justify-center text-[10px] font-bold transition-colors"
                    key={cellKey}
                    style={{
                      backgroundColor,
                      borderBottom: `${walls.south ? 2 : 0}px solid ${colors.wall}`,
                      borderLeft: `${walls.west ? 2 : 0}px solid ${colors.wall}`,
                      borderRight: `${walls.east ? 2 : 0}px solid ${colors.wall}`,
                      borderTop: `${walls.north ? 2 : 0}px solid ${colors.wall}`,
                      color: '#fffdf8',
                      minHeight: 12,
                    }}
                  >
                    {isEntry ? (
                      <span className="maze-marker maze-marker-entry" />
                    ) : null}
                    {isExit ? (
                      <span className="maze-marker maze-marker-exit" />
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <aside
          className="scroll-mt-24 flex flex-col gap-5 border-t border-[#ece8dc] bg-[#faf9f5] p-5 lg:border-l lg:border-t-0"
          id="a-maze-ing-config"
        >
          <div className="grid grid-cols-2 gap-3">
            <NumberField label="Width" max={50} min={5} onChange={(value) => updateConfig('width', value)} value={config.width} />
            <NumberField label="Height" max={40} min={5} onChange={(value) => updateConfig('height', value)} value={config.height} />
          </div>

          <div>
            <div className="grid grid-cols-2 gap-3">
              <TupleField label="Entry" onChange={(value) => updateConfig('entry', value)} value={config.entry} />
              <TupleField label="Exit" onChange={(value) => updateConfig('exit', value)} value={config.exit} />
            </div>
            <p className="mt-2 text-xs font-semibold text-[#8b8174]">
              Format: (row, col)
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Toggle label="Display 42" onChange={(value) => updateConfig('display42', value)} value={config.display42} />
            <Toggle label="Perfect" onChange={(value) => updateConfig('perfect', value)} value={config.perfect} />
          </div>

          <NumberField label="Seed" max={999999} min={0} onChange={(value) => updateConfig('seed', value)} value={config.seed} />

          <SelectField
            label="Generate algorithm"
            onChange={(value) => updateConfig('generateAlgorithm', value as GenerateAlgorithm)}
            options={[
              ['backtracking', 'Backtracking'],
              ['binary_tree', 'Binary tree'],
              ['sidewinder', 'Sidewinder'],
              ['prim', 'Prim'],
            ]}
            value={config.generateAlgorithm}
          />

          <SelectField
            label="Solve algorithm"
            onChange={(value) => updateConfig('solveAlgorithm', value as SolveAlgorithm)}
            options={[
              ['astar', 'A*'],
              ['bfs', 'BFS'],
              ['dfs', 'DFS'],
            ]}
            value={config.solveAlgorithm}
          />

          <SelectField
            label="Theme"
            onChange={(value) => updateConfig('theme', value as MazeTheme)}
            options={[
              ['classic', 'Classic'],
              ['midnight', 'Midnight'],
              ['forest', 'Forest'],
              ['ember', 'Ember'],
            ]}
            value={config.theme}
          />

          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">
              Animation speed <b className="text-[#30302e]">{config.speed} ms</b>
            </span>
            <input
              className="accent-[#c96442]"
              max={180}
              min={8}
              onChange={(event) => updateConfig('speed', Number(event.target.value))}
              step={4}
              type="range"
              value={config.speed}
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <button
              className="min-h-11 rounded-lg bg-[#c96442] px-4 text-sm font-bold text-[#faf9f5] transition hover:bg-[#b65334] disabled:opacity-60"
              disabled={isBusy}
              onClick={regenerateMaze}
              type="button"
            >
              Regenerate
            </button>
            <button
              className="min-h-11 rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-4 text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8] disabled:opacity-60"
              disabled={!response || isBusy || phase === 'generating' || phase === 'solving'}
              onClick={resolveMaze}
              type="button"
            >
              Resolve
            </button>
          </div>

          <p className="min-h-6 text-sm font-medium text-[#5e5d59]">{status}</p>
        </aside>
      </div>
    </article>
  );
}

function NumberField({
  label,
  max,
  min,
  onChange,
  value,
}: {
  label: string;
  max: number;
  min: number;
  onChange: (value: number) => void;
  value: number;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-bold text-[#777267]">{label}</span>
      <input
        className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
        max={max}
        min={min}
        onChange={(event) => onChange(Number(event.target.value))}
        type="number"
        value={value}
      />
    </label>
  );
}

function TupleField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-bold text-[#777267]">{label}</span>
      <input
        className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 font-mono text-sm text-[#30302e] outline-none transition focus:border-[#c96442]"
        onChange={(event) => onChange(event.target.value)}
        placeholder="(row, col)"
        type="text"
        value={value}
      />
    </label>
  );
}

function SelectField({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
  value: string;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-bold text-[#777267]">{label}</span>
      <select
        className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map(([optionValue, labelText]) => (
          <option key={optionValue} value={optionValue}>
            {labelText}
          </option>
        ))}
      </select>
    </label>
  );
}

function Toggle({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: boolean) => void;
  value: boolean;
}) {
  return (
    <label className="flex min-h-11 items-center justify-between gap-3 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-sm font-bold text-[#777267]">
      {label}
      <input
        checked={value}
        className="h-4 w-4 accent-[#c96442]"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <span className="min-w-24 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-2 text-center">
      <b className="text-[#171715]">{value}</b> {label}
    </span>
  );
}

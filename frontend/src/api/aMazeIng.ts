export type MazeTheme = 'classic' | 'midnight' | 'forest' | 'ember';
export type GenerateAlgorithm = 'backtracking' | 'binary_tree' | 'sidewinder' | 'prim';
export type SolveAlgorithm = 'astar' | 'bfs' | 'dfs';
export type Direction = 'north' | 'east' | 'south' | 'west';

export type Walls = Record<Direction, boolean>;

export type MazeCell = {
  row: number;
  col: number;
  blocked: boolean;
  walls: Walls;
};

export type MazeStep = {
  kind: 'carve' | 'extra';
  from: { row: number; col: number };
  to: { row: number; col: number };
  direction: Direction;
};

export type MazeResponse = {
  cells: MazeCell[];
  generation_steps: MazeStep[];
  solve_steps: Array<{ row: number; col: number }>;
  path: Array<{ row: number; col: number }>;
  stats: {
    width: number;
    height: number;
    cells: number;
    generation_steps: number;
    visited_steps: number;
    path_length: number;
  };
};

export type MazeSolveResponse = {
  solve_steps: MazeResponse['solve_steps'];
  path: MazeResponse['path'];
  stats: {
    visited_steps: number;
    path_length: number;
  };
};

export type MazeGeneratePayload = {
  display_42: boolean;
  entry: { row: number; col: number };
  exit: { row: number; col: number };
  generate_algorithm: GenerateAlgorithm;
  height: number;
  perfect: boolean;
  seed: number;
  solve_algorithm: SolveAlgorithm;
  theme: MazeTheme;
  width: number;
};

export type MazeSolvePayload = {
  cells: MazeCell[];
  entry: { row: number; col: number };
  exit: { row: number; col: number };
  height: number;
  solve_algorithm: SolveAlgorithm;
  width: number;
};

const apiBase = '/api/projects/a-maze-ing';

export async function generateMaze(payload: MazeGeneratePayload) {
  const response = await fetch(`${apiBase}/generate`, {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  const data = (await response.json()) as MazeResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not generate the maze.');
  return data;
}

export async function solveMaze(payload: MazeSolvePayload) {
  const response = await fetch(`${apiBase}/solve`, {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  const data = (await response.json()) as MazeSolveResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not solve the maze.');
  return data;
}

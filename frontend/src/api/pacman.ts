export type PacmanScorePayload = {
  player_name: string;
  score: number;
  elapsed_seconds: number;
  level_reached: number;
  completed: boolean;
};

export type PacmanScore = PacmanScorePayload & {
  id: number;
  created_at: string;
};

export type PacmanLevelConfig = {
  width: number;
  height: number;
  seed: number | null;
};

export type PacmanPointsConfig = {
  pacgum: number;
  super_pacgum: number;
  ghost: number;
};

export type PacmanConfig = {
  levels: PacmanLevelConfig[];
  level_max_time: number;
  lives: number;
  pacgum: number;
  points: PacmanPointsConfig;
  window: {
    width: number;
    height: number;
    fps: number;
  };
};

export type PacmanCell = {
  row: number;
  col: number;
  walls: number;
  is_42_pattern: boolean;
};

export type PacmanPosition = {
  row: number;
  col: number;
};

export type PacmanGhostInit = PacmanPosition & {
  home_row: number;
  home_col: number;
  state: string;
};

export type PacmanCollectible = PacmanPosition & {
  points: number;
};

export type PacmanLevel = {
  level_index: number;
  width: number;
  height: number;
  seed: number | null;
  time_limit: number;
  lives: number;
  pacgum_count: number;
  points: PacmanPointsConfig;
  cells: PacmanCell[][];
  player: PacmanPosition;
  ghosts: PacmanGhostInit[];
  pacgums: PacmanCollectible[];
  super_pacgums: PacmanCollectible[];
};

export async function fetchPacmanConfig() {
  const response = await fetch('/api/projects/pacman/config');
  await assertJsonResponse(response, 'Pac-Man config');
  const data = (await response.json()) as PacmanConfig & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not load Pac-Man config.');
  return data;
}

export async function fetchPacmanLevel(levelIndex: number) {
  const response = await fetch(`/api/projects/pacman/levels/${levelIndex}`);
  await assertJsonResponse(response, 'Pac-Man level');
  const data = (await response.json()) as PacmanLevel & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not load Pac-Man level.');
  return data;
}

export async function fetchPacmanScores(limit = 10) {
  const response = await fetch(`/api/projects/pacman/scores?limit=${limit}`);
  await assertJsonResponse(response, 'Pac-Man leaderboard');
  const data = (await response.json()) as { detail?: string; scores?: PacmanScore[] };
  if (!response.ok) throw new Error(data.detail ?? 'Could not load Pac-Man scores.');
  return data.scores ?? [];
}

export async function submitPacmanScore(payload: PacmanScorePayload) {
  const response = await fetch('/api/projects/pacman/scores', {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  await assertJsonResponse(response, 'Pac-Man score submission');
  const data = (await response.json()) as PacmanScore & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not submit Pac-Man score.');
  return data;
}

async function assertJsonResponse(response: Response, label: string) {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) return;
  const text = await response.text();
  const preview = text.replace(/\s+/g, ' ').trim().slice(0, 160);
  throw new Error(`${label} returned HTTP ${response.status} with a non-JSON response. ${preview}`);
}

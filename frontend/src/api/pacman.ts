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

export type PacmanActorPosition = {
  row: number;
  col: number;
  pos_row: number;
  pos_col: number;
  direction: string;
};

export type PacmanGhostSnapshot = PacmanActorPosition & {
  home_row: number;
  home_col: number;
  state: string;
};

export type PacmanRunSnapshot = {
  run_id: string;
  player_name: string;
  status: 'playing' | 'paused' | 'won' | 'lost';
  status_text: string;
  completed: boolean;
  score_eligible: boolean;
  cheat_mode: boolean;
  cheat_used: boolean;
  level: number;
  level_index: number;
  level_count: number;
  score: number;
  lives: number;
  time_left: number;
  elapsed_seconds: number;
  width: number;
  height: number;
  seed: number | null;
  points: PacmanPointsConfig;
  cells: PacmanCell[][];
  player: PacmanActorPosition;
  ghosts: PacmanGhostSnapshot[];
  pacgums: PacmanCollectible[];
  super_pacgums: PacmanCollectible[];
};

export type PacmanRunFrame = Omit<PacmanRunSnapshot, 'width' | 'height' | 'seed' | 'points' | 'cells'>;

export type PacmanStreamMessage =
  | { kind: 'snapshot'; data: PacmanRunSnapshot }
  | { kind: 'frame'; data: PacmanRunFrame }
  | { kind: 'error'; detail: string };

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

export async function startPacmanRun(payload: { player_name: string; cheat_mode: boolean }) {
  const response = await fetch('/api/projects/pacman/runs', {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  await assertJsonResponse(response, 'Pac-Man run start');
  const data = (await response.json()) as PacmanRunSnapshot & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not start Pac-Man run.');
  return data;
}

export async function updatePacmanRunInput(
  runId: string,
  payload: { direction?: string; paused?: boolean; cheat_mode?: boolean },
) {
  const response = await fetch(`/api/projects/pacman/runs/${runId}/input`, {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  await assertJsonResponse(response, 'Pac-Man input');
  const data = (await response.json()) as PacmanRunSnapshot & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not update Pac-Man input.');
  return data;
}

export async function tickPacmanRun(runId: string, deltaSeconds: number) {
  const response = await fetch(`/api/projects/pacman/runs/${runId}/tick`, {
    body: JSON.stringify({ delta_seconds: deltaSeconds }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  await assertJsonResponse(response, 'Pac-Man tick');
  const data = (await response.json()) as PacmanRunSnapshot & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not update Pac-Man run.');
  return data;
}

export async function restartPacmanRun(runId: string, payload?: { player_name: string; cheat_mode: boolean }) {
  const response = await fetch(`/api/projects/pacman/runs/${runId}/restart`, {
    body: payload ? JSON.stringify(payload) : undefined,
    headers: payload ? { 'Content-Type': 'application/json' } : undefined,
    method: 'POST',
  });
  await assertJsonResponse(response, 'Pac-Man restart');
  const data = (await response.json()) as PacmanRunSnapshot & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not restart Pac-Man run.');
  return data;
}

export async function submitPacmanRunScore(runId: string) {
  const response = await fetch(`/api/projects/pacman/runs/${runId}/scores`, { method: 'POST' });
  await assertJsonResponse(response, 'Pac-Man score submission');
  const data = (await response.json()) as PacmanScore & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not submit score.');
  return data;
}

export function pacmanStreamUrl(runId: string) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/projects/pacman/runs/${runId}/stream`;
}

async function assertJsonResponse(response: Response, label: string) {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) return;
  const text = await response.text();
  const preview = text.replace(/\s+/g, ' ').trim().slice(0, 160);
  throw new Error(`${label} returned HTTP ${response.status} with a non-JSON response. ${preview}`);
}

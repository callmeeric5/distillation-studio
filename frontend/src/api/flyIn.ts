export type FlyInDifficulty = 'easy' | 'medium' | 'hard' | 'challenger';
export type FlyInZoneType = 'normal' | 'blocked' | 'restricted' | 'priority';
export type FlyInZoneRole = 'start' | 'end' | 'normal';

export type FlyInMapSummary = {
  difficulty: FlyInDifficulty;
  filename: string;
  name: string;
  path: string;
};

export type FlyInMapListResponse = {
  maps: Record<FlyInDifficulty, FlyInMapSummary[]>;
};

export type FlyInZone = {
  name: string;
  position: { x: number; y: number };
  zone_type: FlyInZoneType;
  color: string | null;
  max_drones: number;
  role: FlyInZoneRole;
};

export type FlyInConnection = {
  source: string;
  target: string;
  max_link_capacity: number;
};

export type FlyInAssignment = {
  drone_id: number;
  path: string[];
  path_index: number;
};

export type FlyInMove = {
  drone_id: number;
  from_zone: string;
  to_zone: string;
  duration: number;
  started_turn: number;
  arrives_turn: number;
  reason: string;
};

export type FlyInWaiting = {
  drone_id: number;
  zone: string;
  next_zone: string | null;
  reason: string;
};

export type FlyInTurn = {
  turn: number;
  moves: FlyInMove[];
  waiting: FlyInWaiting[];
  formatted: string;
};

export type FlyInSimulation = {
  map: FlyInMapSummary;
  zones: FlyInZone[];
  connections: FlyInConnection[];
  assignments: FlyInAssignment[];
  turns: FlyInTurn[];
  stats: {
    drones: number;
    zones: number;
    connections: number;
    turns: number;
    paths: number;
    start: string;
    end: string;
  };
};

const apiBase = '/api/projects/fly-in';

export async function listFlyInMaps() {
  const response = await fetch(`${apiBase}/maps`);
  const data = (await response.json()) as FlyInMapListResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not load Fly_In maps.');
  return data;
}

export async function loadFlyInSimulation(difficulty: FlyInDifficulty, filename: string) {
  const response = await fetch(
    `${apiBase}/maps/${encodeURIComponent(difficulty)}/${encodeURIComponent(filename)}/simulation`,
  );
  const data = (await response.json()) as FlyInSimulation & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not run Fly_In simulation.');
  return data;
}

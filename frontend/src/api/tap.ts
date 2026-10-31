export type TapRoomMeta = {
  name: string;
  description: string;
  exits: Record<string, string>;
};

export type TapWorld = {
  start_room: string;
  rooms: Record<string, TapRoomMeta>;
  items: Record<string, { name: string; description: string }>;
  npcs: Record<string, { name: string; description: string; hostile: boolean; quest: string | null }>;
  quests: Record<string, { description: string; giver: string; reward: string }>;
};

export type TapServerMessage =
  | { kind: 'protocol'; line: string }
  | { kind: 'gateway_error'; detail: string }
  | { kind: 'disconnected'; detail: string };

export type TapLook = {
  room: TapRoomMeta & { id: string };
  players: string[];
  items: string[];
  npcs: string[];
};

export type TapQuest = {
  quest_id: string;
  description: string;
  reward: string;
  status: 'active' | 'ready_to_complete' | 'completed';
  progress: string;
};

export async function fetchTapWorld() {
  const response = await fetch('/api/projects/tap/world');
  const data = (await response.json()) as TapWorld & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not load the TAP world.');
  return data;
}

export function tapSessionUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/projects/tap/session`;
}

export function sendTapCommand(socket: WebSocket, line: string) {
  socket.send(JSON.stringify({ kind: 'command', line }));
}

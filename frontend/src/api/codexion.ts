export type CodexionScheduler = 'FIFO' | 'EDF';
export type CodexionCoderState = 'idle' | 'compiling' | 'debugging' | 'refactoring' | 'burned_out' | 'complete';
export type CodexionDongleState = 'available' | 'in_use' | 'cooldown';
export type CodexionEventKind =
  | 'dongle_taken'
  | 'compiling'
  | 'debugging'
  | 'refactoring'
  | 'burned_out'
  | 'completed'
  | 'log';

export type CodexionConfig = {
  number_of_coders: number;
  time_to_burnout: number;
  time_to_compile: number;
  time_to_debug: number;
  time_to_refactor: number;
  number_of_compiles_required: number;
  dongle_cooldown: number;
  scheduler: CodexionScheduler;
};

export type CodexionLogEvent = {
  index: number;
  time: number;
  coder_id: number | null;
  kind: CodexionEventKind;
  message: string;
  raw: string;
};

export type CodexionCoderFrame = {
  id: number;
  state: CodexionCoderState;
  compiles_done: number;
  dongles: number[];
  deadline: number;
};

export type CodexionDongleFrame = {
  id: number;
  state: CodexionDongleState;
  holder: number | null;
  cooldown_until: number;
};

export type CodexionReplayFrame = {
  index: number;
  time: number;
  event: CodexionLogEvent | null;
  coders: CodexionCoderFrame[];
  dongles: CodexionDongleFrame[];
};

export type CodexionRunResponse = {
  config: CodexionConfig;
  events: CodexionLogEvent[];
  frames: CodexionReplayFrame[];
  raw_log: string[];
  stats: {
    outcome: 'completed' | 'burned_out';
    total_events: number;
    total_time: number;
    coders_completed: number;
    compiles_completed: number;
    scheduler: CodexionScheduler;
  };
};

const apiBase = '/api/projects/codexion';

export async function runCodexion(config: CodexionConfig) {
  const response = await fetch(`${apiBase}/run`, {
    body: JSON.stringify(config),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  const data = (await response.json()) as CodexionRunResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Codexion failed.');
  return data;
}

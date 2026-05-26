export type PushSwapAlgorithm = 'simple' | 'medium' | 'complex';

export type PushSwapRunResponse = {
  values: number[];
  algorithm: PushSwapAlgorithm;
  moves: string[];
  move_count: number;
};

export type PushSwapGenerateResponse = {
  values: number[];
};

const apiBase = '/api/projects/push-swap';

export async function generatePushSwapValues(
  size: number,
  minimum: number,
  maximum: number,
) {
  const response = await fetch(`${apiBase}/generate`, {
    body: JSON.stringify({ maximum, minimum, size }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  const data = (await response.json()) as PushSwapGenerateResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not generate values.');
  return data;
}

export async function runPushSwap(values: number[], algorithm: PushSwapAlgorithm) {
  const response = await fetch(`${apiBase}/run`, {
    body: JSON.stringify({ algorithm, values }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  const data = (await response.json()) as PushSwapRunResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'push_swap failed.');
  return data;
}

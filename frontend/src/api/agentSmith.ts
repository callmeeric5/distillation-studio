export type AgentProvider = 'openrouter' | 'groq';
export type AgentBenchmark = 'mbpp' | 'swebench';
export type AgentRunStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';

export type AgentOptions = {
  providers: Record<AgentProvider, {
    label: string;
    url: string;
    models: Array<{ id: string; label: string }>;
  }>;
  swebench_tasks: Array<{ id: string; repository: string; title: string }>;
  limits: Record<string, unknown>;
};

export type AgentStep = {
  step: number;
  llm_output: string;
  sandbox_input: string;
  sandbox_output: string;
  input_tokens: number;
  output_tokens: number;
  request_time_ms: number;
  retries: number;
};

export type AgentRun = {
  run_id: string;
  benchmark: AgentBenchmark;
  provider: AgentProvider;
  model: string;
  status: AgentRunStatus;
  queue_position: number | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  elapsed_seconds: number;
  iterations: number;
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  steps: AgentStep[];
  solution: string;
  error: string | null;
};

export type CreateAgentRun = {
  benchmark: AgentBenchmark;
  provider: AgentProvider;
  model: string;
  api_key: string;
  task_id?: string;
  task_definition?: string;
  function_definition?: string;
  test_imports?: string[];
  test_list?: string[];
};

async function jsonResponse<T>(response: Response, fallback: string): Promise<T> {
  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) throw new Error(fallback);
  const data = (await response.json()) as T & { detail?: string | Array<{ msg: string }> };
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join(' ')
      : data.detail;
    throw new Error(detail || fallback);
  }
  return data;
}

export async function getAgentOptions() {
  return jsonResponse<AgentOptions>(
    await fetch('/api/projects/agent-smith/options'),
    'Could not load Agent Smith options.',
  );
}

export async function createAgentRun(payload: CreateAgentRun) {
  return jsonResponse<{ run_id: string; status: 'queued' }>(
    await fetch('/api/projects/agent-smith/runs', {
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
    }),
    'Could not start Agent Smith.',
  );
}

export async function getAgentRun(runId: string, afterStep: number) {
  return jsonResponse<AgentRun>(
    await fetch(`/api/projects/agent-smith/runs/${runId}?after_step=${afterStep}`),
    'Could not refresh Agent Smith.',
  );
}

export async function cancelAgentRun(runId: string) {
  return jsonResponse<AgentRun>(
    await fetch(`/api/projects/agent-smith/runs/${runId}`, { method: 'DELETE' }),
    'Could not cancel Agent Smith.',
  );
}

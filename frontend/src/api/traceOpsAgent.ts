export type TraceProvider = 'openai' | 'gemini' | 'anthropic' | 'deepseek';

export type DiagnosePayload = {
  provider: TraceProvider;
  model: string;
  api_key: string;
  incident: string;
  logs: string;
  max_iterations: number;
};

export type DiagnoseResponse = {
  summary: string;
  root_cause: string;
  evidence: string[];
  recommended_actions: string[];
  confidence: string;
  reasoning_steps: string[];
  tool_calls: string[];
  raw_text: string;
};

export const providerLabels: Record<TraceProvider, string> = {
  gemini: 'Gemini',
  openai: 'ChatGPT / OpenAI',
  anthropic: 'Claude / Anthropic',
  deepseek: 'DeepSeek',
};

export const providerModels: Record<TraceProvider, string[]> = {
  gemini: ['gemini-2.5-flash-lite', 'gemini-2.5-flash'],
  openai: ['gpt-4o-mini', 'gpt-4.1-mini'],
  anthropic: ['claude-3-5-haiku-latest', 'claude-3-5-sonnet-latest'],
  deepseek: ['deepseek-chat', 'deepseek-reasoner'],
};

export async function diagnoseTraceOps(payload: DiagnosePayload) {
  const response = await fetch('/api/projects/trace-ops-agent/diagnose', {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });

  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) {
    const text = await response.text();
    const preview = text.replace(/\s+/g, ' ').trim().slice(0, 160);
    throw new Error(
      response.ok
        ? 'Trace-Ops API returned a non-JSON response. Check that FastAPI is running on port 8000.'
        : `Trace-Ops API proxy returned HTTP ${response.status}. ${preview}`,
    );
  }

  const data = (await response.json()) as DiagnoseResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not diagnose the incident.');
  return data;
}

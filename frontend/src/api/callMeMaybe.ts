export type FunctionDefinition = {
  fn_name: string;
  args_names: string[];
  args_types: Record<string, 'str' | 'float' | 'int' | 'bool'>;
  return_type: 'str' | 'float' | 'int' | 'bool';
};

export type CallMeMaybePayload = {
  prompt: string;
  functions_definition: FunctionDefinition[];
};

export type CallMeMaybeResponse = {
  prompt: string;
  name: string;
  parameters: Record<string, string | number | boolean>;
};

export async function runCallMeMaybe(payload: CallMeMaybePayload) {
  const response = await fetch('/api/projects/call-me-maybe/run', {
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
        ? 'Call_Me_Maybe API returned a non-JSON response.'
        : `Call_Me_Maybe API proxy returned HTTP ${response.status}. ${preview}`,
    );
  }

  const data = (await response.json()) as CallMeMaybeResponse & { detail?: string };
  if (!response.ok) throw new Error(data.detail ?? 'Could not run Call_Me_Maybe.');
  return data;
}

import { useState } from 'react';

import {
  runCallMeMaybe,
  type CallMeMaybeResponse,
  type FunctionDefinition,
} from './api/callMeMaybe';

const samplePrompt = "Substitute the digits in the string 'Hello 34 I am 233 years old' with 'NUMBERS'";

const builtInFunctions: FunctionDefinition[] = [
  {
    fn_name: 'fn_add_numbers',
    args_names: ['a', 'b'],
    args_types: { a: 'float', b: 'float' },
    return_type: 'float',
  },
  {
    fn_name: 'fn_get_square_root',
    args_names: ['a'],
    args_types: { a: 'float' },
    return_type: 'float',
  },
  {
    fn_name: 'fn_greet',
    args_names: ['name'],
    args_types: { name: 'str' },
    return_type: 'str',
  },
  {
    fn_name: 'fn_is_even',
    args_names: ['n'],
    args_types: { n: 'int' },
    return_type: 'bool',
  },
  {
    fn_name: 'fn_multiply_numbers',
    args_names: ['a', 'b'],
    args_types: { a: 'float', b: 'float' },
    return_type: 'float',
  },
  {
    fn_name: 'fn_reverse_string',
    args_names: ['s'],
    args_types: { s: 'str' },
    return_type: 'str',
  },
  {
    fn_name: 'fn_substitute_string_with_regex',
    args_names: ['source_string', 'regex', 'replacement'],
    args_types: {
      source_string: 'str',
      regex: 'str',
      replacement: 'str',
    },
    return_type: 'str',
  },
];

const sampleAdditionalFunctions = JSON.stringify(
  [
    {
      fn_name: 'fn_extract_email',
      args_names: ['source_string'],
      args_types: { source_string: 'str' },
      return_type: 'str',
    },
  ],
  null,
  2,
);

export function CallMeMaybeStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const [prompt, setPrompt] = useState(samplePrompt);
  const [additionalFunctionConfig, setAdditionalFunctionConfig] = useState(sampleAdditionalFunctions);
  const [result, setResult] = useState<CallMeMaybeResponse | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const [status, setStatus] = useState('Edit the prompt or add extra functions, then run selection.');
  const [isBusy, setIsBusy] = useState(false);
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);
  const canExpand = fullDescription && fullDescription !== description;

  async function run() {
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) {
      setStatus('Prompt is required.');
      return;
    }

    let parsedConfig: FunctionDefinition[];
    const trimmedFunctionConfig = additionalFunctionConfig.trim();
    try {
      const parsed = trimmedFunctionConfig ? (JSON.parse(trimmedFunctionConfig) as unknown) : [];
      if (!Array.isArray(parsed)) {
        setStatus('Additional function configuration must be a JSON array.');
        return;
      }
      parsedConfig = [...builtInFunctions, ...(parsed as FunctionDefinition[])];
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Additional function configuration is not valid JSON.');
      return;
    }

    setIsBusy(true);
    setResult(null);
    setDurationMs(null);
    setStatus('Running constrained function selection...');
    const startedAt = performance.now();
    try {
      const response = await runCallMeMaybe({
        prompt: trimmedPrompt,
        functions_definition: parsedConfig,
      });
      const elapsedMs = Math.round(performance.now() - startedAt);
      setResult(response);
      setDurationMs(elapsedMs);
      setStatus(`Function call generated in ${formatDuration(elapsedMs)}.`);
    } catch (error) {
      setDurationMs(Math.round(performance.now() - startedAt));
      setStatus(error instanceof Error ? error.message : 'Could not run Call_Me_Maybe.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <div className="grid min-h-[720px] lg:grid-cols-[minmax(0,1fr)_430px]">
        <section className="flex min-w-0 flex-col">
          <header className="border-b border-[#ece8dc] p-5 lg:p-7">
            <button
              className="mb-5 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#30302e] transition hover:bg-[#faf9f5]"
              onClick={onBack}
              type="button"
            >
              Back to gallery
            </button>
            <p className="text-sm font-semibold text-[#c96442]">42 project / function calling</p>
            <h3 className="mt-2 font-serif text-4xl leading-tight text-[#171715] sm:text-5xl">
              Call_Me_Maybe
            </h3>
            <p className="mt-5 text-lg leading-8 text-[#5e5d59]">
              {isDescriptionExpanded || !canExpand ? (fullDescription ?? description) : description}
            </p>
            {canExpand ? (
              <button
                className="mt-3 min-h-9 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 text-sm font-semibold text-[#8a4429] transition hover:bg-[#fffdf8]"
                onClick={() => setIsDescriptionExpanded((current) => !current)}
                type="button"
              >
                {isDescriptionExpanded ? 'Less' : 'More'}
              </button>
            ) : null}
          </header>

          <div className="grid gap-5 p-5 lg:p-7">
            <section className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
              <h4 className="text-sm font-bold uppercase text-[#8b8174]">Selected function</h4>
              <p className="mt-2 break-words font-mono text-lg font-semibold text-[#30302e]">
                {result?.name ?? 'Waiting for selection.'}
              </p>
              <p className="mt-2 text-sm font-medium text-[#777267]">
                Duration: {durationMs === null ? 'Waiting for run.' : formatDuration(durationMs)}
              </p>
            </section>

            <section className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
              <h4 className="text-sm font-bold uppercase text-[#8b8174]">Parameters</h4>
              {result ? (
                <dl className="mt-3 grid gap-3">
                  {Object.entries(result.parameters).map(([key, value]) => (
                    <div
                      className="grid gap-1 rounded-lg bg-[#fffdf8] p-3 sm:grid-cols-[150px_minmax(0,1fr)]"
                      key={key}
                    >
                      <dt className="break-words font-mono text-sm font-bold text-[#8a4429]">{key}</dt>
                      <dd className="break-words font-mono text-sm text-[#30302e]">
                        {JSON.stringify(value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <p className="mt-2 text-base leading-7 text-[#30302e]">Waiting for result.</p>
              )}
            </section>

            <section className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
              <h4 className="text-sm font-bold uppercase text-[#8b8174]">Raw output</h4>
              <pre className="mt-3 min-h-40 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-[#fffdf8] p-3 font-mono text-sm leading-6 text-[#30302e]">
                {result ? JSON.stringify(result, null, 2) : 'Waiting for result.'}
              </pre>
            </section>
          </div>
        </section>

        <aside className="flex flex-col gap-5 border-t border-[#ece8dc] bg-[#faf9f5] p-5 lg:border-l lg:border-t-0">
          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Prompt</span>
            <textarea
              className="min-h-28 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-3 text-sm leading-6 text-[#30302e] outline-none transition focus:border-[#c96442]"
              onChange={(event) => setPrompt(event.target.value)}
              value={prompt}
            />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Additional functions JSON</span>
            <span className="text-xs leading-5 text-[#777267]">
              {builtInFunctions.length} built-in functions are already loaded. Add more functions as a JSON array here.
            </span>
            <textarea
              className="min-h-[380px] rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-3 font-mono text-xs leading-5 text-[#30302e] outline-none transition focus:border-[#c96442]"
              onChange={(event) => setAdditionalFunctionConfig(event.target.value)}
              spellCheck={false}
              value={additionalFunctionConfig}
            />
          </label>

          <button
            className="min-h-11 rounded-lg bg-[#c96442] px-4 text-sm font-bold text-[#faf9f5] transition hover:bg-[#b65334] disabled:opacity-60"
            disabled={isBusy}
            onClick={run}
            type="button"
          >
            {isBusy ? 'Running...' : 'Generate function call'}
          </button>
          <p className="min-h-6 text-sm font-medium text-[#5e5d59]">{status}</p>
        </aside>
      </div>
    </article>
  );
}

function formatDuration(durationMs: number) {
  if (durationMs < 1000) return `${durationMs} ms`;
  return `${(durationMs / 1000).toFixed(2)} s`;
}

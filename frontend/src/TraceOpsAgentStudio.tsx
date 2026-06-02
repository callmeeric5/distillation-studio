import { useMemo, useState } from 'react';

import {
  diagnoseTraceOps,
  providerLabels,
  providerModels,
  type DiagnoseResponse,
  type TraceProvider,
} from './api/traceOpsAgent';

const sampleIncident =
  'Checkout latency spiked after a deployment. Users report intermittent payment failures and the order service is timing out.';

const sampleLogs = `[2026-06-02T08:10:12Z] ERROR order-service trace_id=trc-91 payment request timed out after 3000ms
[2026-06-02T08:10:13Z] WARN payment-service trace_id=trc-91 connection pool exhausted active=100 idle=0
[2026-06-02T08:10:14Z] ERROR order-service trace_id=trc-92 failed to reserve inventory after payment timeout
[2026-06-02T08:11:02Z] INFO api-gateway p95 latency=1840ms route=/checkout
[2026-06-02T08:11:33Z] ERROR payment-service trace_id=trc-94 database connection acquisition timeout`;

export function TraceOpsAgentStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const [provider, setProvider] = useState<TraceProvider>('gemini');
  const [model, setModel] = useState(providerModels.gemini[0]);
  const [apiKey, setApiKey] = useState('');
  const [incident, setIncident] = useState(sampleIncident);
  const [logs, setLogs] = useState(sampleLogs);
  const [maxIterations, setMaxIterations] = useState(6);
  const [result, setResult] = useState<DiagnoseResponse | null>(null);
  const [status, setStatus] = useState('Enter an API key, review the incident, then run the agent.');
  const [isBusy, setIsBusy] = useState(false);
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);

  const models = providerModels[provider];
  const canExpand = fullDescription && fullDescription !== description;
  const providerOptions = useMemo(() => Object.keys(providerLabels) as TraceProvider[], []);

  function updateProvider(nextProvider: TraceProvider) {
    setProvider(nextProvider);
    setModel(providerModels[nextProvider][0]);
  }

  async function diagnose() {
    if (!apiKey.trim()) {
      setStatus('API key is required for the selected provider.');
      return;
    }
    if (!incident.trim()) {
      setStatus('Incident description is required.');
      return;
    }

    setIsBusy(true);
    setResult(null);
    setStatus('Running...');
    try {
      const diagnosis = await diagnoseTraceOps({
        api_key: apiKey.trim(),
        incident,
        logs,
        max_iterations: maxIterations,
        model,
        provider,
      });
      setResult(diagnosis);
      setStatus('Diagnosis complete.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not diagnose the incident.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <div className="grid min-h-[720px] lg:grid-cols-[minmax(0,1fr)_390px]">
        <section className="flex min-w-0 flex-col">
          <header className="border-b border-[#ece8dc] p-5 lg:p-7">
            <button
              className="mb-5 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#30302e] transition hover:bg-[#faf9f5]"
              onClick={onBack}
              type="button"
            >
              Back to gallery
            </button>
            <p className="text-sm font-semibold text-[#c96442]">Fun project / LLM ops agent</p>
            <h3 className="mt-2 font-serif text-4xl leading-tight text-[#171715] sm:text-5xl">
              Trace_Ops_Agent
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
            <ResultSection title="Summary" value={result?.summary} />
            <ResultSection title="Root cause" value={result?.root_cause} />
            <ResultList items={result?.evidence ?? []} title="Evidence" />
            <ResultList items={result?.recommended_actions ?? []} title="Recommended actions" />
            <ResultSection title="Confidence" value={result?.confidence} />
            {result ? (
              <details className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
                <summary className="cursor-pointer text-sm font-bold text-[#8a4429]">
                  Agent trace · {result.tool_calls.length} tool events
                </summary>
                <div className="mt-4 grid gap-4">
                  <TraceList items={result.reasoning_steps} title="Reasoning" />
                  <TraceList items={result.tool_calls} title="Tools" />
                </div>
              </details>
            ) : null}
            {result?.raw_text ? (
              <details className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
                <summary className="cursor-pointer text-sm font-bold text-[#8a4429]">
                  Raw final response
                </summary>
                <pre className="mt-3 whitespace-pre-wrap text-sm leading-6 text-[#5e5d59]">
                  {result.raw_text}
                </pre>
              </details>
            ) : null}
          </div>
        </section>

        <aside className="flex flex-col gap-5 border-t border-[#ece8dc] bg-[#faf9f5] p-5 lg:border-l lg:border-t-0">
          <SelectField
            label="Provider"
            onChange={(value) => updateProvider(value as TraceProvider)}
            options={providerOptions.map((option) => [option, providerLabels[option]])}
            value={provider}
          />
          <SelectField
            label="Model"
            onChange={setModel}
            options={models.map((option) => [option, option])}
            value={model}
          />
          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">API key</span>
            <input
              autoComplete="off"
              className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="Used for this request only"
              type="password"
              value={apiKey}
            />
          </label>
          <TextAreaField label="Incident" onChange={setIncident} rows={7} value={incident} />
          <TextAreaField label="Logs" onChange={setLogs} rows={12} value={logs} />
          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Max agent steps</span>
            <input
              className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
              max={12}
              min={1}
              onChange={(event) => setMaxIterations(Number(event.target.value))}
              type="number"
              value={maxIterations}
            />
          </label>
          <button
            className="min-h-11 rounded-lg bg-[#c96442] px-4 text-sm font-bold text-[#faf9f5] transition hover:bg-[#b65334] disabled:opacity-60"
            disabled={isBusy}
            onClick={diagnose}
            type="button"
          >
            {isBusy ? 'Diagnosing...' : 'Diagnose'}
          </button>
          <p className="min-h-6 text-sm font-medium text-[#5e5d59]">{status}</p>
        </aside>
      </div>
    </article>
  );
}

function TraceList({ items, title }: { items: string[]; title: string }) {
  return (
    <section>
      <h4 className="text-sm font-bold uppercase text-[#8b8174]">{title}</h4>
      {items.length > 0 ? (
        <ol className="mt-2 grid gap-2 text-sm leading-6 text-[#30302e]">
          {items.map((item, index) => (
            <li className="rounded-lg bg-[#fffdf8] p-3" key={`${title}-${index}`}>
              {item}
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-2 text-sm leading-6 text-[#5e5d59]">No trace entries returned.</p>
      )}
    </section>
  );
}

function ResultSection({ title, value }: { title: string; value?: string }) {
  return (
    <section className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
      <h4 className="text-sm font-bold uppercase text-[#8b8174]">{title}</h4>
      <p className="mt-2 text-base leading-7 text-[#30302e]">{value || 'Waiting for diagnosis.'}</p>
    </section>
  );
}

function ResultList({ items, title }: { items: string[]; title: string }) {
  return (
    <section className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
      <h4 className="text-sm font-bold uppercase text-[#8b8174]">{title}</h4>
      {items.length > 0 ? (
        <ul className="mt-2 grid gap-2 text-base leading-7 text-[#30302e]">
          {items.map((item) => (
            <li key={item}>- {item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-base leading-7 text-[#30302e]">Waiting for diagnosis.</p>
      )}
    </section>
  );
}

function SelectField({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
  value: string;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-bold text-[#777267]">{label}</span>
      <select
        className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map(([optionValue, labelText]) => (
          <option key={optionValue} value={optionValue}>
            {labelText}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextAreaField({
  label,
  onChange,
  rows,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  rows: number;
  value: string;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-bold text-[#777267]">{label}</span>
      <textarea
        className="rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-3 font-mono text-sm leading-6 text-[#30302e] outline-none transition focus:border-[#c96442]"
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
        value={value}
      />
    </label>
  );
}

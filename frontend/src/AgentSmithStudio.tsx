import { useEffect, useMemo, useRef, useState } from 'react';

import {
  cancelAgentRun,
  createAgentRun,
  getAgentOptions,
  getAgentRun,
  type AgentBenchmark,
  type AgentOptions,
  type AgentProvider,
  type AgentRun,
  type AgentRunStatus,
  type AgentStep,
} from './api/agentSmith';
import { CollapsibleDescription } from './components/CollapsibleDescription';

const terminalStatuses: AgentRunStatus[] = ['succeeded', 'failed', 'cancelled'];
const sampleTask = 'Write a function that counts the vowels in a string, ignoring case.';
const sampleFunction = 'def count_vowels(text: str) -> int';
const sampleTests = `assert count_vowels("Agent Smith") == 3
assert count_vowels("rhythm") == 0
assert count_vowels("AEIOU") == 5`;

export function AgentSmithStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const [options, setOptions] = useState<AgentOptions | null>(null);
  const [benchmark, setBenchmark] = useState<AgentBenchmark>('mbpp');
  const [provider, setProvider] = useState<AgentProvider>('openrouter');
  const [model, setModel] = useState('openai/gpt-4.1-nano');
  const [apiKey, setApiKey] = useState('');
  const [taskDefinition, setTaskDefinition] = useState(sampleTask);
  const [functionDefinition, setFunctionDefinition] = useState(sampleFunction);
  const [testImports, setTestImports] = useState('');
  const [tests, setTests] = useState(sampleTests);
  const [sweTask, setSweTask] = useState('django__django-11066');
  const [runId, setRunId] = useState<string | null>(null);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [message, setMessage] = useState('Loading Agent Smith options...');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const lastStep = useRef(0);

  useEffect(() => {
    let active = true;
    getAgentOptions()
      .then((value) => {
        if (!active) return;
        setOptions(value);
        const firstTask = value.swebench_tasks[0]?.id;
        if (firstTask) setSweTask(firstTask);
        setMessage('Choose a task and provide a request-only API key.');
      })
      .catch((error) => active && setMessage(error instanceof Error ? error.message : 'Could not load options.'));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!runId) return;
    let stopped = false;
    let timer: number | undefined;
    async function poll() {
      try {
        const value = await getAgentRun(runId as string, lastStep.current);
        if (stopped) return;
        if (value.steps.length) {
          setSteps((current) => [...current, ...value.steps]);
          lastStep.current = Math.max(lastStep.current, ...value.steps.map((step) => step.step));
        }
        setRun(value);
        setMessage(statusMessage(value));
        if (!terminalStatuses.includes(value.status)) timer = window.setTimeout(poll, 1500);
      } catch (error) {
        if (!stopped) setMessage(error instanceof Error ? error.message : 'Could not refresh the run.');
      }
    }
    void poll();
    return () => {
      stopped = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [runId]);

  const models = useMemo(() => options?.providers[provider]?.models ?? [], [options, provider]);
  const running = Boolean(run && !terminalStatuses.includes(run.status));

  function changeProvider(next: AgentProvider) {
    setProvider(next);
    const firstModel = options?.providers[next]?.models[0]?.id;
    if (firstModel) setModel(firstModel);
  }

  async function startRun() {
    if (!apiKey.trim()) {
      setMessage('API key is required for the selected provider.');
      return;
    }
    setIsSubmitting(true);
    setRun(null);
    setSteps([]);
    setRunId(null);
    lastStep.current = 0;
    try {
      const created = await createAgentRun({
        api_key: apiKey.trim(),
        benchmark,
        function_definition: benchmark === 'mbpp' ? functionDefinition : undefined,
        model,
        provider,
        task_definition: benchmark === 'mbpp' ? taskDefinition : undefined,
        task_id: benchmark === 'swebench' ? sweTask : undefined,
        test_imports: benchmark === 'mbpp' ? lines(testImports) : undefined,
        test_list: benchmark === 'mbpp' ? lines(tests) : undefined,
      });
      setRunId(created.run_id);
      setMessage('Queued. The API key is held in memory for this run only.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not start Agent Smith.');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function cancel() {
    if (!runId) return;
    try {
      const value = await cancelAgentRun(runId);
      setRun(value);
      setMessage('Run cancelled.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not cancel the run.');
    }
  }

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <header className="border-b border-[#ece8dc] p-5 lg:p-7">
        <button className="mb-5 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#30302e]" onClick={onBack} type="button">
          Back to gallery
        </button>
        <p className="text-sm font-semibold text-[#c96442]">Fun project / code agent</p>
        <h3 className="mt-2 font-serif text-4xl text-[#171715] sm:text-5xl">Agent_Smith</h3>
        <CollapsibleDescription className="mt-5" fullText={fullDescription ?? description} previewText={description} />
      </header>

      <div className="grid min-h-[720px] lg:grid-cols-[minmax(0,1fr)_390px]">
        <section className="grid content-start gap-5 p-5 lg:p-7">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Metric label="Status" value={run?.status ?? 'idle'} />
            <Metric label="Elapsed" value={`${run?.elapsed_seconds ?? 0}s`} />
            <Metric label="Iterations" value={String(run?.iterations ?? steps.length)} />
            <Metric label="Tokens" value={String((run?.total_input_tokens ?? 0) + (run?.total_output_tokens ?? 0))} />
          </div>

          {run?.queue_position ? <p className="rounded-xl bg-[#f4f1e8] p-4 text-sm text-[#5e5d59]">Queue position: {run.queue_position}</p> : null}
          {steps.length ? (
            <div className="grid gap-3">
              {steps.map((step) => <StepCard key={step.step} step={step} />)}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-[#d8d1c2] bg-[#f4f1e8] p-8 text-center text-[#5e5d59]">
              The Thought → Code → Observation trace will appear here.
            </div>
          )}

          {run?.solution ? (
            <section className="rounded-xl border border-[#c9d1bd] bg-[#eef3e8] p-4">
              <h4 className="text-sm font-bold uppercase text-[#415234]">Final {benchmark === 'mbpp' ? 'source' : 'patch'}</h4>
              <pre className="mt-3 max-h-[520px] overflow-auto whitespace-pre-wrap text-sm leading-6 text-[#30302e]">{run.solution}</pre>
            </section>
          ) : null}
          {run?.error ? <p className="rounded-xl border border-[#dec6b5] bg-[#fbede5] p-4 text-sm text-[#8a4429]">{run.error}</p> : null}
        </section>

        <aside className="flex flex-col gap-5 border-t border-[#ece8dc] bg-[#faf9f5] p-5 lg:border-l lg:border-t-0">
          <div className="grid grid-cols-2 gap-2">
            {(['mbpp', 'swebench'] as AgentBenchmark[]).map((value) => (
              <button className={`min-h-10 rounded-lg text-sm font-bold ${benchmark === value ? 'bg-[#30302e] text-[#faf9f5]' : 'border border-[#e8e3d6] bg-[#fffdf8] text-[#5e5d59]'}`} disabled={running} key={value} onClick={() => setBenchmark(value)} type="button">
                {value === 'mbpp' ? 'MBPP' : 'SWE-bench'}
              </button>
            ))}
          </div>
          <Select label="Provider" onChange={(value) => changeProvider(value as AgentProvider)} options={(Object.keys(options?.providers ?? {}) as AgentProvider[]).map((value) => [value, options?.providers[value].label ?? value])} value={provider} />
          <Select label="Model" onChange={setModel} options={models.map((value) => [value.id, value.label])} value={model} />
          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">API key</span>
            <input autoComplete="off" className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 outline-none focus:border-[#c96442]" onChange={(event) => setApiKey(event.target.value)} placeholder="Used for this run only" type="password" value={apiKey} />
          </label>

          {benchmark === 'mbpp' ? (
            <>
              <TextArea label="Task" onChange={setTaskDefinition} rows={4} value={taskDefinition} />
              <TextArea label="Function signature" onChange={setFunctionDefinition} rows={2} value={functionDefinition} />
              <TextArea label="Imports · one per line" onChange={setTestImports} rows={2} value={testImports} />
              <TextArea label="Tests · one per line" onChange={setTests} rows={5} value={tests} />
            </>
          ) : (
            <Select label="Built-in task" onChange={setSweTask} options={(options?.swebench_tasks ?? []).map((task) => [task.id, `${task.repository} · ${task.title}`])} value={sweTask} />
          )}

          <div className="flex gap-3">
            <button className="min-h-11 flex-1 rounded-lg bg-[#c96442] px-4 text-sm font-bold text-[#faf9f5] disabled:opacity-60" disabled={!options || isSubmitting || running} onClick={startRun} type="button">
              {isSubmitting ? 'Queuing...' : 'Run agent'}
            </button>
            {running ? <button className="min-h-11 rounded-lg border border-[#dec6b5] px-4 text-sm font-bold text-[#8a4429]" onClick={cancel} type="button">Cancel</button> : null}
          </div>
          <p className="min-h-12 text-sm leading-6 text-[#5e5d59]">{message}</p>
        </aside>
      </div>
    </article>
  );
}

function lines(value: string) { return value.split('\n').map((item) => item.trim()).filter(Boolean); }
function statusMessage(run: AgentRun) {
  if (run.status === 'queued') return `Queued${run.queue_position ? ` at position ${run.queue_position}` : ''}.`;
  if (run.status === 'running') return `Running iteration ${run.iterations + 1}...`;
  if (run.status === 'succeeded') return 'Agent completed successfully.';
  return run.error || `Run ${run.status}.`;
}
function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-3"><div className="text-xs font-bold uppercase text-[#8b8174]">{label}</div><div className="mt-1 truncate font-semibold text-[#171715]">{value}</div></div>;
}
function StepCard({ step }: { step: AgentStep }) {
  return <details className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4" open={step.step === 1}><summary className="cursor-pointer font-bold text-[#8a4429]">Step {step.step} · {step.input_tokens + step.output_tokens} tokens · {Math.round(step.request_time_ms)} ms</summary><div className="mt-4 grid gap-4"><Trace title="Thought / model output" value={step.llm_output} /><Trace title="Code" value={step.sandbox_input} /><Trace title="Observation" value={step.sandbox_output} /></div></details>;
}
function Trace({ title, value }: { title: string; value: string }) {
  return <section><h5 className="text-xs font-bold uppercase text-[#8b8174]">{title}</h5><pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-[#fffdf8] p-3 text-xs leading-5 text-[#30302e]">{value || 'No content.'}</pre></section>;
}
function Select({ label, onChange, options, value }: { label: string; onChange: (value: string) => void; options: Array<[string, string]>; value: string }) {
  return <label className="grid gap-2"><span className="text-sm font-bold text-[#777267]">{label}</span><select className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none focus:border-[#c96442]" onChange={(event) => onChange(event.target.value)} value={value}>{options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></label>;
}
function TextArea({ label, onChange, rows, value }: { label: string; onChange: (value: string) => void; rows: number; value: string }) {
  return <label className="grid gap-2"><span className="text-sm font-bold text-[#777267]">{label}</span><textarea className="rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-3 font-mono text-sm leading-6 text-[#30302e] outline-none focus:border-[#c96442]" onChange={(event) => onChange(event.target.value)} rows={rows} value={value} /></label>;
}

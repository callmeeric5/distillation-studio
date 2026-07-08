import { useEffect, useState, type Dispatch, type SetStateAction } from 'react';

import {
  runCodexion,
  type CodexionCoderFrame,
  type CodexionCoderState,
  type CodexionConfig,
  type CodexionDongleFrame,
  type CodexionRunResponse,
  type CodexionScheduler,
} from './api/codexion';
import { CollapsibleDescription } from './components/CollapsibleDescription';

const defaultConfig: CodexionConfig = {
  dongle_cooldown: 20,
  number_of_coders: 4,
  number_of_compiles_required: 3,
  scheduler: 'FIFO',
  time_to_burnout: 1200,
  time_to_compile: 120,
  time_to_debug: 120,
  time_to_refactor: 120,
};

const coderPalette: Record<CodexionCoderState, { fill: string; stroke: string; text: string }> = {
  burned_out: { fill: '#f3dfd2', stroke: '#8a4429', text: '#8a4429' },
  compiling: { fill: '#c96442', stroke: '#8a4429', text: '#fffdf8' },
  complete: { fill: '#e8eee0', stroke: '#49603b', text: '#49603b' },
  debugging: { fill: '#dfe8f0', stroke: '#36546d', text: '#28465f' },
  idle: { fill: '#fffdf8', stroke: '#8b8174', text: '#5e5d59' },
  refactoring: { fill: '#f4f1e8', stroke: '#8b8174', text: '#5e5d59' },
};

const donglePalette: Record<CodexionDongleFrame['state'], { fill: string; stroke: string; text: string }> = {
  available: { fill: '#fffdf8', stroke: '#8b8174', text: '#5e5d59' },
  cooldown: { fill: '#dfe8f0', stroke: '#36546d', text: '#28465f' },
  in_use: { fill: '#f3dfd2', stroke: '#c96442', text: '#8a4429' },
};

const stateLegend: Array<{ label: string; state: CodexionCoderState }> = [
  { label: 'compile', state: 'compiling' },
  { label: 'debug', state: 'debugging' },
  { label: 'refactor', state: 'refactoring' },
  { label: 'done', state: 'complete' },
  { label: 'burnout', state: 'burned_out' },
];

function updateNumber(
  field: keyof Omit<CodexionConfig, 'scheduler'>,
  value: string,
  setConfig: Dispatch<SetStateAction<CodexionConfig>>,
) {
  setConfig((current) => ({ ...current, [field]: Number(value) }));
}

export function CodexionStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const [config, setConfig] = useState<CodexionConfig>(defaultConfig);
  const [simulation, setSimulation] = useState<CodexionRunResponse | null>(null);
  const [simulationConfigKey, setSimulationConfigKey] = useState('');
  const [cursor, setCursor] = useState(0);
  const [speed, setSpeed] = useState(360);
  const [isBusy, setIsBusy] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [status, setStatus] = useState('Configure a run, then replay the scheduler trace.');

  const configKey = JSON.stringify(config);
  const frames = simulation?.frames ?? [];
  const frame = frames[cursor] ?? frames[0] ?? null;
  const currentEvent = frame?.event;
  const canvasCoders = frame?.coders ?? buildEmptyCoders(config.number_of_coders);
  const canvasDongles = frame?.dongles ?? buildEmptyDongles(config.number_of_coders);
  const activeCoders = canvasCoders.filter((coder) => coder.state === 'compiling');
  const activeDongles = canvasDongles.filter((dongle) => dongle.state === 'in_use');

  async function runSimulation(autoplay = false) {
    setIsPlaying(false);
    setIsBusy(true);
    setStatus('Running Codexion...');
    try {
      const data = await runCodexion(config);
      setSimulation(data);
      setSimulationConfigKey(configKey);
      setCursor(0);
      setIsPlaying(autoplay && data.frames.length > 1);
      setStatus(
        data.stats.outcome === 'completed'
          ? `Completed ${data.stats.compiles_completed} compile cycles.`
          : 'A coder burned out before the run completed.',
      );
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Codexion failed.');
    } finally {
      setIsBusy(false);
    }
  }

  function togglePlayback() {
    if (isBusy) return;
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }
    if (!simulation || simulationConfigKey !== configKey) {
      void runSimulation(true);
      return;
    }
    if (frames.length === 0) return;
    if (cursor >= frames.length - 1) setCursor(0);
    setIsPlaying(true);
  }

  useEffect(() => {
    if (!isPlaying || cursor >= frames.length - 1) return undefined;
    const timer = window.setTimeout(() => {
      setCursor((current) => {
        const next = Math.min(current + 1, frames.length - 1);
        if (next >= frames.length - 1) setIsPlaying(false);
        return next;
      });
    }, speed);
    return () => window.clearTimeout(timer);
  }, [cursor, frames.length, isPlaying, speed]);

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <div className="grid min-h-[760px] lg:grid-cols-[minmax(0,1fr)_390px]">
        <section className="flex min-w-0 flex-col">
          <header className="flex flex-col gap-5 border-b border-[#ece8dc] p-5 sm:flex-row sm:items-center sm:justify-between lg:p-7">
            <div className="max-w-3xl">
              <button
                className="mb-5 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 py-2 text-sm font-semibold text-[#30302e] transition hover:bg-[#faf9f5]"
                onClick={onBack}
                type="button"
              >
                Back to gallery
              </button>
              <p className="text-sm font-semibold text-[#c96442]">42 Codexion</p>
              <h3 className="mt-2 font-serif text-4xl leading-tight text-[#171715] sm:text-5xl">Codexion</h3>
              <CollapsibleDescription
                className="mt-5"
                fullText={fullDescription ?? description}
                previewText={description}
              />
            </div>
            <div className="flex flex-wrap gap-2 text-sm text-[#5e5d59]">
              <Metric label="time" value={`${frame?.time ?? 0} ms`} />
              <Metric label="events" value={simulation?.stats.total_events ?? 0} />
              <Metric label="scheduler" value={simulation?.stats.scheduler ?? config.scheduler} />
            </div>
          </header>

          <div className="flex flex-1 bg-[#f4f1e8] p-4">
            <section className="flex min-h-[520px] min-w-0 flex-col rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
              <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[#ece8dc] px-4 py-3">
                <div>
                  <h4 className="font-semibold text-[#171715]">State machine</h4>
                  <p className="mt-1 text-sm text-[#777267]">
                    {currentEvent ? `${currentEvent.time} ms · ${currentEvent.raw}` : 'Initial state'}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-bold ${
                    simulation?.stats.outcome === 'burned_out'
                      ? 'bg-[#f3dfd2] text-[#8a4429]'
                      : 'bg-[#e8eee0] text-[#49603b]'
                  }`}
                >
                  {simulation?.stats.outcome ?? 'ready'}
                </span>
              </header>

              <SimulationCanvas
                coders={canvasCoders}
                dongles={canvasDongles}
                required={config.number_of_compiles_required}
                time={frame?.time ?? 0}
              />
            </section>
          </div>
        </section>

        <aside
          className="scroll-mt-24 flex flex-col gap-5 border-t border-[#ece8dc] bg-[#faf9f5] p-5 lg:border-l lg:border-t-0"
          id="codexion-config"
        >
          <div className="grid grid-cols-2 gap-3">
            <NumberField field="number_of_coders" label="Coders" max={12} min={1} setConfig={setConfig} value={config.number_of_coders} />
            <NumberField
              field="number_of_compiles_required"
              label="Compiles"
              max={20}
              min={1}
              setConfig={setConfig}
              value={config.number_of_compiles_required}
            />
            <NumberField field="time_to_burnout" label="Burnout ms" max={10000} min={1} setConfig={setConfig} value={config.time_to_burnout} />
            <NumberField field="time_to_compile" label="Compile ms" max={5000} min={0} setConfig={setConfig} value={config.time_to_compile} />
            <NumberField field="time_to_debug" label="Debug ms" max={5000} min={0} setConfig={setConfig} value={config.time_to_debug} />
            <NumberField field="time_to_refactor" label="Refactor ms" max={5000} min={0} setConfig={setConfig} value={config.time_to_refactor} />
            <NumberField
              field="dongle_cooldown"
              label="Cooldown ms"
              max={5000}
              min={0}
              setConfig={setConfig}
              value={config.dongle_cooldown}
            />
          </div>

          <fieldset className="grid grid-cols-2 gap-2">
            <legend className="col-span-2 mb-1 text-sm font-bold text-[#777267]">Scheduler</legend>
            {(['FIFO', 'EDF'] as CodexionScheduler[]).map((scheduler) => (
              <label
                className={`flex min-h-10 items-center justify-center rounded-lg border text-sm font-semibold ${
                  config.scheduler === scheduler
                    ? 'border-[#c96442] bg-[#f3dfd2] text-[#8a4429]'
                    : 'border-[#e8e3d6] bg-[#fffdf8] text-[#5e5d59]'
                }`}
                key={scheduler}
              >
                <input
                  checked={config.scheduler === scheduler}
                  className="sr-only"
                  name="scheduler"
                  onChange={() => setConfig((current) => ({ ...current, scheduler }))}
                  type="radio"
                  value={scheduler}
                />
                {scheduler}
              </label>
            ))}
          </fieldset>

          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">
              Replay speed <b className="text-[#30302e]">{speed} ms</b>
            </span>
            <input
              className="accent-[#c96442]"
              max={1200}
              min={80}
              onChange={(event) => setSpeed(Number(event.target.value))}
              step={40}
              type="range"
              value={speed}
            />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Timeline</span>
            <input
              className="accent-[#c96442]"
              disabled={frames.length === 0}
              max={Math.max(frames.length - 1, 0)}
              min={0}
              onChange={(event) => {
                setIsPlaying(false);
                setCursor(Number(event.target.value));
              }}
              type="range"
              value={cursor}
            />
          </label>

          <div>
            <button
              className="min-h-11 w-full rounded-lg bg-[#c96442] px-4 text-sm font-bold text-[#faf9f5] transition hover:bg-[#b65334] disabled:opacity-60"
              disabled={isBusy}
              onClick={togglePlayback}
              type="button"
            >
              {isBusy ? 'Running...' : isPlaying ? 'Pause' : 'Play'}
            </button>
          </div>

          <p className="min-h-6 text-sm font-medium text-[#5e5d59]">{status}</p>

          <section className="rounded-xl border border-[#e8e3d6] bg-[#fffdf8] p-4">
            <h4 className="font-semibold text-[#171715]">Now</h4>
            <dl className="mt-3 grid gap-2 text-sm">
              <StatusRow label="Compiling" value={activeCoders.map((coder) => `C${coder.id}`).join(', ') || 'none'} />
              <StatusRow
                label="Dongles"
                value={activeDongles.map((dongle) => `D${dongle.id}->C${dongle.holder}`).join(', ') || 'none'}
              />
              <StatusRow label="Frame" value={`${cursor + 1}/${Math.max(frames.length, 1)}`} />
            </dl>
          </section>

          <section className="flex min-h-72 flex-1 flex-col overflow-hidden rounded-xl border border-[#e8e3d6] bg-[#fffdf8]">
            <header className="border-b border-[#ece8dc] px-4 py-3">
              <h4 className="font-semibold text-[#171715]">Logs</h4>
            </header>
            <ol className="flex-1 overflow-auto p-3 font-mono text-xs">
              {(simulation?.events ?? []).map((event) => (
                <li
                  className={`rounded-md px-2 py-1 ${
                    event.index === currentEvent?.index ? 'bg-[#f3dfd2] font-bold text-[#8a4429]' : 'text-[#777267]'
                  }`}
                  key={event.index}
                >
                  {event.raw}
                </li>
              ))}
            </ol>
          </section>
        </aside>
      </div>
    </article>
  );
}

function NumberField({
  field,
  label,
  max,
  min,
  setConfig,
  value,
}: {
  field: keyof Omit<CodexionConfig, 'scheduler'>;
  label: string;
  max: number;
  min: number;
  setConfig: Dispatch<SetStateAction<CodexionConfig>>;
  value: number;
}) {
  return (
    <label className="grid gap-2">
      <span className="text-sm font-bold text-[#777267]">{label}</span>
      <input
        className="h-11 min-w-0 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
        max={max}
        min={min}
        onChange={(event) => updateNumber(field, event.target.value, setConfig)}
        type="number"
        value={value}
      />
    </label>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <span className="min-w-24 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-2 text-center">
      <b className="text-[#171715]">{value}</b> {label}
    </span>
  );
}

function SimulationCanvas({
  coders,
  dongles,
  required,
  time,
}: {
  coders: CodexionCoderFrame[];
  dongles: CodexionDongleFrame[];
  required: number;
  time: number;
}) {
  const width = 920;
  const height = 620;
  const center = { x: width / 2, y: height / 2 };
  const radius = Math.min(width, height) * 0.32;
  const coderPoints = coders.map((coder, index) => ({
    ...pointOnCircle(center.x, center.y, radius, (index / Math.max(coders.length, 1)) * Math.PI * 2 - Math.PI / 2),
    coder,
  }));

  return (
    <div className="flex flex-1 flex-col p-4">
      <svg
        aria-label="Codexion circular state machine"
        className="min-h-[520px] w-full rounded-xl bg-[#faf9f5]"
        preserveAspectRatio="xMidYMid meet"
        viewBox={`0 0 ${width} ${height}`}
      >
        <defs>
          <filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="8" floodColor="#171715" floodOpacity="0.12" stdDeviation="8" />
          </filter>
        </defs>

        <rect fill="#faf9f5" height={height} rx="18" width={width} />
        <circle cx={center.x} cy={center.y} fill="none" r={radius} stroke="#d8d1c2" strokeDasharray="8 10" strokeWidth="2" />
        <circle cx={center.x} cy={center.y} fill="#fffdf8" r="82" stroke="#e8e3d6" strokeWidth="2" />
        <text fill="#171715" fontSize="18" fontWeight="700" textAnchor="middle" x={center.x} y={center.y - 8}>
          Scheduler
        </text>
        <text fill="#777267" fontSize="13" fontWeight="700" textAnchor="middle" x={center.x} y={center.y + 16}>
          {time} ms
        </text>

        {coderPoints.map(({ coder, x, y }, index) => {
          const next = coderPoints[(index + 1) % coderPoints.length];
          if (!next) return null;
          return (
            <line
              key={`edge-${coder.id}`}
              stroke="#cfc7b8"
              strokeDasharray="7 9"
              strokeWidth="2"
              x1={x}
              x2={next.x}
              y1={y}
              y2={next.y}
            />
          );
        })}

        {dongles.map((dongle) => {
          const holderPoint = dongle.holder ? coderPoints[dongle.holder - 1] : null;
          const point = midpointForDongle(dongle.id, coderPoints, center);
          const palette = donglePalette[dongle.state];
          const cooldownRemaining = Math.max(dongle.cooldown_until - time, 0);
          return (
            <g key={`dongle-${dongle.id}`}>
              {holderPoint ? (
                <line
                  stroke={palette.stroke}
                  strokeDasharray="4 7"
                  strokeWidth="3"
                  x1={holderPoint.x}
                  x2={point.x}
                  y1={holderPoint.y}
                  y2={point.y}
                />
              ) : null}
              <g filter="url(#soft-shadow)">
                <rect
                  fill={palette.fill}
                  height="34"
                  rx="9"
                  stroke={palette.stroke}
                  strokeWidth="3"
                  transform={`rotate(${angleBetween(center, point)} ${point.x} ${point.y})`}
                  width="58"
                  x={point.x - 29}
                  y={point.y - 17}
                />
                <circle cx={point.x - 12} cy={point.y} fill={palette.stroke} r="4" />
                <circle cx={point.x + 12} cy={point.y} fill={palette.stroke} r="4" />
              </g>
              <text fill={palette.text} fontSize="12" fontWeight="800" textAnchor="middle" x={point.x} y={point.y + 35}>
                D{dongle.id}{cooldownRemaining > 0 ? ` ${cooldownRemaining}` : ''}
              </text>
            </g>
          );
        })}

        {coderPoints.map(({ coder, x, y }) => (
          <CoderShape key={coder.id} coder={coder} required={required} x={x} y={y} />
        ))}
      </svg>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs font-bold text-[#5e5d59]">
        {stateLegend.map(({ label, state }) => {
          const palette = coderPalette[state];
          return (
            <span className="inline-flex items-center gap-2 rounded-full border border-[#e8e3d6] bg-[#fffdf8] px-3 py-1" key={state}>
              <span className="h-3 w-3 rounded-full" style={{ backgroundColor: palette.fill, border: `2px solid ${palette.stroke}` }} />
              {label}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function CoderShape({ coder, required, x, y }: { coder: CodexionCoderFrame; required: number; x: number; y: number }) {
  const palette = coderPalette[coder.state];
  const progress = Math.min(coder.compiles_done / Math.max(required, 1), 1);
  const label = coder.state === 'compiling' ? 'C' : coder.state === 'debugging' ? 'D' : coder.state === 'refactoring' ? 'R' : coder.state === 'complete' ? 'OK' : coder.state === 'burned_out' ? '!' : 'I';

  return (
    <g filter="url(#soft-shadow)">
      {coder.state === 'debugging' ? (
        <rect fill={palette.fill} height="86" rx="14" stroke={palette.stroke} strokeWidth="4" width="86" x={x - 43} y={y - 43} />
      ) : coder.state === 'refactoring' ? (
        <polygon fill={palette.fill} points={hexPoints(x, y, 50)} stroke={palette.stroke} strokeWidth="4" />
      ) : (
        <circle cx={x} cy={y} fill={palette.fill} r="48" stroke={palette.stroke} strokeWidth={coder.state === 'compiling' ? 7 : 4} />
      )}
      {coder.state === 'compiling' ? (
        <circle cx={x} cy={y} fill="none" r="60" stroke="#c96442" strokeDasharray="8 8" strokeWidth="3" />
      ) : null}
      <circle cx={x} cy={y} fill="none" r="38" stroke="#fffdf8" strokeOpacity="0.7" strokeWidth="2" />
      <text fill={palette.text} fontSize="22" fontWeight="900" textAnchor="middle" x={x} y={y - 5}>
        {label}
      </text>
      <text fill={palette.text} fontSize="13" fontWeight="800" textAnchor="middle" x={x} y={y + 17}>
        coder {coder.id}
      </text>
      <path
        d={progressArc(x, y, 55, progress)}
        fill="none"
        stroke="#171715"
        strokeLinecap="round"
        strokeOpacity="0.45"
        strokeWidth="5"
      />
      <text fill="#5e5d59" fontSize="12" fontWeight="800" textAnchor="middle" x={x} y={y + 73}>
        {coder.compiles_done}/{required}
      </text>
    </g>
  );
}

function pointOnCircle(cx: number, cy: number, radius: number, angle: number) {
  return {
    x: cx + Math.cos(angle) * radius,
    y: cy + Math.sin(angle) * radius,
  };
}

function midpointForDongle(
  dongleId: number,
  coderPoints: Array<{ x: number; y: number; coder: CodexionCoderFrame }>,
  center: { x: number; y: number },
) {
  const current = coderPoints[dongleId - 1];
  const next = coderPoints[dongleId % coderPoints.length];
  if (!current || !next) return center;
  const midpoint = { x: (current.x + next.x) / 2, y: (current.y + next.y) / 2 };
  return {
    x: center.x + (midpoint.x - center.x) * 0.94,
    y: center.y + (midpoint.y - center.y) * 0.94,
  };
}

function angleBetween(from: { x: number; y: number }, to: { x: number; y: number }) {
  return (Math.atan2(to.y - from.y, to.x - from.x) * 180) / Math.PI;
}

function hexPoints(cx: number, cy: number, radius: number) {
  return Array.from({ length: 6 }, (_, index) => {
    const point = pointOnCircle(cx, cy, radius, (index / 6) * Math.PI * 2 - Math.PI / 2);
    return `${point.x},${point.y}`;
  }).join(' ');
}

function progressArc(cx: number, cy: number, radius: number, progress: number) {
  if (progress <= 0) return '';
  const start = pointOnCircle(cx, cy, radius, -Math.PI / 2);
  const end = pointOnCircle(cx, cy, radius, -Math.PI / 2 + progress * Math.PI * 2);
  const largeArc = progress > 0.5 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[120px_minmax(0,1fr)] gap-3">
      <dt className="font-bold text-[#777267]">{label}</dt>
      <dd className="break-words text-[#30302e]">{value}</dd>
    </div>
  );
}

function buildEmptyCoders(count: number): CodexionCoderFrame[] {
  return Array.from({ length: count }, (_, index) => ({
    compiles_done: 0,
    deadline: defaultConfig.time_to_burnout,
    dongles: [],
    id: index + 1,
    state: 'idle',
  }));
}

function buildEmptyDongles(count: number): CodexionDongleFrame[] {
  return Array.from({ length: count }, (_, index) => ({
    cooldown_until: 0,
    holder: null,
    id: index + 1,
    state: 'available',
  }));
}

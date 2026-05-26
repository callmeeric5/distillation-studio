import { useEffect, useMemo, useState } from 'react';

import {
  generatePushSwapValues,
  runPushSwap,
  type PushSwapAlgorithm,
} from './api/pushSwap';

type StackKey = 'a' | 'b';

function parseValues(text: string) {
  const trimmed = text.trim();
  if (!trimmed) return [];
  return trimmed.split(/[\s,]+/).map((value) => Number(value));
}

function swap(stack: number[]) {
  if (stack.length < 2) return stack;
  const next = [...stack];
  [next[0], next[1]] = [next[1], next[0]];
  return next;
}

function rotate(stack: number[]) {
  if (stack.length < 2) return stack;
  return [...stack.slice(1), stack[0]];
}

function reverseRotate(stack: number[]) {
  if (stack.length < 2) return stack;
  return [stack[stack.length - 1], ...stack.slice(0, -1)];
}

function applyMove(
  current: Record<StackKey, number[]>,
  move: string,
): Record<StackKey, number[]> {
  let a = current.a;
  let b = current.b;

  if (move === 'pa' && b.length > 0) {
    a = [b[0], ...a];
    b = b.slice(1);
  }
  if (move === 'pb' && a.length > 0) {
    b = [a[0], ...b];
    a = a.slice(1);
  }
  if (move === 'sa' || move === 'ss') a = swap(a);
  if (move === 'sb' || move === 'ss') b = swap(b);
  if (move === 'ra' || move === 'rr') a = rotate(a);
  if (move === 'rb' || move === 'rr') b = rotate(b);
  if (move === 'rra' || move === 'rrr') a = reverseRotate(a);
  if (move === 'rrb' || move === 'rrr') b = reverseRotate(b);

  return { a, b };
}

function replayMoves(values: number[], moves: string[], cursor: number) {
  return moves.slice(0, cursor).reduce(
    (current, move) => applyMove(current, move),
    { a: values, b: [] as number[] },
  );
}

export function PushSwapStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const [input, setInput] = useState('8 2 5 1 9 3');
  const [size, setSize] = useState(100);
  const [algorithm, setAlgorithm] = useState<PushSwapAlgorithm>('complex');
  const [initialValues, setInitialValues] = useState<number[]>(parseValues(input));
  const [moves, setMoves] = useState<string[]>([]);
  const [cursor, setCursor] = useState(0);
  const [speed, setSpeed] = useState(50);
  const [status, setStatus] = useState('Paste values or generate a random set.');
  const [isBusy, setIsBusy] = useState(false);
  const [isMovesExpanded, setIsMovesExpanded] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const stacks = useMemo(
    () => replayMoves(initialValues, moves, cursor),
    [cursor, initialValues, moves],
  );
  const allValues = [...initialValues, ...stacks.a, ...stacks.b];
  const minValue = Math.min(...allValues, 0);
  const maxValue = Math.max(...allValues, 1);
  const currentMove =
    moves.length === 0 ? 'Idle' : cursor >= moves.length ? 'Done' : moves[cursor] ?? 'Ready';

  async function generateValues() {
    setStatus('Generating input...');
    setIsBusy(true);
    try {
      const data = await generatePushSwapValues(size, -500, 500);
      setInput(data.values.join(' '));
      setStatus('Generated a unique random input.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Could not generate values.');
    } finally {
      setIsBusy(false);
    }
  }

  async function runSort() {
    setIsPlaying(false);
    const values = parseValues(input);
    if (values.length === 0 || values.some((value) => !Number.isInteger(value))) {
      setStatus('Use only integer values.');
      return;
    }

    setStatus('Running push_swap...');
    setIsBusy(true);
    try {
      const data = await runPushSwap(values, algorithm);
      setInitialValues(data.values);
      setMoves(data.moves);
      setCursor(0);
      setStatus(`${data.algorithm} algorithm returned ${data.move_count} moves.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'push_swap failed.');
    } finally {
      setIsBusy(false);
    }
  }

  function play() {
    if (isPlaying || cursor >= moves.length) return;
    setIsPlaying(true);
  }

  useEffect(() => {
    if (!isPlaying) return undefined;
    if (cursor >= moves.length) return undefined;

    const timer = window.setTimeout(() => {
      setCursor((current) => {
        const next = current + 1;
        if (next >= moves.length) setIsPlaying(false);
        return next;
      });
    }, speed);

    return () => window.clearTimeout(timer);
  }, [cursor, isPlaying, moves.length, speed]);

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <div className="grid min-h-[720px] lg:grid-cols-[minmax(0,1fr)_380px]">
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
              <p className="text-sm font-semibold text-[#c96442]">42 Push Swap</p>
              <h3 className="mt-2 font-serif text-4xl leading-tight text-[#171715] sm:text-5xl">
                Push Swap Studio
              </h3>
              <CollapsibleDescription
                className="mt-5"
                configHref="#push-swap-config"
                fullText={fullDescription ?? description}
                previewText={description}
              />
            </div>
            <div className="flex flex-wrap gap-2 text-sm text-[#5e5d59]">
              <Metric label="moves" value={moves.length} />
              <Metric label="current" value={currentMove} />
            </div>
          </header>

          <div className="grid flex-1 gap-4 bg-[#f4f1e8] p-4 sm:grid-cols-2 lg:p-5">
            <StackView
              maxValue={maxValue}
              minValue={minValue}
              name="Stack A"
              stackKey="a"
              values={stacks.a}
            />
            <StackView
              maxValue={maxValue}
              minValue={minValue}
              name="Stack B"
              stackKey="b"
              values={stacks.b}
            />
          </div>
        </section>

        <aside
          className="scroll-mt-24 flex flex-col gap-5 border-t border-[#ece8dc] bg-[#faf9f5] p-5 lg:border-l lg:border-t-0"
          id="push-swap-config"
        >
          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Input</span>
            <textarea
              className="min-h-32 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] p-3 font-mono text-sm text-[#30302e] outline-none transition focus:border-[#c96442]"
              onChange={(event) => setInput(event.target.value)}
              spellCheck={false}
              value={input}
            />
          </label>

          <div className="grid grid-cols-[minmax(0,1fr)_128px] items-end gap-3">
            <label className="grid gap-2">
              <span className="text-sm font-bold text-[#777267]">Size</span>
              <input
                className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
                max={500}
                min={2}
                onChange={(event) => setSize(Number(event.target.value))}
                type="number"
                value={size}
              />
            </label>
            <button
              className="min-h-11 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 text-sm font-semibold text-[#30302e] transition hover:bg-[#fffdf8] disabled:opacity-60"
              disabled={isBusy}
              onClick={generateValues}
              type="button"
            >
              Generate
            </button>
          </div>

          <fieldset className="grid grid-cols-3 gap-2">
            <legend className="col-span-3 mb-1 text-sm font-bold text-[#777267]">
              Algorithm
            </legend>
            {(['simple', 'medium', 'complex'] as PushSwapAlgorithm[]).map((item) => (
              <label
                className={`flex min-h-10 items-center justify-center rounded-lg border text-sm font-semibold ${
                  algorithm === item
                    ? 'border-[#c96442] bg-[#f3dfd2] text-[#8a4429]'
                    : 'border-[#e8e3d6] bg-[#fffdf8] text-[#5e5d59]'
                }`}
                key={item}
              >
                <input
                  checked={algorithm === item}
                  className="sr-only"
                  name="algorithm"
                  onChange={() => setAlgorithm(item)}
                  type="radio"
                  value={item}
                />
                {item}
              </label>
            ))}
          </fieldset>

          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">
              Animation speed <b className="text-[#30302e]">{speed} ms</b>
            </span>
            <input
              className="accent-[#c96442]"
              max={1200}
              min={40}
              onChange={(event) => setSpeed(Number(event.target.value))}
              step={20}
              type="range"
              value={speed}
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <button
              className="col-span-2 min-h-11 rounded-lg bg-[#c96442] px-4 text-sm font-bold text-[#faf9f5] transition hover:bg-[#b65334] disabled:opacity-60"
              disabled={isBusy}
              onClick={runSort}
              type="button"
            >
              Run
            </button>
            <button
              className="min-h-11 rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-4 text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8] disabled:opacity-60"
              disabled={moves.length === 0 || cursor >= moves.length || isPlaying}
              onClick={play}
              type="button"
            >
              Play
            </button>
            <button
              className="min-h-11 rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-4 text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8] disabled:opacity-60"
              disabled={!isPlaying}
              onClick={() => setIsPlaying(false)}
              type="button"
            >
              Pause
            </button>
            <button
              className="col-span-2 min-h-11 rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-4 text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8] disabled:opacity-60"
              disabled={moves.length === 0}
              onClick={() => {
                setIsPlaying(false);
                setCursor(0);
              }}
              type="button"
            >
              Reset
            </button>
          </div>

          <p className="min-h-6 text-sm font-medium text-[#5e5d59]">{status}</p>
          <section className="overflow-hidden rounded-xl border border-[#e8e3d6] bg-[#fffdf8]">
            <button
              aria-expanded={isMovesExpanded}
              className="flex min-h-12 w-full items-center justify-between gap-3 px-4 text-left text-sm font-semibold text-[#30302e] transition hover:bg-[#f4f1e8]"
              onClick={() => setIsMovesExpanded((current) => !current)}
              type="button"
            >
              <span>Moves · {moves.length}</span>
              <span className="text-[#8a4429]">
                {isMovesExpanded ? 'Hide' : 'Show'}
              </span>
            </button>
            {isMovesExpanded ? (
              <ol className="grid max-h-64 gap-1 overflow-auto border-t border-[#e8e3d6] p-3 pl-8 font-mono text-sm">
                {moves.map((move, index) => (
                  <li
                    className={`rounded-md px-2 py-1 ${
                      index === cursor
                        ? 'bg-[#f3dfd2] font-bold text-[#8a4429]'
                        : 'text-[#777267]'
                    }`}
                    key={`${move}-${index}`}
                  >
                    {move}
                  </li>
                ))}
              </ol>
            ) : null}
          </section>
        </aside>
      </div>
    </article>
  );
}

function CollapsibleDescription({
  className = '',
  configHref,
  fullText,
  previewText,
}: {
  className?: string;
  configHref?: string;
  fullText: string;
  previewText: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const canExpand = fullText !== previewText;

  return (
    <div className={className}>
      <p className="text-lg leading-8 text-[#5e5d59]">
        {isExpanded || !canExpand ? fullText : previewText}
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        {canExpand ? (
          <button
            className="min-h-9 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 text-sm font-semibold text-[#8a4429] transition hover:bg-[#fffdf8]"
            onClick={() => setIsExpanded((current) => !current)}
            type="button"
          >
            {isExpanded ? 'Less' : 'More'}
          </button>
        ) : null}
        {configHref ? (
          <a
            className="inline-flex min-h-9 items-center rounded-lg bg-[#c96442] px-4 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334]"
            href={configHref}
          >
            Config
          </a>
        ) : null}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <span className="min-w-24 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-2 text-center">
      <b className="text-[#171715]">{value}</b> {label}
    </span>
  );
}

function StackView({
  maxValue,
  minValue,
  name,
  stackKey,
  values,
}: {
  maxValue: number;
  minValue: number;
  name: string;
  stackKey: StackKey;
  values: number[];
}) {
  return (
    <section className="flex min-h-[420px] min-w-0 flex-col rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <header className="flex items-center justify-between border-b border-[#ece8dc] px-4 py-3">
        <h4 className="font-semibold text-[#171715]">{name}</h4>
        <span className="font-bold text-[#777267]">{values.length}</span>
      </header>
      <div className="flex flex-1 flex-col items-center gap-1 overflow-auto p-3">
        {values.length === 0 ? (
          <div className="flex min-h-7 w-5/12 items-center justify-center rounded-md bg-[#d8d1c2] text-sm font-bold text-[#faf9f5] opacity-70">
            empty
          </div>
        ) : (
          values.map((value, index) => {
            const range = Math.max(maxValue - minValue, 1);
            const width = 34 + ((value - minValue) / range) * 62;
            return (
              <div
                className={`flex min-h-7 max-w-full items-center justify-center rounded-md text-sm font-bold text-white transition-all ${
                  stackKey === 'a' ? 'bg-[#49603b]' : 'bg-[#c96442]'
                }`}
                key={`${value}-${index}`}
                style={{ width: `${width}%` }}
              >
                {value}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

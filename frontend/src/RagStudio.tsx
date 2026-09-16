import { useState } from 'react';

import { answerRagQuestion, type RagAnswerResponse } from './api/rag';

const sampleQuestion = 'How does prefix caching work?';
const sourceCounts = [1, 3, 5, 10];

export function RagStudio({
  description,
  fullDescription,
  onBack,
}: {
  description: string;
  fullDescription?: string;
  onBack: () => void;
}) {
  const [question, setQuestion] = useState(sampleQuestion);
  const [sourceCount, setSourceCount] = useState(5);
  const [result, setResult] = useState<RagAnswerResponse | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const [status, setStatus] = useState('Ask a question about the vLLM 0.10.1 source tree.');
  const [isBusy, setIsBusy] = useState(false);
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);
  const canExpand = fullDescription && fullDescription !== description;

  async function run() {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setStatus('A question is required.');
      return;
    }

    setIsBusy(true);
    setResult(null);
    setDurationMs(null);
    setStatus('Retrieving source passages and generating a grounded answer...');
    const startedAt = performance.now();
    try {
      const response = await answerRagQuestion({ question: trimmedQuestion, k: sourceCount });
      const elapsedMs = Math.round(performance.now() - startedAt);
      setResult(response);
      setDurationMs(elapsedMs);
      setStatus(
        `Answer generated from ${response.sources.length} source${response.sources.length === 1 ? '' : 's'} in ${formatDuration(elapsedMs)}.`,
      );
    } catch (error) {
      setDurationMs(Math.round(performance.now() - startedAt));
      setStatus(error instanceof Error ? error.message : 'Could not run RAG.');
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
            <p className="text-sm font-semibold text-[#c96442]">42 project / retrieval-augmented generation</p>
            <h3 className="mt-2 font-serif text-4xl leading-tight text-[#171715] sm:text-5xl">RAG</h3>
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
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h4 className="text-sm font-bold uppercase text-[#8b8174]">Grounded answer</h4>
                <span className="text-xs font-semibold text-[#777267]">
                  {durationMs === null ? 'Waiting for a question' : formatDuration(durationMs)}
                </span>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-base leading-7 text-[#30302e]">
                {result?.answer ?? 'The Qwen answer will appear here after retrieval.'}
              </p>
            </section>

            <section>
              <div className="flex flex-wrap items-end justify-between gap-2">
                <div>
                  <p className="text-sm font-bold uppercase text-[#8b8174]">Retrieved sources</p>
                  <p className="mt-1 text-sm text-[#777267]">Exact ranges from the bundled vLLM 0.10.1 corpus.</p>
                </div>
                {result ? (
                  <span className="rounded-full bg-[#f4f1e8] px-3 py-1 text-xs font-bold text-[#8a4429]">
                    {result.sources.length} matches
                  </span>
                ) : null}
              </div>

              <div className="mt-3 grid gap-3">
                {result?.sources.map((source, index) => (
                  <details
                    className="overflow-hidden rounded-xl border border-[#e8e3d6] bg-[#f4f1e8]"
                    key={`${source.file_path}-${source.first_character_index}`}
                    open={index === 0}
                  >
                    <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-[#30302e]">
                      <span className="break-all font-mono">{source.file_path}</span>
                      <span className="ml-2 whitespace-nowrap text-xs text-[#8b8174]">
                        {source.first_character_index}–{source.last_character_index}
                      </span>
                    </summary>
                    <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words border-t border-[#e8e3d6] bg-[#fffdf8] p-4 font-mono text-xs leading-5 text-[#30302e]">
                      {source.content}
                    </pre>
                  </details>
                ))}
                {!result ? (
                  <p className="rounded-xl border border-dashed border-[#d9d1c1] p-5 text-sm text-[#777267]">
                    Retrieved code and documentation passages will be shown here.
                  </p>
                ) : null}
              </div>
            </section>
          </div>
        </section>

        <aside className="flex flex-col gap-5 border-t border-[#ece8dc] bg-[#faf9f5] p-5 lg:border-l lg:border-t-0">
          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Question</span>
            <textarea
              className="min-h-40 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 py-3 text-sm leading-6 text-[#30302e] outline-none transition focus:border-[#c96442]"
              maxLength={4000}
              onChange={(event) => setQuestion(event.target.value)}
              value={question}
            />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-bold text-[#777267]">Sources to retrieve</span>
            <select
              className="h-11 rounded-xl border border-[#e8e3d6] bg-[#fffdf8] px-3 text-[#30302e] outline-none transition focus:border-[#c96442]"
              onChange={(event) => setSourceCount(Number(event.target.value))}
              value={sourceCount}
            >
              {sourceCounts.map((count) => (
                <option key={count} value={count}>{count}</option>
              ))}
            </select>
          </label>

          <div className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4 text-sm leading-6 text-[#5e5d59]">
            BM25 ranks exact source ranges first. Qwen3-0.6B then answers using only those passages.
          </div>

          <button
            className="min-h-11 rounded-lg bg-[#c96442] px-4 text-sm font-bold text-[#faf9f5] transition hover:bg-[#b65334] disabled:opacity-60"
            disabled={isBusy}
            onClick={run}
            type="button"
          >
            {isBusy ? 'Running RAG...' : 'Ask RAG'}
          </button>
          <p className="min-h-6 text-sm font-medium leading-6 text-[#5e5d59]">{status}</p>
        </aside>
      </div>
    </article>
  );
}

function formatDuration(durationMs: number) {
  if (durationMs < 1000) return `${durationMs} ms`;
  return `${(durationMs / 1000).toFixed(2)} s`;
}

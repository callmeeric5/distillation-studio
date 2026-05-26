import { AMazeIngStudio } from '../AMazeIngStudio';
import { PushSwapStudio } from '../PushSwapStudio';
import { projectStatusStyles, statusStyles } from '../lib/styles';
import type { Project, RunState } from '../types/projects';
import { CollapsibleDescription } from './CollapsibleDescription';

export function ProjectPage({
  onBack,
  onRunProject,
  project,
  runState,
}: {
  onBack: () => void;
  onRunProject: (project: Project) => void;
  project: Project;
  runState: RunState;
}) {
  const isRunnable = Boolean(project.endpoint);

  if (project.slug === 'push-swap') {
    return (
      <PushSwapStudio
        description={project.description}
        fullDescription={project.fullDescription}
        onBack={onBack}
      />
    );
  }

  if (project.slug === 'a-maze-ing') {
    return (
      <AMazeIngStudio
        description={project.description}
        fullDescription={project.fullDescription}
        onBack={onBack}
      />
    );
  }

  return (
    <article className="overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#fffdf8]">
      <div className="grid gap-8 p-5 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] lg:p-7">
        <div className="relative min-h-96 overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#e8e3d6]">
          {project.coverImage ? (
            <img
              alt={`${project.title} cover`}
              className="h-full min-h-96 w-full object-cover"
              src={project.coverImage}
            />
          ) : (
            <div className="h-full min-h-96 bg-[#f4f1e8]" />
          )}
          <button
            className="absolute left-5 top-5 rounded-lg bg-[#faf9f5]/90 px-4 py-2 text-sm font-semibold text-[#30302e] backdrop-blur transition hover:bg-[#faf9f5]"
            onClick={onBack}
            type="button"
          >
            Back to gallery
          </button>
          <div className="absolute inset-x-0 bottom-0 flex flex-wrap items-end justify-between gap-3 bg-gradient-to-t from-[#171715]/75 to-transparent p-5 text-[#faf9f5]">
            <div>
              <h3 className="font-serif text-4xl sm:text-5xl">{project.title}</h3>
              <p className="mt-3 text-sm font-semibold text-[#faf9f5]/75">{project.category}</p>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${projectStatusStyles[project.status]}`}
            >
              {project.status}
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <div>
            <p className="text-sm font-semibold text-[#c96442]">
              {isRunnable ? 'Project runner' : 'Project notes'}
            </p>
            <CollapsibleDescription
              className="mt-3"
              fullText={project.fullDescription ?? project.description}
              previewText={project.description}
            />
          </div>

          <dl className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
              <dt className="text-xs font-bold uppercase text-[#8b8174]">Runtime</dt>
              <dd className="mt-1 font-semibold text-[#171715]">{project.language}</dd>
            </div>
            <div className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
              <dt className="text-xs font-bold uppercase text-[#8b8174]">
                {isRunnable ? 'API route' : 'Availability'}
              </dt>
              <dd
                className={`mt-1 break-words text-sm ${
                  isRunnable ? 'font-mono text-[#8a4429]' : 'font-semibold text-[#5e5d59]'
                }`}
              >
                {project.endpoint ??
                  'This page is prepared for notes and progress. A runner will be connected when the project is ready.'}
              </dd>
            </div>
          </dl>

          <div className="flex flex-wrap gap-2" aria-label={`${project.title} tags`}>
            {project.tags.map((tag) => (
              <span
                className="rounded-full border border-[#e8e3d6] px-3 py-1 text-sm font-semibold text-[#6f6a5f]"
                key={tag}
              >
                {tag}
              </span>
            ))}
          </div>

          {isRunnable ? (
            <>
              <button
                className="min-h-12 w-fit rounded-lg bg-[#c96442] px-6 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334] disabled:cursor-wait disabled:opacity-60"
                disabled={runState.status === 'running'}
                onClick={() => onRunProject(project)}
                type="button"
              >
                {runState.status === 'running' ? 'Running...' : 'Run project'}
              </button>

              <output
                className={`block min-h-24 whitespace-pre-wrap break-words rounded-xl border p-4 font-mono text-sm ${statusStyles[runState.status]}`}
              >
                {runState.message}
              </output>
            </>
          ) : (
            <div className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4 text-base leading-7 text-[#5e5d59]">
              This project is not runnable yet. It stays in the portfolio as a progress marker until there is a stable demo or write-up to connect.
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

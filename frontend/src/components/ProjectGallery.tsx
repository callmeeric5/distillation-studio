import { useMemo } from 'react';

import { statusFilters, statusOrder } from '../data/projects';
import { projectStatusStyles } from '../lib/styles';
import type { Project, StatusFilter } from '../types/projects';

export function ProjectGallery({
  onStatusFilterChange,
  onTryProject,
  projects,
  statusFilter,
}: {
  onStatusFilterChange: (status: StatusFilter) => void;
  onTryProject: (project: Project) => void;
  projects: Project[];
  statusFilter: StatusFilter;
}) {
  const sortedProjects = useMemo(
    () =>
      [...projects].sort(
        (first, second) =>
          statusOrder.indexOf(first.status) - statusOrder.indexOf(second.status),
      ),
    [projects],
  );
  const visibleProjects =
    statusFilter === 'all'
      ? sortedProjects
      : sortedProjects.filter((project) => project.status === statusFilter);

  return (
    <div className="grid gap-7">
      <div className="flex flex-wrap gap-2 border-b border-[#ece8dc] pb-5">
        {statusFilters.map((status) => (
          <button
            className={`min-h-10 rounded-lg px-4 text-sm font-semibold transition ${
              statusFilter === status
                ? 'bg-[#30302e] text-[#faf9f5]'
                : 'border border-[#e8e3d6] bg-[#f4f1e8] text-[#5e5d59] hover:bg-white hover:text-[#171715]'
            }`}
            key={status}
            onClick={() => onStatusFilterChange(status)}
            type="button"
          >
            {status}
          </button>
        ))}
      </div>

      {visibleProjects.length > 0 ? (
        <div className="grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
          {visibleProjects.map((project) => (
            <GalleryCard key={project.title} onTryProject={onTryProject} project={project} />
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-[#d8d1c2] bg-[#f4f1e8] p-8 text-center">
          <h3 className="font-serif text-3xl text-[#171715]">No projects match this status.</h3>
          <p className="mx-auto mt-3 max-w-xl text-base leading-7 text-[#5e5d59]">
            Choose another status filter to continue browsing the gallery.
          </p>
        </div>
      )}
    </div>
  );
}

export function GalleryCard({
  onTryProject,
  project,
}: {
  onTryProject: (project: Project) => void;
  project: Project;
}) {
  return (
    <article className="group flex min-h-[500px] flex-col border-t border-[#ded8ca] pt-4">
      <div className="relative aspect-[16/10] overflow-hidden rounded-2xl border border-[#e8e3d6] bg-[#e8e3d6]">
        {project.coverImage ? (
          <img
            alt={`${project.title} cover`}
            className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]"
            src={project.coverImage}
          />
        ) : (
          <div className="h-full w-full bg-[#e8e3d6] p-5">
            <div className="h-full rounded-xl border border-[#d4cbbb] bg-[#f4f1e8]" />
          </div>
        )}
        <span
          className={`absolute right-4 top-4 rounded-full px-3 py-1 text-xs font-semibold ring-1 ${projectStatusStyles[project.status]}`}
        >
          {project.status}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-4 pt-5">
        <div>
          <p className="text-sm font-semibold text-[#8b8174]">
            {project.category} / {project.language}
          </p>
          <h3 className="mt-2 font-serif text-3xl leading-tight text-[#171715]">
            {project.title}
          </h3>
        </div>

        <p className="min-h-[84px] line-clamp-4 text-base leading-7 text-[#5e5d59]">
          {project.description}
        </p>

        <div className="flex min-h-[48px] flex-wrap content-start gap-2" aria-label={`${project.title} tags`}>
          {project.tags.map((tag) => (
            <span
              className="rounded-full border border-[#e8e3d6] px-3 py-1 text-sm font-semibold text-[#6f6a5f]"
              key={tag}
            >
              {tag}
            </span>
          ))}
        </div>

        <button
          className="mt-auto min-h-11 w-fit rounded-lg bg-[#c96442] px-5 text-sm font-semibold text-[#faf9f5] transition hover:bg-[#b65334]"
          onClick={() => onTryProject(project)}
          type="button"
        >
          Try it out
        </button>
      </div>
    </article>
  );
}

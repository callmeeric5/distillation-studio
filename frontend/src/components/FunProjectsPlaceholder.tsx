import { GalleryCard } from './ProjectGallery';
import type { Project } from '../types/projects';

export function FunProjectsPlaceholder({
  onTryProject,
  projects,
}: {
  onTryProject: (project: Project) => void;
  projects: Project[];
}) {
  if (projects.length > 0) {
    return (
      <div className="grid gap-5 md:grid-cols-2">
        {projects.map((project) => (
          <GalleryCard key={project.title} onTryProject={onTryProject} project={project} />
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-dashed border-[#d8d1c2] bg-[#f4f1e8] p-8 text-center">
      <p className="text-sm font-semibold text-[#c96442]">Coming next</p>
      <h3 className="mt-3 font-serif text-3xl text-[#171715]">
        A gallery space for experiments and playful tools.
      </h3>
      <p className="mx-auto mt-3 max-w-xl text-base leading-7 text-[#5e5d59]">
        Add Python, Go, C, or browser-based projects here when they are ready to connect through FastAPI.
      </p>
    </div>
  );
}

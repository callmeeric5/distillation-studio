import mazeCover from '../assets/a-maze-ing-cover.png';
import pushSwapCover from '../assets/push-swap-cover.png';
import type { Project, ProjectStatus, StatusFilter, TabKey } from '../types/projects';

export const tabs: Array<{ key: TabKey; label: string }> = [
  { key: 'projects42', label: 'Projects in 42' },
  { key: 'fun', label: 'Fun projects' },
  { key: 'about', label: 'About me' },
];

export const projects42: Project[] = [
  {
    title: 'A_Maze_Ing',
    category: '42 project',
    language: 'Common Core / python',
    status: 'ready',
    description: 'An interactive maze project for generating, solving, and replaying maze algorithms in the browser.',
    fullDescription:
      'A_Maze_Ing turns maze generation and solving into an interactive study surface. Configure the dimensions, entry, exit, 42 pattern, generation strategy, solver, seed, and visual theme, then watch the maze carve and solve itself step by step.',
    endpoint: '/api/projects/a-maze-ing/run',
    coverImage: mazeCover,
    slug: 'a-maze-ing',
    routeSlug: 'a_maze_ing',
    tags: ['maze', 'algorithm', 'runner'],
  },
  {
    title: 'Pacman',
    category: '42 project',
    language: 'Common Core / c',
    status: 'in progress',
    description: 'A game-oriented C project planned as a compact arcade-style entry in the 42 collection.',
    fullDescription:
      'Pacman is listed as in progress while the project materials are being prepared. The detail page will collect the goal, implementation notes, and any runnable or visual pieces once they are ready.',
    slug: 'pacman',
    routeSlug: 'pacman',
    tags: ['game', 'maps', 'graphics'],
  },
  {
    title: 'Flyin',
    category: '42 project',
    language: 'Common Core / c',
    status: 'in progress',
    description: 'A work-in-progress 42 project entry reserved for notes, implementation details, and demos.',
    fullDescription:
      'Flyin is currently in progress. This page will become the place for the project description, technical notes, and any browser-friendly output once the implementation is ready to present.',
    slug: 'flyin',
    routeSlug: 'flyin',
    tags: ['42', 'systems', 'demo'],
  },
  {
    title: 'Call_Me_Maybe',
    category: '42 project',
    language: 'Common Core / c',
    status: 'in progress',
    description: 'A planned 42 project page for collecting the project story, implementation notes, and final result.',
    fullDescription:
      'Call_Me_Maybe is listed as in progress while the project is being prepared for the portfolio. The page will stay non-runnable until there is a stable implementation or demo to connect.',
    slug: 'call-me-maybe',
    routeSlug: 'call_me_maybe',
    tags: ['42', 'notes', 'demo'],
  },
  {
    title: 'Push_Swap',
    category: '42 project',
    language: 'Common Core / c',
    status: 'ready',
    description: 'A sorting algorithm project built around constrained stack operations and move-count optimization.',
    fullDescription:
      'Push_Swap explores how to sort integer inputs using only a constrained set of stack operations. The interactive page generates inputs, sends them to the shared FastAPI backend, runs the C binary, then replays the returned operations so move count, stack state, and algorithm behavior can be inspected step by step.',
    endpoint: '/api/projects/push-swap/run',
    coverImage: pushSwapCover,
    slug: 'push-swap',
    routeSlug: 'push_swap',
    tags: ['sorting', 'stacks', 'optimization'],
  },
];

export const funProjects: Project[] = [];
export const statusOrder: ProjectStatus[] = ['ready', 'coming soon', 'in progress'];
export const statusFilters: StatusFilter[] = ['all', ...statusOrder];
export const allProjects = [...projects42, ...funProjects];

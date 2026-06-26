import mazeCover from '../assets/a-maze-ing-cover.png';
import flyInCover from '../assets/fly-in-cover.png';
import pacManCover from '../assets/pac-man-cover.png';
import pushSwapCover from '../assets/push-swap-cover.png';
import traceOpsCover from '../assets/trace-ops-agent-cover.png';
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
    title: 'Pac_Man',
    category: '42 project',
    language: 'Common Core / python',
    status: 'ready',
    description: 'A multi-level browser arcade game with maze movement, ghost AI, scoring, and a live leaderboard.',
    fullDescription:
      'Pac_Man adapts the original Python Arcade project into a browser-playable Canvas game. Move through generated mazes, collect pacgums, use power dots to turn the chase around, advance through several levels, then let the Postgres-backed leaderboard save eligible runs automatically.',
    coverImage: pacManCover,
    slug: 'pacman',
    routeSlug: 'pac-man',
    tags: ['game', 'maze', 'ghost AI'],
  },
  {
    title: 'Fly_In',
    category: '42 project',
    language: 'Common Core / python',
    status: 'ready',
    description: 'A turn-by-turn drone routing simulation with capacity-aware zones, connections, and route playback.',
    fullDescription:
      'Fly_In routes drones from a start zone to an end zone through a constrained network. The shared FastAPI backend reads the original map files, computes drone paths, runs the turn scheduler, and returns a trace that the browser replays as moving and waiting drones.',
    endpoint: '/api/projects/fly-in/maps',
    coverImage: flyInCover,
    slug: 'flyin',
    routeSlug: 'fly-in',
    tags: ['routing', 'simulation', 'capacity'],
  },
  {
    title: 'Call_Me_Maybe',
    category: '42 project',
    language: 'Common Core / python',
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

export const funProjects: Project[] = [
  {
    title: 'Trace_Ops_Agent',
    category: 'Fun project',
    language: 'LLM / FastAPI / ops',
    status: 'ready',
    description:
      'An incident diagnosis assistant that turns logs and alerts into a structured operations report.',
    fullDescription:
      'Trace_Ops_Agent is a lightweight portfolio version of an SRE diagnostic assistant. Enter an incident, paste logs, choose a provider and model, and the shared FastAPI backend calls your selected LLM with your request-only API key to produce a root cause, evidence chain, recommended actions, and confidence.',
    endpoint: '/api/projects/trace-ops-agent/diagnose',
    coverImage: traceOpsCover,
    slug: 'trace-ops-agent',
    routeSlug: 'trace_ops_agent',
    tags: ['ReAct Agent', 'LangGraph', 'LangChain'],
  },
];
export const statusOrder: ProjectStatus[] = ['ready', 'coming soon', 'in progress'];
export const statusFilters: StatusFilter[] = ['all', ...statusOrder];
export const allProjects = [...projects42, ...funProjects];

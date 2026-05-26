export type TabKey = 'projects42' | 'fun' | 'about';
export type ProjectStatus = 'ready' | 'coming soon' | 'in progress';
export type StatusFilter = 'all' | ProjectStatus;

export type Project = {
  title: string;
  category: string;
  language: string;
  status: ProjectStatus;
  description: string;
  fullDescription?: string;
  endpoint?: string;
  coverImage?: string;
  slug: string;
  routeSlug: string;
  tags: string[];
};

export type RunState = {
  status: 'idle' | 'running' | 'success' | 'error';
  message: string;
};

export type RouteState = {
  activeTab: TabKey;
  selectedProject: Project | null;
  title: string;
};

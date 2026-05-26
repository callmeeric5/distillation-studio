import { allProjects } from '../data/projects';
import type { Project, RouteState, TabKey } from '../types/projects';

export function getProjectPath(project: Project) {
  return `/projects/42projects/${project.routeSlug}`;
}

export function getTabPath(tab: TabKey) {
  const paths: Record<TabKey, string> = {
    about: '/about',
    fun: '/projects/fun',
    projects42: '/projects',
  };
  return paths[tab];
}

export function readRoute(): RouteState {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  const projectMatch = path.match(/^\/projects\/42projects\/([^/]+)$/);
  const selectedProject = projectMatch
    ? allProjects.find((project) => project.routeSlug === projectMatch[1])
    : null;

  if (selectedProject) {
    return { activeTab: 'projects42', selectedProject, title: selectedProject.title };
  }
  if (path === '/projects') {
    return { activeTab: 'projects42', selectedProject: null, title: 'Projects' };
  }
  if (path === '/about') {
    return { activeTab: 'about', selectedProject: null, title: 'About' };
  }
  if (path === '/projects/fun') {
    return { activeTab: 'fun', selectedProject: null, title: 'Fun projects' };
  }
  return { activeTab: 'projects42', selectedProject: null, title: 'Home' };
}

import { useEffect, useMemo, useState } from 'react';

import { FunProjectsPlaceholder } from './components/FunProjectsPlaceholder';
import { ProjectGallery } from './components/ProjectGallery';
import { ProjectPage } from './components/ProjectPage';
import { SiteHeader } from './components/SiteHeader';
import { funProjects, projects42, tabs } from './data/projects';
import { getProjectPath, getTabPath, readRoute } from './lib/routes';
import { AboutMe } from './pages/AboutMe';
import type { Project, RouteState, RunState, StatusFilter, TabKey } from './types/projects';

function App() {
  const [routeState, setRouteState] = useState<RouteState>(() => readRoute());
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [runStates, setRunStates] = useState<Record<string, RunState>>({});
  const [theme, setTheme] = useState<'light' | 'dark'>(() =>
    window.localStorage.getItem('theme') === 'dark' ? 'dark' : 'light',
  );
  const { activeTab, selectedProject } = routeState;
  const activeLabel = useMemo(
    () => tabs.find((tab) => tab.key === activeTab)?.label ?? tabs[0].label,
    [activeTab],
  );

  useEffect(() => {
    document.title = routeState.title;
  }, [routeState.title]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    function syncRoute() {
      setRouteState(readRoute());
      setStatusFilter('all');
    }

    window.addEventListener('popstate', syncRoute);
    return () => window.removeEventListener('popstate', syncRoute);
  }, []);

  function navigate(path: string) {
    if (window.location.pathname !== path) {
      window.history.pushState(null, '', path);
    }
    setRouteState(readRoute());
    setStatusFilter('all');
  }

  function selectTab(tab: TabKey) {
    navigate(getTabPath(tab));
  }

  function selectProject(project: Project) {
    navigate(getProjectPath(project));
  }

  async function runProject(project: Project) {
    if (!project.endpoint) return;

    setRunStates((current) => ({
      ...current,
      [project.title]: {
        status: 'running',
        message: `Calling ${project.endpoint}`,
      },
    }));

    try {
      const response = await fetch(project.endpoint, { method: 'POST' });
      if (!response.ok) throw new Error(`Backend returned ${response.status}`);
      const payload: unknown = await response.json();
      setRunStates((current) => ({
        ...current,
        [project.title]: {
          status: 'success',
          message: JSON.stringify(payload, null, 2),
        },
      }));
    } catch (error) {
      setRunStates((current) => ({
        ...current,
        [project.title]: {
          status: 'error',
          message: error instanceof Error ? error.message : 'Backend runner is not reachable yet.',
        },
      }));
    }
  }

  return (
    <main className={`min-h-screen bg-[#faf9f5] text-[#171715] ${theme === 'dark' ? 'theme-dark' : ''}`}>
      <div className="mx-auto flex w-full max-w-7xl flex-col px-5 py-5 sm:px-8 lg:px-10">
        <SiteHeader
          activeTab={activeTab}
          onSelectTab={selectTab}
          onToggleTheme={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
          theme={theme}
        />

        <section className="border-b border-[#ece8dc] pb-12">
          <div>
            <p className="text-sm font-semibold text-[#c96442]">Distillation Studio</p>
            <h1 className="mt-4 max-w-4xl font-serif text-5xl leading-[0.98] text-[#171715] sm:text-6xl lg:text-7xl">
              A gallery of projects you can explore and run.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-[#5e5d59]">
              For projects I have built, lessons I am still working through...
            </p>
          </div>
        </section>

        <section aria-labelledby="section-title" className="py-12">
          <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold text-[#c96442]">Selected collection</p>
              <h2 className="mt-1 font-serif text-4xl text-[#171715] sm:text-5xl" id="section-title">
                {activeLabel}
              </h2>
            </div>
          </div>

          {selectedProject ? (
            <ProjectPage
              onBack={() => navigate('/projects')}
              onRunProject={runProject}
              project={selectedProject}
              runState={
                runStates[selectedProject.title] ?? {
                  status: 'idle',
                  message: 'Waiting for a run request.',
                }
              }
            />
          ) : null}

          {!selectedProject && activeTab === 'projects42' && (
            <ProjectGallery
              onStatusFilterChange={setStatusFilter}
              onTryProject={selectProject}
              projects={projects42}
              statusFilter={statusFilter}
            />
          )}
          {!selectedProject && activeTab === 'fun' && (
            <FunProjectsPlaceholder onTryProject={selectProject} projects={funProjects} />
          )}
          {!selectedProject && activeTab === 'about' && <AboutMe />}
        </section>
      </div>
    </main>
  );
}

export default App;

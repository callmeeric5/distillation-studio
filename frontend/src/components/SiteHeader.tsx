import logo from '../assets/logo.png';
import { tabs } from '../data/projects';
import type { TabKey } from '../types/projects';

export function SiteHeader({
  activeTab,
  onSelectTab,
  onToggleTheme,
  theme,
}: {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  onToggleTheme: () => void;
  theme: 'light' | 'dark';
}) {
  return (
    <header className="sticky top-0 z-10 -mx-5 mb-10 border-b border-[#ece8dc] bg-[#faf9f5]/95 px-5 py-4 backdrop-blur sm:-mx-8 sm:px-8 lg:-mx-10 lg:px-10">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-lg bg-[#c96442]">
            <img alt="Zihang Wang logo" className="h-full w-full object-cover" src={logo} />
          </span>
          <div>
            <p className="text-sm font-semibold text-[#3d3d3a]">Zihang Wang</p>
            <p className="text-xs text-[#777267]">Projects and runnable notes</p>
          </div>
        </div>
        <nav
          aria-label="Project board sections"
          className="flex gap-1 overflow-x-auto rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-1"
        >
          {tabs.map((tab) => (
            <button
              className={`min-h-10 shrink-0 rounded-lg px-4 text-sm font-semibold transition ${
                tab.key === activeTab
                  ? 'bg-[#30302e] text-[#faf9f5]'
                  : 'text-[#5e5d59] hover:bg-[#faf9f5] hover:text-[#171715]'
              }`}
              key={tab.key}
              onClick={() => onSelectTab(tab.key)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
          <button
            aria-label={theme === 'dark' ? 'Switch to day mode' : 'Switch to night mode'}
            className="theme-toggle flex min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border border-[#e8e3d6] bg-[#faf9f5] text-lg font-semibold text-[#5e5d59] transition hover:bg-white hover:text-[#171715]"
            onClick={onToggleTheme}
            title={theme === 'dark' ? 'Switch to day mode' : 'Switch to night mode'}
            type="button"
          >
            {theme === 'dark' ? '☀' : '☾'}
          </button>
        </nav>
      </div>
    </header>
  );
}

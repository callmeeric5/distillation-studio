import { type ReactNode, useEffect, useMemo, useState } from "react";
import { PushSwapStudio } from "./PushSwapStudio";
import mazeCover from "./assets/a-maze-ing-cover.png";
import logo from "./assets/logo.png";
import profilePhoto from "./assets/profolio.jpg";
import pushSwapCover from "./assets/push-swap-cover.png";

type TabKey = "projects42" | "fun" | "about";
type ProjectStatus = "ready" | "coming soon" | "in progress";
type StatusFilter = "all" | ProjectStatus;

type Project = {
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

type RunState = {
    status: "idle" | "running" | "success" | "error";
    message: string;
};

const tabs: Array<{ key: TabKey; label: string }> = [
    { key: "projects42", label: "Projects in 42" },
    { key: "fun", label: "Fun projects" },
    { key: "about", label: "About me" },
];

const projects42: Project[] = [
    {
        title: "A_Maze_Ing",
        category: "42 project",
        language: "Common Core / python",
        status: "coming soon",
        description:
            "A maze project space planned for clearer browser notes, examples, and visual explanations.",
        fullDescription:
            "A_Maze_Ing will become a readable project page for maze generation and solving ideas. For now it is marked as coming soon while the write-up and runnable presentation are being prepared.",
        coverImage: mazeCover,
        slug: "a-maze-ing",
        routeSlug: "a_maze_ing",
        tags: ["maze", "algorithm", "runner"],
    },
    {
        title: "Pacman",
        category: "42 project",
        language: "Common Core / c",
        status: "in progress",
        description:
            "A game-oriented C project planned as a compact arcade-style entry in the 42 collection.",
        fullDescription:
            "Pacman is listed as in progress while the project materials are being prepared. The detail page will collect the goal, implementation notes, and any runnable or visual pieces once they are ready.",
        slug: "pacman",
        routeSlug: "pacman",
        tags: ["game", "maps", "graphics"],
    },
    {
        title: "Flyin",
        category: "42 project",
        language: "Common Core / c",
        status: "in progress",
        description:
            "A work-in-progress 42 project entry reserved for notes, implementation details, and demos.",
        fullDescription:
            "Flyin is currently in progress. This page will become the place for the project description, technical notes, and any browser-friendly output once the implementation is ready to present.",
        slug: "flyin",
        routeSlug: "flyin",
        tags: ["42", "systems", "demo"],
    },
    {
        title: "Call_Me_Maybe",
        category: "42 project",
        language: "Common Core / c",
        status: "in progress",
        description:
            "A planned 42 project page for collecting the project story, implementation notes, and final result.",
        fullDescription:
            "Call_Me_Maybe is listed as in progress while the project is being prepared for the portfolio. The page will stay non-runnable until there is a stable implementation or demo to connect.",
        slug: "call-me-maybe",
        routeSlug: "call_me_maybe",
        tags: ["42", "notes", "demo"],
    },
    {
        title: "Push_Swap",
        category: "42 project",
        language: "Common Core / c",
        status: "ready",
        description:
            "A sorting algorithm project built around constrained stack operations and move-count optimization.",
        fullDescription:
            "Push_Swap explores how to sort integer inputs using only a constrained set of stack operations. The interactive page generates inputs, sends them to the shared FastAPI backend, runs the C binary, then replays the returned operations so move count, stack state, and algorithm behavior can be inspected step by step.",
        endpoint: "/api/projects/push-swap/run",
        coverImage: pushSwapCover,
        slug: "push-swap",
        routeSlug: "push_swap",
        tags: ["sorting", "stacks", "optimization"],
    },
];

const funProjects: Project[] = [];
const statusOrder: ProjectStatus[] = ["ready", "coming soon", "in progress"];
const statusFilters: StatusFilter[] = ["all", ...statusOrder];

const statusStyles: Record<RunState["status"], string> = {
    idle: "border-[#dedbd0] bg-[#f4f1e8] text-[#6f6a5f]",
    running: "border-[#d2c9b7] bg-[#f7f2e8] text-[#7a5139]",
    success: "border-[#c9d1bd] bg-[#eef3e8] text-[#4d5f39]",
    error: "border-[#dec6b5] bg-[#fbede5] text-[#8a4429]",
};

const projectStatusStyles: Record<ProjectStatus, string> = {
    ready: "bg-[#e8eee0] text-[#415234] ring-[#cfd8c4]",
    "coming soon": "bg-[#ede9dd] text-[#625e55] ring-[#ddd7c9]",
    "in progress": "bg-[#f3dfd2] text-[#8a4429] ring-[#e4c2ae]",
};

type RouteState = {
    activeTab: TabKey;
    selectedProject: Project | null;
    title: string;
};

const allProjects = [...projects42, ...funProjects];

function getProjectPath(project: Project) {
    return `/projects/42projects/${project.routeSlug}`;
}

function readRoute(): RouteState {
    const path = window.location.pathname.replace(/\/+$/, "") || "/";
    const projectMatch = path.match(/^\/projects\/42projects\/([^/]+)$/);
    const selectedProject = projectMatch
        ? allProjects.find((project) => project.routeSlug === projectMatch[1])
        : null;

    if (selectedProject) {
        return {
            activeTab: "projects42",
            selectedProject,
            title: selectedProject.title,
        };
    }

    if (path === "/projects") {
        return {
            activeTab: "projects42",
            selectedProject: null,
            title: "Projects",
        };
    }

    if (path === "/about") {
        return { activeTab: "about", selectedProject: null, title: "About" };
    }

    if (path === "/projects/fun") {
        return {
            activeTab: "fun",
            selectedProject: null,
            title: "Fun projects",
        };
    }

    return { activeTab: "projects42", selectedProject: null, title: "Home" };
}

function App() {
    const [routeState, setRouteState] = useState<RouteState>(() => readRoute());
    const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
    const [runStates, setRunStates] = useState<Record<string, RunState>>({});
    const [theme, setTheme] = useState<"light" | "dark">(() =>
        window.localStorage.getItem("theme") === "dark" ? "dark" : "light",
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
        window.localStorage.setItem("theme", theme);
    }, [theme]);

    useEffect(() => {
        function syncRoute() {
            setRouteState(readRoute());
            setStatusFilter("all");
        }

        window.addEventListener("popstate", syncRoute);
        return () => window.removeEventListener("popstate", syncRoute);
    }, []);

    function navigate(path: string) {
        if (window.location.pathname !== path) {
            window.history.pushState(null, "", path);
        }
        setRouteState(readRoute());
        setStatusFilter("all");
    }

    function selectTab(tab: TabKey) {
        const paths: Record<TabKey, string> = {
            about: "/about",
            fun: "/projects/fun",
            projects42: "/projects",
        };
        navigate(paths[tab]);
    }

    function selectProject(project: Project) {
        navigate(getProjectPath(project));
    }

    function toggleTheme() {
        setTheme((current) => (current === "dark" ? "light" : "dark"));
    }

    async function runProject(project: Project) {
        if (!project.endpoint) return;

        setRunStates((current) => ({
            ...current,
            [project.title]: {
                status: "running",
                message: `Calling ${project.endpoint}`,
            },
        }));

        try {
            const response = await fetch(project.endpoint, { method: "POST" });
            if (!response.ok) {
                throw new Error(`Backend returned ${response.status}`);
            }
            const payload: unknown = await response.json();
            setRunStates((current) => ({
                ...current,
                [project.title]: {
                    status: "success",
                    message: JSON.stringify(payload, null, 2),
                },
            }));
        } catch (error) {
            setRunStates((current) => ({
                ...current,
                [project.title]: {
                    status: "error",
                    message:
                        error instanceof Error
                            ? error.message
                            : "Backend runner is not reachable yet.",
                },
            }));
        }
    }

    return (
        <main
            className={`min-h-screen bg-[#faf9f5] text-[#171715] ${
                theme === "dark" ? "theme-dark" : ""
            }`}
        >
            <div className="mx-auto flex w-full max-w-7xl flex-col px-5 py-5 sm:px-8 lg:px-10">
                <header className="sticky top-0 z-10 -mx-5 mb-10 border-b border-[#ece8dc] bg-[#faf9f5]/95 px-5 py-4 backdrop-blur sm:-mx-8 sm:px-8 lg:-mx-10 lg:px-10">
                    <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                        <div className="flex items-center gap-3">
                            <span className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-lg bg-[#c96442]">
                                <img
                                    alt="Zihang Wang logo"
                                    className="h-full w-full object-cover"
                                    src={logo}
                                />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-[#3d3d3a]">
                                    Zihang Wang
                                </p>
                                <p className="text-xs text-[#777267]">
                                    Projects and runnable notes
                                </p>
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
                                            ? "bg-[#30302e] text-[#faf9f5]"
                                            : "text-[#5e5d59] hover:bg-[#faf9f5] hover:text-[#171715]"
                                    }`}
                                    key={tab.key}
                                    onClick={() => {
                                        selectTab(tab.key);
                                    }}
                                    type="button"
                                >
                                    {tab.label}
                                </button>
                            ))}
                            <button
                                aria-label={
                                    theme === "dark"
                                        ? "Switch to day mode"
                                        : "Switch to night mode"
                                }
                                className="theme-toggle flex min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border border-[#e8e3d6] bg-[#faf9f5] text-lg font-semibold text-[#5e5d59] transition hover:bg-white hover:text-[#171715]"
                                onClick={toggleTheme}
                                title={
                                    theme === "dark"
                                        ? "Switch to day mode"
                                        : "Switch to night mode"
                                }
                                type="button"
                            >
                                {theme === "dark" ? "☀" : "☾"}
                            </button>
                        </nav>
                    </div>
                </header>

                <section className="border-b border-[#ece8dc] pb-12">
                    <div>
                        <p className="text-sm font-semibold text-[#c96442]">
                            Distillation Studio
                        </p>
                        <h1 className="mt-4 max-w-4xl font-serif text-5xl leading-[0.98] text-[#171715] sm:text-6xl lg:text-7xl">
                            A gallery of projects you can explore and run.
                        </h1>
                        <p className="mt-6 max-w-2xl text-lg leading-8 text-[#5e5d59]">
                            For projects I have built, lessons I am still
                            working through...
                        </p>
                    </div>
                </section>

                <section aria-labelledby="section-title" className="py-12">
                    <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                        <div>
                            <p className="text-sm font-semibold text-[#c96442]">
                                Selected collection
                            </p>
                            <h2
                                className="mt-1 font-serif text-4xl text-[#171715] sm:text-5xl"
                                id="section-title"
                            >
                                {activeLabel}
                            </h2>
                        </div>
                    </div>

                    {selectedProject ? (
                        <ProjectPage
                            onBack={() => navigate("/projects")}
                            onRunProject={runProject}
                            project={selectedProject}
                            runState={
                                runStates[selectedProject.title] ?? {
                                    status: "idle",
                                    message: "Waiting for a run request.",
                                }
                            }
                        />
                    ) : null}

                    {!selectedProject && activeTab === "projects42" && (
                        <ProjectGallery
                            onTryProject={selectProject}
                            projects={projects42}
                            statusFilter={statusFilter}
                            onStatusFilterChange={setStatusFilter}
                        />
                    )}
                    {!selectedProject && activeTab === "fun" && (
                        <FunProjectsPlaceholder
                            onTryProject={selectProject}
                            projects={funProjects}
                        />
                    )}
                    {!selectedProject && activeTab === "about" && <AboutMe />}
                </section>
            </div>
        </main>
    );
}

function ProjectGallery({
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
                    statusOrder.indexOf(first.status) -
                    statusOrder.indexOf(second.status),
            ),
        [projects],
    );
    const visibleProjects =
        statusFilter === "all"
            ? sortedProjects
            : sortedProjects.filter(
                  (project) => project.status === statusFilter,
              );

    return (
        <div className="grid gap-7">
            <div className="flex flex-wrap gap-2 border-b border-[#ece8dc] pb-5">
                {statusFilters.map((status) => (
                    <button
                        className={`min-h-10 rounded-lg px-4 text-sm font-semibold transition ${
                            statusFilter === status
                                ? "bg-[#30302e] text-[#faf9f5]"
                                : "border border-[#e8e3d6] bg-[#f4f1e8] text-[#5e5d59] hover:bg-white hover:text-[#171715]"
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
                        <GalleryCard
                            key={project.title}
                            onTryProject={onTryProject}
                            project={project}
                        />
                    ))}
                </div>
            ) : (
                <div className="rounded-2xl border border-dashed border-[#d8d1c2] bg-[#f4f1e8] p-8 text-center">
                    <h3 className="font-serif text-3xl text-[#171715]">
                        No projects match this status.
                    </h3>
                    <p className="mx-auto mt-3 max-w-xl text-base leading-7 text-[#5e5d59]">
                        Choose another status filter to continue browsing the
                        gallery.
                    </p>
                </div>
            )}
        </div>
    );
}

function GalleryCard({
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

                <p className="line-clamp-4 text-base leading-7 text-[#5e5d59]">
                    {project.description}
                </p>

                <div
                    className="flex flex-wrap gap-2"
                    aria-label={`${project.title} tags`}
                >
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
                    {project.endpoint ? "Try it out" : "Open project"}
                </button>
            </div>
        </article>
    );
}

function ProjectPage({
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

    if (project.slug === "push-swap") {
        return (
            <PushSwapStudio
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
                            <h3 className="font-serif text-4xl sm:text-5xl">
                                {project.title}
                            </h3>
                            <p className="mt-3 text-sm font-semibold text-[#faf9f5]/75">
                                {project.category}
                            </p>
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
                            {isRunnable ? "Project runner" : "Project notes"}
                        </p>
                        <CollapsibleDescription
                            className="mt-3"
                            fullText={
                                project.fullDescription ?? project.description
                            }
                            previewText={project.description}
                        />
                    </div>

                    <dl className="grid gap-4 sm:grid-cols-2">
                        <div className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
                            <dt className="text-xs font-bold uppercase text-[#8b8174]">
                                Runtime
                            </dt>
                            <dd className="mt-1 font-semibold text-[#171715]">
                                {project.language}
                            </dd>
                        </div>
                        <div className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4">
                            <dt className="text-xs font-bold uppercase text-[#8b8174]">
                                {isRunnable ? "API route" : "Availability"}
                            </dt>
                            <dd
                                className={`mt-1 break-words text-sm ${
                                    isRunnable
                                        ? "font-mono text-[#8a4429]"
                                        : "font-semibold text-[#5e5d59]"
                                }`}
                            >
                                {project.endpoint ??
                                    "This page is prepared for notes and progress. A runner will be connected when the project is ready."}
                            </dd>
                        </div>
                    </dl>

                    <div
                        className="flex flex-wrap gap-2"
                        aria-label={`${project.title} tags`}
                    >
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
                                disabled={runState.status === "running"}
                                onClick={() => onRunProject(project)}
                                type="button"
                            >
                                {runState.status === "running"
                                    ? "Running..."
                                    : "Run project"}
                            </button>

                            <output
                                className={`block min-h-24 whitespace-pre-wrap break-words rounded-xl border p-4 font-mono text-sm ${statusStyles[runState.status]}`}
                            >
                                {runState.message}
                            </output>
                        </>
                    ) : (
                        <div className="rounded-xl border border-[#e8e3d6] bg-[#f4f1e8] p-4 text-base leading-7 text-[#5e5d59]">
                            This project is not runnable yet. It stays in the
                            portfolio as a progress marker until there is a
                            stable demo or write-up to connect.
                        </div>
                    )}
                </div>
            </div>
        </article>
    );
}

function FunProjectsPlaceholder({
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
                    <GalleryCard
                        key={project.title}
                        onTryProject={onTryProject}
                        project={project}
                    />
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
                Add Python, Go, C, or browser-based projects here when they are
                ready to connect through FastAPI.
            </p>
        </div>
    );
}

function AboutMe() {
    const profileLinks = [
        ["GitHub", "https://github.com/callmeeric5"],
        ["LinkedIn", "https://www.linkedin.com/in/callmeeric5/"],
    ];

    const personalInfo = [
        ["Name", "Zihang Wang"],
        ["Location", "Paris/France"],
        ["Focus", "Machine learning, systems programming and algorithms"],
        ["Current work", "MLE in distillation studio"],
    ];

    const workExperience = [
        {
            title: "Full Stack Machine Learning Engineer",
            meta: "Distillation Studio",
            body: "AI integration and transition for small business.",
        },
        {
            title: "Data Scientist",
            meta: "Yso Corp",
            body: "User install classification in RTB system",
        },
        {
            title: "Data Scientist",
            meta: "Trip.com",
            body: "OCR and auto reconciliation of transaction receipts",
        },
    ];

    const education = [
        {
            title: "42 Paris",
            meta: "Systems Programming",
            body: "Project-based learning focused on C, Unix fundamentals, algorithms, debugging, collaboration, and building reliable programs from first principles.",
        },
        {
            title: "EPITA",
            meta: "Artificial Intelligence",
            body: " ML and DL",
        },
        {
            title: "Hong Kong Baptist University",
            meta: "Computer Science",
            body: "Foundation of computer science",
        },
    ];

    return (
        <div className="grid gap-8 rounded-2xl border border-[#e8e3d6] bg-[#fffdf8] p-6 lg:grid-cols-[0.72fr_1.28fr] lg:p-7">
            <aside className="rounded-2xl border border-[#e8e3d6] bg-[#f4f1e8] p-7">
                <div className="flex flex-col items-center text-center">
                    <p className="text-sm font-semibold tracking-wide text-[#c96442]">
                        About me
                    </p>

                    <h3 className="mt-3 font-serif text-4xl leading-tight text-[#171715]">
                        Zihang Wang
                    </h3>

                    <img
                        alt="Zihang Wang profile"
                        className="mt-8 h-45 w-45 rounded-full border border-[#d8d1c2] object-cover shadow-sm sm:h-50 sm:w-50"
                        src={profilePhoto}
                    />

                    <div className="mt-7 flex flex-row flex-wrap justify-center gap-3">
                        {profileLinks.map(([label, href]) => (
                            <a
                                className="inline-flex min-h-10 items-center justify-center rounded-lg border border-[#e8e3d6] bg-[#fffdf8] px-5 text-sm font-semibold text-[#8a4429] transition hover:bg-[#faf9f5]"
                                href={href}
                                key={label}
                                rel="noreferrer"
                                target="_blank"
                            >
                                {label}
                            </a>
                        ))}
                    </div>
                </div>

                <p className="mt-8 text-center text-base leading-8 text-[#5e5d59]">
                    Building AI products by day.
                    <br />
                    Gaming and lifting after hours.
                </p>
            </aside>

            <div className="grid gap-7">
                <ResumeSection title="Personal info">
                    <dl className="grid gap-3 sm:grid-cols-2">
                        {personalInfo.map(([label, value]) => (
                            <div
                                className="rounded-xl border border-[#e8e3d6] bg-[#faf9f5] p-4"
                                key={label}
                            >
                                <dt className="text-xs font-bold uppercase text-[#8b8174]">
                                    {label}
                                </dt>
                                <dd className="mt-1 text-sm font-semibold text-[#30302e]">
                                    {value}
                                </dd>
                            </div>
                        ))}
                    </dl>
                </ResumeSection>

                <ResumeSection title="Working experience">
                    <div className="grid gap-4">
                        {workExperience.map((item) => (
                            <ResumeItem key={item.title} {...item} />
                        ))}
                    </div>
                </ResumeSection>

                <ResumeSection title="Educational experience">
                    <div className="grid gap-4">
                        {education.map((item) => (
                            <ResumeItem key={item.title} {...item} />
                        ))}
                    </div>
                </ResumeSection>
            </div>
        </div>
    );
}

function ResumeSection({
    children,
    title,
}: {
    children: ReactNode;
    title: string;
}) {
    return (
        <section>
            <h3 className="font-serif text-3xl leading-tight text-[#171715]">
                {title}
            </h3>
            <div className="mt-4">{children}</div>
        </section>
    );
}

function ResumeItem({
    body,
    meta,
    title,
}: {
    body: string;
    meta: string;
    title: string;
}) {
    return (
        <article className="border-t border-[#e8e3d6] pt-4">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                <h4 className="text-lg font-semibold text-[#30302e]">
                    {title}
                </h4>
                <p className="text-sm font-semibold text-[#8b8174]">{meta}</p>
            </div>
            <p className="mt-2 text-base leading-7 text-[#5e5d59]">{body}</p>
        </article>
    );
}

function CollapsibleDescription({
    className = "",
    fullText,
    previewText,
}: {
    className?: string;
    fullText: string;
    previewText: string;
}) {
    const [isExpanded, setIsExpanded] = useState(false);
    const canExpand = fullText !== previewText;

    return (
        <div className={className}>
            <p className="text-lg leading-8 text-[#5e5d59]">
                {isExpanded || !canExpand ? fullText : previewText}
            </p>
            {canExpand ? (
                <button
                    className="mt-3 min-h-9 rounded-lg border border-[#e8e3d6] bg-[#f4f1e8] px-4 text-sm font-semibold text-[#8a4429] transition hover:bg-[#fffdf8]"
                    onClick={() => setIsExpanded((current) => !current)}
                    type="button"
                >
                    {isExpanded ? "Less" : "More"}
                </button>
            ) : null}
        </div>
    );
}

export default App;

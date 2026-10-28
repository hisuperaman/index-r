
import { useMemo, useState } from "react";
import { PageContainer, ThemeToggle } from "@/components";
import { Button } from "@/components/ui/button.tsx";
import { useLogout } from "@/queries";

type Workspace = {
    id: number;
    title: string;
    description: string;
    category: string;
    color: string;
    icon: string;
    updated: string;
};

const initialWorkspaces: Workspace[] = [
    {
        id: 1,
        title: "Research & Discovery",
        description: "Explore ideas, research papers, and new possibilities.",
        category: "Research",
        color: "from-violet-500/30 to-indigo-500/10",
        icon: "⌕",
        updated: "Updated today",
    },
    {
        id: 2,
        title: "Product Planning",
        description: "Organize product ideas, plans, and priorities.",
        category: "Planning",
        color: "from-cyan-500/30 to-blue-500/10",
        icon: "◈",
        updated: "Updated yesterday",
    },
    {
        id: 3,
        title: "Learning Space",
        description: "Collect useful resources and learning materials.",
        category: "Learning",
        color: "from-amber-500/30 to-orange-500/10",
        icon: "✳",
        updated: "Updated 2 days ago",
    },
    {
        id: 4,
        title: "Project Documents",
        description: "Keep project notes, references, and ideas together.",
        category: "Projects",
        color: "from-emerald-500/30 to-teal-500/10",
        icon: "▤",
        updated: "Updated 3 days ago",
    },
];

export const Home = () => {
    const logoutMutation = useLogout();

    const [workspaces, setWorkspaces] =
        useState<Workspace[]>(initialWorkspaces);
    const [search, setSearch] = useState("");
    const [activeTab, setActiveTab] = useState("All");
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [newTitle, setNewTitle] = useState("");
    const [selectedWorkspace, setSelectedWorkspace] =
        useState<Workspace | null>(null);

    const tabs = ["All", "Research", "Planning", "Learning", "Projects"];

    const filteredWorkspaces = useMemo(() => {
        return workspaces.filter((workspace) => {
            const matchesSearch =
                workspace.title.toLowerCase().includes(search.toLowerCase()) ||
                workspace.description.toLowerCase().includes(search.toLowerCase());

            const matchesTab =
                activeTab === "All" || workspace.category === activeTab;

            return matchesSearch && matchesTab;
        });
    }, [workspaces, search, activeTab]);

    const createWorkspace = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        const title = newTitle.trim();
        if (!title) return;

        const workspace: Workspace = {
            id: Date.now(),
            title,
            description: "Your new space for ideas and resources.",
            category: "Projects",
            color: "from-fuchsia-500/30 to-pink-500/10",
            icon: "✧",
            updated: "Created just now",
        };

        setWorkspaces((current) => [workspace, ...current]);
        setActiveTab("All");
        setSearch("");
        setNewTitle("");
        setShowCreateForm(false);
    };

    return (
        <PageContainer>
            <div className="min-h-screen bg-background text-foreground">
                <div className="flex min-h-screen">
                    <aside className="hidden w-64 shrink-0 border-r border-border/70 bg-muted/20 p-5 md:flex md:flex-col">
                        <a href="/" className="mb-10 flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-xl font-bold text-primary-foreground">
                                W
                            </div>
                            <div>
                                <p className="text-lg font-semibold tracking-tight">
                                    Workspace
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    Your ideas, organized
                                </p>
                            </div>
                        </a>

                        <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                            Menu
                        </p>

                        <nav className="space-y-1">
                            <button
                                onClick={() => {
                                    setActiveTab("All");
                                    setSelectedWorkspace(null);
                                }}
                                className="flex w-full items-center gap-3 rounded-xl bg-primary/10 px-3 py-3 text-left text-sm font-medium text-primary"
                            >
                                <span>▦</span> All workspaces
                            </button>
                            <button
                                onClick={() => setShowCreateForm(true)}
                                className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm text-muted-foreground transition hover:bg-muted hover:text-foreground"
                            >
                                <span>＋</span> Create workspace
                            </button>
                        </nav>

                        <div className="mt-9">
                            <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                                Categories
                            </p>
                            {tabs.slice(1).map((tab) => (
                                <button
                                    key={tab}
                                    onClick={() => {
                                        setActiveTab(tab);
                                        setSelectedWorkspace(null);
                                    }}
                                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition ${
                                        activeTab === tab
                                            ? "bg-muted font-medium text-foreground"
                                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                    }`}
                                >
                                    <span className="text-base">◇</span>
                                    {tab}
                                </button>
                            ))}
                        </div>

                        <div className="mt-auto rounded-2xl border border-border bg-background p-4">
                            <div className="mb-2 text-xl">✦</div>
                            <p className="text-sm font-semibold">
                                One place for everything
                            </p>
                            <p className="mt-1 text-xs leading-5 text-muted-foreground">
                                Bring your ideas and resources together in one organized space.
                            </p>
                        </div>
                    </aside>

                    <main className="min-w-0 flex-1">
                        <header className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-border/70 bg-background/90 px-5 py-4 backdrop-blur-md sm:px-8 lg:px-10">
                            <div className="md:hidden">
                                <p className="font-semibold">Workspace</p>
                            </div>

                            <div className="hidden text-sm text-muted-foreground md:block">
                                Home <span className="mx-2">/</span>
                                <span className="text-foreground">Workspaces</span>
                            </div>

                            <div className="flex items-center gap-3">
                                <ThemeToggle />
                                <div className="hidden h-9 w-9 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary sm:flex">
                                    W
                                </div>
                                <Button
                                    variant="destructive"
                                    onClick={() => logoutMutation.mutate()}
                                    disabled={logoutMutation.isPending}
                                >
                                    {logoutMutation.isPending ? "Logging out..." : "Logout"}
                                </Button>
                            </div>
                        </header>

                        <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-10 lg:px-10">
                            <section className="mb-10">
                                <div className="mb-7 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
                                    <div>
                                        <p className="mb-3 text-sm font-medium text-primary">
                                            YOUR PERSONAL SPACE
                                        </p>
                                        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                                            Good to see you.
                                        </h1>
                                        <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground sm:text-base">
                                            Bring your research, ideas, and resources
                                            together in one place.
                                        </p>
                                    </div>

                                    <Button onClick={() => setShowCreateForm(true)}>
                                        <span className="mr-2">＋</span>
                                        New workspace
                                    </Button>
                                </div>

                                <label className="flex max-w-2xl items-center gap-3 rounded-2xl border border-border bg-muted/30 px-4 py-3.5 transition focus-within:border-primary">
                                    <span className="text-lg text-muted-foreground">
                                        ⌕
                                    </span>
                                    <input
                                        value={search}
                                        onChange={(event) => setSearch(event.target.value)}
                                        placeholder="Search your workspaces..."
                                        className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                                    />
                                    <span className="hidden rounded-md border border-border px-2 py-1 text-xs text-muted-foreground sm:block">
                                        Search
                                    </span>
                                </label>
                            </section>

                            {showCreateForm && (
                                <section className="mb-8 rounded-2xl border border-border bg-muted/20 p-5 sm:p-6">
                                    <h2 className="text-lg font-semibold">
                                        Create a workspace
                                    </h2>
                                    <p className="mt-1 text-sm text-muted-foreground">
                                        Give your new workspace a name.
                                    </p>
                                    <form
                                        onSubmit={createWorkspace}
                                        className="mt-4 flex flex-col gap-3 sm:flex-row"
                                    >
                                        <input
                                            autoFocus
                                            value={newTitle}
                                            onChange={(event) =>
                                                setNewTitle(event.target.value)
                                            }
                                            placeholder="e.g. AI Research"
                                            maxLength={80}
                                            className="min-w-0 flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-primary"
                                        />
                                        <Button type="submit">Create</Button>
                                        <Button
                                            type="button"
                                            variant="outline"
                                            onClick={() => {
                                                setShowCreateForm(false);
                                                setNewTitle("");
                                            }}
                                        >
                                            Cancel
                                        </Button>
                                    </form>
                                </section>
                            )}

                            {selectedWorkspace ? (
                                <section className="mb-10 rounded-2xl border border-border p-6 sm:p-8">
                                    <button
                                        onClick={() => setSelectedWorkspace(null)}
                                        className="mb-6 text-sm text-primary hover:underline"
                                    >
                                        ← Back to workspaces
                                    </button>
                                    <div
                                        className={`mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br ${selectedWorkspace.color} text-3xl`}
                                    >
                                        {selectedWorkspace.icon}
                                    </div>
                                    <h2 className="text-2xl font-semibold">
                                        {selectedWorkspace.title}
                                    </h2>
                                    <p className="mt-2 text-muted-foreground">
                                        {selectedWorkspace.description}
                                    </p>
                                    <p className="mt-5 text-sm text-muted-foreground">
                                        {selectedWorkspace.updated}
                                    </p>
                                    <div className="mt-6 rounded-xl border border-dashed border-border p-6 text-center">
                                        <p className="font-medium">
                                            Your workspace is ready
                                        </p>
                                        <p className="mt-2 text-sm text-muted-foreground">
                                            Workspace content and integrations can be added later.
                                        </p>
                                    </div>
                                </section>
                            ) : (
                                <>
                                    <section className="mb-12">
                                        <div className="mb-5 flex items-center justify-between">
                                            <div>
                                                <h2 className="text-xl font-semibold">
                                                    Featured workspaces
                                                </h2>
                                                <p className="mt-1 text-sm text-muted-foreground">
                                                    A few places to get you started.
                                                </p>
                                            </div>
                                            <span className="text-sm text-muted-foreground">
                                                {workspaces.length} total
                                            </span>
                                        </div>

                                        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                                            {workspaces.slice(0, 3).map((workspace) => (
                                                <button
                                                    key={workspace.id}
                                                    onClick={() =>
                                                        setSelectedWorkspace(workspace)
                                                    }
                                                    className="group overflow-hidden rounded-2xl border border-border bg-card text-left transition duration-200 hover:-translate-y-1 hover:border-primary/40 hover:shadow-lg"
                                                >
                                                    <div
                                                        className={`flex h-32 items-center justify-center bg-gradient-to-br ${workspace.color}`}
                                                    >
                                                        <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/20 bg-background/50 text-4xl shadow-sm backdrop-blur">
                                                            {workspace.icon}
                                                        </div>
                                                    </div>
                                                    <div className="p-5">
                                                        <div className="mb-2 flex items-center justify-between gap-2">
                                                            <h3 className="font-semibold group-hover:text-primary">
                                                                {workspace.title}
                                                            </h3>
                                                            <span className="text-muted-foreground">
                                                                ↗
                                                            </span>
                                                        </div>
                                                        <p className="min-h-10 text-sm leading-5 text-muted-foreground">
                                                            {workspace.description}
                                                        </p>
                                                        <p className="mt-4 text-xs text-muted-foreground">
                                                            {workspace.updated}
                                                        </p>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </section>

                                    <section>
                                        <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                                            <div>
                                                <h2 className="text-xl font-semibold">
                                                    Recent workspaces
                                                </h2>
                                                <p className="mt-1 text-sm text-muted-foreground">
                                                    Pick up where you left off.
                                                </p>
                                            </div>
                                            <button
                                                onClick={() => setActiveTab("All")}
                                                className="self-start text-sm font-medium text-primary hover:underline sm:self-auto"
                                            >
                                                View all →
                                            </button>
                                        </div>

                                        <div className="mb-5 flex flex-wrap gap-2">
                                            {tabs.map((tab) => (
                                                <button
                                                    key={tab}
                                                    onClick={() => setActiveTab(tab)}
                                                    className={`rounded-full px-4 py-2 text-sm transition ${
                                                        activeTab === tab
                                                            ? "bg-primary text-primary-foreground"
                                                            : "border border-border bg-background text-muted-foreground hover:bg-muted"
                                                    }`}
                                                >
                                                    {tab}
                                                </button>
                                            ))}
                                        </div>

                                        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                                            {filteredWorkspaces.map((workspace) => (
                                                <button
                                                    key={workspace.id}
                                                    onClick={() =>
                                                        setSelectedWorkspace(workspace)
                                                    }
                                                    className="flex min-w-0 items-start gap-4 rounded-2xl border border-border bg-card p-4 text-left transition hover:border-primary/40 hover:bg-muted/30"
                                                >
                                                    <div
                                                        className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${workspace.color} text-2xl`}
                                                    >
                                                        {workspace.icon}
                                                    </div>
                                                    <div className="min-w-0 flex-1">
                                                        <h3 className="truncate text-sm font-semibold">
                                                            {workspace.title}
                                                        </h3>
                                                        <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                                                            {workspace.description}
                                                        </p>
                                                        <p className="mt-3 text-xs text-muted-foreground">
                                                            {workspace.updated}
                                                        </p>
                                                    </div>
                                                    <span className="text-muted-foreground">
                                                        ···
                                                    </span>
                                                </button>
                                            ))}
                                        </div>

                                        {filteredWorkspaces.length === 0 && (
                                            <div className="rounded-2xl border border-dashed border-border px-6 py-12 text-center">
                                                <p className="font-medium">
                                                    No workspaces found
                                                </p>
                                                <p className="mt-2 text-sm text-muted-foreground">
                                                    Try another search or category.
                                                </p>
                                            </div>
                                        )}
                                    </section>
                                </>
                            )}

                            <footer className="mt-14 border-t border-border/70 pt-5 text-xs text-muted-foreground">
                                Workspace · Your ideas, all in one place
                            </footer>
                        </div>
                    </main>
                </div>
            </div>
        </PageContainer>
    );
};

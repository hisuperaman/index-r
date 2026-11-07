import {useRef, useState} from "react";
import {Link} from "react-router";
import {
    BookOpenCheckIcon,
    LibraryIcon,
    MessageCircleQuestionIcon,
    MoreHorizontalIcon,
    PlusIcon,
    SearchIcon,
    SearchXIcon,
    SparklesIcon,
    XIcon,
} from "lucide-react";
import {AppHeader, ErrorPlaceholder} from "@/components";
import {Button} from "@/components/ui/button";
import {Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle} from "@/components/ui/empty";
import {InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput} from "@/components/ui/input-group";
import {Skeleton} from "@/components/ui/skeleton";
import {Spinner} from "@/components/ui/spinner";
import {CreateWorkspaceDialog, WorkspaceActions} from "@/components/workspaces";
import {useDebouncedValue, useOnVisible} from "@/hooks";
import type {Workspace} from "@/models";
import {useWorkspaces} from "@/queries";
import {Path, formatRelativeTime, getInitials, groupByRecency, pluralize} from "@/utils";

const WorkspaceRow = ({workspace}: { workspace: Workspace }) => (
    <li className="group relative flex items-center gap-4 px-4 py-3.5 transition-colors hover:bg-muted/50 md:px-5">
        <div
            className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-sm font-semibold text-secondary-foreground ring-1 ring-primary/10">
            {getInitials(workspace.name, workspace.name)}
        </div>
        <div className="min-w-0 flex-1">
            <div className="flex min-w-0 items-center gap-2">
                <Link
                    to={Path.getWorkspacePath(workspace.id)}
                    className="truncate font-medium outline-none after:absolute after:inset-0 focus-visible:after:ring-3 focus-visible:after:ring-ring/50 focus-visible:after:ring-inset"
                >
                    {workspace.name}
                </Link>
                {workspace.unseen_update_count > 0 && (
                    <span className="shrink-0 rounded-full bg-primary px-1.5 text-[0.7rem] font-semibold text-primary-foreground tabular-nums">
                        {workspace.unseen_update_count} new
                    </span>
                )}
            </div>
            <p className="line-clamp-1 text-sm text-muted-foreground">
                {workspace.last_question ?? "No questions yet"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground md:hidden">
                {[
                    pluralize(workspace.paper_count, "paper"),
                    pluralize(workspace.question_count, "question"),
                    formatRelativeTime(workspace.last_activity_at),
                ].join(" · ")}
            </p>
        </div>
        <div className="hidden shrink-0 items-center gap-4 text-xs text-muted-foreground md:flex">
            <span className="flex w-24 items-center gap-1.5">
                <LibraryIcon className="size-3.5"/> {pluralize(workspace.paper_count, "paper")}
            </span>
            <span className="flex w-28 items-center gap-1.5">
                <MessageCircleQuestionIcon className="size-3.5"/> {pluralize(workspace.question_count, "question")}
            </span>
            <span className="w-24 text-right">{formatRelativeTime(workspace.last_activity_at)}</span>
        </div>
        <div className="relative z-10 shrink-0">
            <WorkspaceActions
                workspace={workspace}
                trigger={
                    <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${workspace.name}`}>
                        <MoreHorizontalIcon/>
                    </Button>
                }
            />
        </div>
    </li>
);

const RowsSkeleton = () => (
    <div className="divide-y rounded-xl border">
        {Array.from({length: 6}, (_, index) => (
            <div key={index} className="flex items-center gap-4 px-5 py-4">
                <Skeleton className="size-10 rounded-lg"/>
                <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-1/3"/>
                    <Skeleton className="h-3 w-2/3"/>
                </div>
                <Skeleton className="hidden h-3 w-64 md:block"/>
            </div>
        ))}
    </div>
);

const STEPS = [
    {icon: MessageCircleQuestionIcon, title: "Ask a question", text: "Write it the way you'd ask a colleague."},
    {icon: SparklesIcon, title: "IndexR finds the papers", text: "It looks through its papers and finds new ones online when needed."},
    {icon: BookOpenCheckIcon, title: "Get a cited answer", text: "Every claim links to the exact section and page."},
];

const Onboarding = ({onCreate}: { onCreate: () => void }) => (
    <div className="rounded-xl border bg-muted/20 px-6 py-12 text-center md:px-12">
        <h2 className="text-lg font-semibold">Create your first workspace</h2>
        <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">
            A workspace holds one research topic: your questions, the cited answers and the papers behind them.
        </p>
        <div className="mx-auto mt-8 grid max-w-3xl gap-4 text-left sm:grid-cols-3">
            {STEPS.map(({icon: Icon, title, text}, index) => (
                <div key={title} className="rounded-lg border bg-background p-4">
                    <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                        <span className="flex size-5 items-center justify-center rounded-full bg-primary text-primary-foreground">{index + 1}</span>
                        <Icon className="size-3.5"/>
                    </div>
                    <p className="mt-3 text-sm font-medium">{title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{text}</p>
                </div>
            ))}
        </div>
        <Button className="mt-8" onClick={onCreate}>
            <PlusIcon data-icon="inline-start"/> New workspace
        </Button>
    </div>
);

export const Home = () => {
    const [creating, setCreating] = useState(false);
    const [search, setSearch] = useState("");
    const query = useDebouncedValue(search.trim());
    const workspaces = useWorkspaces(query);
    const sentinel = useRef<HTMLDivElement>(null);
    useOnVisible(sentinel, workspaces.fetchNextPage, workspaces.hasNextPage && !workspaces.isFetchingNextPage);

    const items = workspaces.data?.pages.flatMap((page) => page.results) ?? [];
    const groups = groupByRecency(items, (workspace) => workspace.last_activity_at);
    const searching = query.length > 0;

    const body = () => {
        if (workspaces.isPending) return <RowsSkeleton/>;
        if (workspaces.isError) {
            return <ErrorPlaceholder className="min-h-[50vh] rounded-xl border" description="We couldn't load your workspaces."
                                     onRetry={() => workspaces.refetch()}/>;
        }
        if (!items.length && !searching) return <Onboarding onCreate={() => setCreating(true)}/>;
        if (!items.length) {
            return (
                <Empty className="rounded-xl border py-16">
                    <EmptyHeader>
                        <EmptyMedia variant="icon"><SearchXIcon/></EmptyMedia>
                        <EmptyTitle>No workspaces match “{query}”</EmptyTitle>
                        <EmptyDescription>Try a different name, or clear the search.</EmptyDescription>
                    </EmptyHeader>
                    <Button variant="outline" onClick={() => setSearch("")}>Clear search</Button>
                </Empty>
            );
        }
        return (
            <div className="space-y-8">
                {groups.map((group) => (
                    <section key={group.label} aria-labelledby={`group-${group.label}`}>
                        <h2 id={`group-${group.label}`}
                            className="mb-2 px-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                            {group.label}
                        </h2>
                        <ul className="divide-y overflow-hidden rounded-xl border bg-card">
                            {group.items.map((workspace) => <WorkspaceRow key={workspace.id} workspace={workspace}/>)}
                        </ul>
                    </section>
                ))}
                <div ref={sentinel} className="flex justify-center">
                    {workspaces.isFetchingNextPage && <Spinner className="text-muted-foreground"/>}
                </div>
            </div>
        );
    };

    return (
        <>
            <AppHeader/>
            <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 md:px-8 md:py-10">
                <div className="flex flex-wrap items-end justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-semibold tracking-tight">Workspaces</h1>
                        <p className="mt-1 text-sm text-muted-foreground">
                            Pick up where you left off, or start a new research topic.
                        </p>
                    </div>
                    <Button onClick={() => setCreating(true)}>
                        <PlusIcon data-icon="inline-start"/> New workspace
                    </Button>
                </div>

                <div className="mt-6 mb-8 flex items-center gap-3">
                    <InputGroup className="max-w-md">
                        <InputGroupInput
                            value={search}
                            onChange={(event) => setSearch(event.target.value)}
                            placeholder="Search workspaces"
                            aria-label="Search workspaces"
                        />
                        <InputGroupAddon><SearchIcon/></InputGroupAddon>
                        {search && (
                            <InputGroupAddon align="inline-end">
                                {workspaces.isFetching ? <Spinner/> : (
                                    <InputGroupButton size="icon-xs" aria-label="Clear search" onClick={() => setSearch("")}>
                                        <XIcon/>
                                    </InputGroupButton>
                                )}
                            </InputGroupAddon>
                        )}
                    </InputGroup>
                </div>

                {body()}
            </main>
            <CreateWorkspaceDialog open={creating} onOpenChange={setCreating}/>
        </>
    );
};

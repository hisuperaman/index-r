import {useCallback, useEffect, useState} from "react";
import {Link, useParams} from "react-router";
import {ChevronDownIcon, RadarIcon, SearchXIcon} from "lucide-react";
import {AppHeader, BreadcrumbSlash, ErrorPlaceholder} from "@/components";
import {Button} from "@/components/ui/button";
import {Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle} from "@/components/ui/empty";
import {Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle} from "@/components/ui/sheet";
import {Skeleton} from "@/components/ui/skeleton";
import {WorkspaceActions} from "@/components/workspaces";
import {RoutePaths} from "@/enums";
import {useMediaQuery, useTrackingSheet} from "@/hooks";
import {useWorkspace} from "@/queries";
import {Path} from "@/utils";
import {ChatPanel, PanelToggle, PapersPanel, TrackingSheet} from "./components";

const PANEL_STORAGE_KEY = "indexr-papers-panel";

const readPanelPreference = (): boolean => {
    try {
        return localStorage.getItem(PANEL_STORAGE_KEY) !== "closed";
    } catch {
        return true;
    }
};

const savePanelPreference = (open: boolean) => {
    try {
        localStorage.setItem(PANEL_STORAGE_KEY, open ? "open" : "closed");
    } catch {
        // The preference is a convenience; without storage the panel simply opens by default.
    }
};

const WorkspacesLink = () => (
    <Link
        to={Path.getExactRoutePath(RoutePaths.empty)}
        className="shrink-0 rounded-md text-sm text-muted-foreground transition-colors outline-none hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50"
    >
        Workspaces
    </Link>
);

const WorkspaceView = ({workspaceId}: { workspaceId: string }) => {
    const workspace = useWorkspace(workspaceId);
    const wide = useMediaQuery("(min-width: 1024px)");
    const [panelOpen, setPanelOpen] = useState(readPanelPreference);
    const [sheetOpen, setSheetOpen] = useState(false);
    const tracking = useTrackingSheet(workspace.data);

    const togglePapers = useCallback(() => {
        if (!wide) return setSheetOpen((open) => !open);
        setPanelOpen((open) => {
            savePanelPreference(!open);
            return !open;
        });
    }, [wide]);

    useEffect(() => {
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key.toLowerCase() === "b" && (event.metaKey || event.ctrlKey)) {
                event.preventDefault();
                togglePapers();
            }
        };
        window.addEventListener("keydown", onKeyDown);
        return () => window.removeEventListener("keydown", onKeyDown);
    }, [togglePapers]);

    if (workspace.isError) {
        if (workspace.error.response?.status === 404) {
            return (
                <>
                    <AppHeader breadcrumb={<WorkspacesLink/>}/>
                    <Empty className="flex-1">
                        <EmptyHeader>
                            <EmptyMedia variant="icon"><SearchXIcon/></EmptyMedia>
                            <EmptyTitle>This workspace doesn't exist</EmptyTitle>
                            <EmptyDescription>It may have been deleted, or the link is wrong.</EmptyDescription>
                        </EmptyHeader>
                        <EmptyContent>
                            <Button nativeButton={false} render={<Link to={Path.getExactRoutePath(RoutePaths.empty)}/>}>
                                Back to workspaces
                            </Button>
                        </EmptyContent>
                    </Empty>
                </>
            );
        }
        return (
            <>
                <AppHeader breadcrumb={<WorkspacesLink/>}/>
                <ErrorPlaceholder description="We couldn't load this workspace." onRetry={() => workspace.refetch()}/>
            </>
        );
    }


    return (
        <div className="flex h-svh flex-col">
            <AppHeader
                breadcrumb={
                    <>
                        <span className="hidden items-center gap-2 sm:flex">
                            <WorkspacesLink/>
                            <BreadcrumbSlash/>
                        </span>
                        {workspace.data ? (
                            <WorkspaceActions
                                workspace={workspace.data}
                                align="start"
                                trigger={
                                    <Button variant="ghost" size="sm" className="-ml-1 min-w-0 max-w-full gap-1 px-2 font-medium">
                                        <span className="truncate">{workspace.data.name}</span>
                                        <ChevronDownIcon className="text-muted-foreground"/>
                                    </Button>
                                }
                            />
                        ) : <Skeleton className="h-5 w-48"/>}
                    </>
                }
                actions={workspace.data && (
                    <Button variant="ghost" size="sm" onClick={tracking.show} aria-label="Tracking and updates">
                        <RadarIcon data-icon="inline-start"/>
                        <span className="hidden sm:inline">Tracking</span>
                        {workspace.data.unseen_update_count > 0 && (
                            <span className="rounded-full bg-primary px-1.5 text-[0.7rem] font-semibold text-primary-foreground tabular-nums">
                                {workspace.data.unseen_update_count}
                            </span>
                        )}
                    </Button>
                )}
            />

            <div className="flex min-h-0 flex-1">
                {wide && panelOpen && workspace.data && (
                    <aside className="w-80 shrink-0 border-r bg-muted/20 xl:w-96" aria-label="Workspace papers">
                        <PapersPanel workspace={workspace.data} onCollapse={togglePapers}/>
                    </aside>
                )}

                <div className="relative flex min-w-0 flex-1 flex-col">
                    {!(wide && panelOpen) && (
                        <PanelToggle open={false} onClick={togglePapers}
                                     className="absolute top-3 left-3 z-10 bg-background/80 shadow-sm ring-1 ring-border backdrop-blur"/>
                    )}
                    {workspace.data ? <ChatPanel workspace={workspace.data} onShowUpdates={tracking.show}/> : <div className="flex-1"/>}
                </div>
            </div>

            {workspace.data && (
                <TrackingSheet workspace={workspace.data} open={tracking.open} seenBefore={tracking.seenBefore}
                               onOpenChange={tracking.setOpen}/>
            )}

            {!wide && workspace.data && (
                <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
                    <SheetContent side="left" className="w-full gap-0 p-0 sm:max-w-md">
                        <SheetHeader className="sr-only">
                            <SheetTitle>Papers</SheetTitle>
                            <SheetDescription>The papers in this workspace.</SheetDescription>
                        </SheetHeader>
                        <PapersPanel workspace={workspace.data} inSheet/>
                    </SheetContent>
                </Sheet>
            )}
        </div>
    );
};

export const WorkspacePage = () => {
    const {workspaceId = ""} = useParams();
    return <WorkspaceView key={workspaceId} workspaceId={workspaceId}/>;
};

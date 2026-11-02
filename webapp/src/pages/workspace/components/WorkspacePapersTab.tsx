import {useId, useRef, useState} from "react";
import {ExternalLinkIcon, FileTextIcon, LibraryIcon, XIcon} from "lucide-react";
import {ConfirmDialog} from "@/components";
import {Button} from "@/components/ui/button";
import {Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle} from "@/components/ui/empty";
import {ScrollArea} from "@/components/ui/scroll-area";
import {Skeleton} from "@/components/ui/skeleton";
import {Spinner} from "@/components/ui/spinner";
import {Switch} from "@/components/ui/switch";
import {toast} from "@/components/ui/toast";
import {useOnVisible} from "@/hooks";
import type {Paper, Workspace} from "@/models";
import {useRemoveWorkspacePaper, useUpdateWorkspace, useWorkspacePapers} from "@/queries";
import {cn} from "@/lib/utils.ts";
import {IconAction, PaperCard} from "./PaperCard.tsx";

const ScopeSwitch = ({workspace}: { workspace: Workspace }) => {
    const id = useId();
    const update = useUpdateWorkspace(workspace.id);
    const on = workspace.papers_only;

    const toggle = (checked: boolean) => update.mutate({papers_only: checked}, {
        onError: () => toast.add({title: "Couldn't change the setting", description: "Please try again.", type: "error"}),
    });

    return (
        <label
            htmlFor={id}
            className={cn(
                "flex cursor-pointer items-start gap-3 rounded-2xl border p-3 transition-colors",
                on ? "border-primary/30 bg-secondary" : "bg-muted/40 hover:bg-muted/70",
            )}
        >
            <div className="min-w-0 flex-1 space-y-0.5">
                <p className="text-sm font-medium">Answer only from these papers</p>
                <p className="text-xs text-muted-foreground">
                    {on
                        ? "Answers only use the papers in this list."
                        : "All papers: IndexR may find new papers automatically, and papers cited in answers are added here."}
                </p>
            </div>
            <Switch id={id} checked={on} disabled={update.isPending} onCheckedChange={toggle} className="mt-0.5"/>
        </label>
    );
};

/** The papers the user keeps in the workspace, with the switch that limits answers to them. */
export const WorkspacePapersTab = ({workspace, onAdd}: { workspace: Workspace; onAdd: () => void }) => {
    const papers = useWorkspacePapers(workspace.id);
    const removePaper = useRemoveWorkspacePaper(workspace.id);
    const [removing, setRemoving] = useState<Paper | null>(null);
    const sentinel = useRef<HTMLDivElement>(null);
    useOnVisible(sentinel, papers.fetchNextPage, papers.hasNextPage && !papers.isFetchingNextPage);

    const items = papers.data?.pages.flatMap((page) => page.results) ?? [];

    const confirmRemove = () => {
        if (!removing) return;
        removePaper.mutate(removing.id, {
            onSuccess: () => {
                toast.add({title: "Removed from workspace", description: removing.title, type: "success"});
                setRemoving(null);
            },
            onError: () => toast.add({title: "Couldn't remove the paper", description: "Please try again.", type: "error"}),
        });
    };

    return (
        <ScrollArea className="min-h-0 flex-1">
            <div className="space-y-3 p-3">
                <ScopeSwitch workspace={workspace}/>

                {papers.isPending && Array.from({length: 3}, (_, index) => <Skeleton key={index} className="h-24 rounded-2xl"/>)}

                {papers.isError && (
                    <div className="space-y-2 py-8 text-center text-sm text-muted-foreground">
                        <p>Couldn't load the papers.</p>
                        <Button size="sm" variant="outline" onClick={() => papers.refetch()}>Retry</Button>
                    </div>
                )}

                {papers.isSuccess && !items.length && (
                    <Empty className="py-8">
                        <EmptyHeader>
                            <EmptyMedia variant="icon"><LibraryIcon/></EmptyMedia>
                            <EmptyTitle className="text-sm">No papers yet</EmptyTitle>
                            <EmptyDescription className="text-xs">
                                Papers cited in answers are added here automatically. You can also add your own.
                            </EmptyDescription>
                        </EmptyHeader>
                        <Button size="sm" variant="outline" onClick={onAdd}>Add papers</Button>
                    </Empty>
                )}

                <ul className="space-y-2">
                    {items.map(({paper}) => (
                        <PaperCard
                            key={paper.id}
                            paper={paper}
                            actions={
                                <>
                                    {paper.pdf_url && (
                                        <IconAction label="Open PDF" nativeButton={false}
                                                    render={<a href={paper.pdf_url} target="_blank" rel="noreferrer"/>}>
                                            <FileTextIcon/>
                                        </IconAction>
                                    )}
                                    {paper.url && (
                                        <IconAction label="Open paper page" nativeButton={false}
                                                    render={<a href={paper.url} target="_blank" rel="noreferrer"/>}>
                                            <ExternalLinkIcon/>
                                        </IconAction>
                                    )}
                                    <IconAction label="Remove from workspace" onClick={() => setRemoving(paper)}>
                                        <XIcon/>
                                    </IconAction>
                                </>
                            }
                        />
                    ))}
                </ul>
                <div ref={sentinel} className="flex justify-center">
                    {papers.isFetchingNextPage && <Spinner className="text-muted-foreground"/>}
                </div>
            </div>

            <ConfirmDialog
                open={!!removing}
                onOpenChange={(open) => !open && setRemoving(null)}
                title="Remove this paper?"
                description={
                    <>
                        “{removing?.title}” will be removed from this workspace's list. Past answers keep their
                        sources.{!workspace.papers_only && " If a later answer cites it, it'll be added back."}
                    </>
                }
                confirmLabel="Remove paper"
                destructive
                pending={removePaper.isPending}
                onConfirm={confirmRemove}
            />
        </ScrollArea>
    );
};

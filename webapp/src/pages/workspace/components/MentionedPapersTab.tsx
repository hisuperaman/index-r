import {useRef, useState} from "react";
import {CheckIcon, PlusIcon, QuoteIcon} from "lucide-react";
import {ConfirmDialog} from "@/components";
import {Badge} from "@/components/ui/badge";
import {Button} from "@/components/ui/button";
import {Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle} from "@/components/ui/empty";
import {ScrollArea} from "@/components/ui/scroll-area";
import {Skeleton} from "@/components/ui/skeleton";
import {Spinner} from "@/components/ui/spinner";
import {toast} from "@/components/ui/toast";
import {useOnVisible} from "@/hooks";
import type {MentionedPaper, Workspace} from "@/models";
import {useAddWorkspacePaper, useMentionedPapers} from "@/queries";
import {formatRelativeTime} from "@/utils";
import {PaperCard} from "./PaperCard.tsx";

/** Every paper the workspace's answers have cited, with a way to keep it in the workspace. */
export const MentionedPapersTab = ({workspace}: { workspace: Workspace }) => {
    const mentioned = useMentionedPapers(workspace.id);
    const addPaper = useAddWorkspacePaper(workspace.id);
    const [adding, setAdding] = useState<MentionedPaper | null>(null);
    const sentinel = useRef<HTMLDivElement>(null);
    useOnVisible(sentinel, mentioned.fetchNextPage, mentioned.hasNextPage && !mentioned.isFetchingNextPage);

    const items = mentioned.data?.pages.flatMap((page) => page.results) ?? [];

    const confirmAdd = () => {
        if (!adding) return;
        addPaper.mutate(adding.id, {
            onSuccess: () => {
                toast.add({title: "Added to workspace", description: adding.title, type: "success"});
                setAdding(null);
            },
            onError: () => toast.add({title: "Couldn't add the paper", description: "Please try again.", type: "error"}),
        });
    };

    return (
        <ScrollArea className="min-h-0 flex-1">
            <div className="space-y-3 p-3">
                <p className="px-1 text-xs text-muted-foreground">
                    Every paper cited in this workspace's answers.
                </p>

                {mentioned.isPending && Array.from({length: 3}, (_, index) => <Skeleton key={index} className="h-24 rounded-2xl"/>)}

                {mentioned.isError && (
                    <div className="space-y-2 py-8 text-center text-sm text-muted-foreground">
                        <p>Couldn't load the mentioned papers.</p>
                        <Button size="sm" variant="outline" onClick={() => mentioned.refetch()}>Retry</Button>
                    </div>
                )}

                {mentioned.isSuccess && !items.length && (
                    <Empty className="py-8">
                        <EmptyHeader>
                            <EmptyMedia variant="icon"><QuoteIcon/></EmptyMedia>
                            <EmptyTitle className="text-sm">Nothing cited yet</EmptyTitle>
                            <EmptyDescription className="text-xs">
                                Papers cited in answers will appear here.
                            </EmptyDescription>
                        </EmptyHeader>
                    </Empty>
                )}

                <ul className="space-y-2">
                    {items.map((paper) => (
                        <PaperCard
                            key={paper.id}
                            paper={paper}
                            detail={`Cited ${paper.mention_count}× · ${formatRelativeTime(paper.last_mentioned_at)}`}
                            actions={paper.in_workspace ? (
                                <Badge variant="secondary"><CheckIcon/> In workspace</Badge>
                            ) : (
                                <Button size="xs" variant="outline" onClick={() => setAdding(paper)}>
                                    <PlusIcon/> Add
                                </Button>
                            )}
                        />
                    ))}
                </ul>
                <div ref={sentinel} className="flex justify-center">
                    {mentioned.isFetchingNextPage && <Spinner className="text-muted-foreground"/>}
                </div>
            </div>

            <ConfirmDialog
                open={!!adding}
                onOpenChange={(open) => !open && setAdding(null)}
                title="Add this paper to the workspace?"
                description={<>“{adding?.title}” will join this workspace's papers.{workspace.papers_only && " Answers will be able to use it."}</>}
                confirmLabel="Add paper"
                pending={addPaper.isPending}
                onConfirm={confirmAdd}
            />
        </ScrollArea>
    );
};

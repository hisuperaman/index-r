import {useRef, useState} from "react";
import {CheckIcon, PlusIcon, SearchIcon} from "lucide-react";
import type {AxiosError} from "axios";
import {ConfirmDialog} from "@/components";
import {Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle} from "@/components/ui/dialog";
import {Button} from "@/components/ui/button";
import {InputGroup, InputGroupAddon, InputGroupInput} from "@/components/ui/input-group";
import {ScrollArea} from "@/components/ui/scroll-area";
import {Skeleton} from "@/components/ui/skeleton";
import {Spinner} from "@/components/ui/spinner";
import {toast} from "@/components/ui/toast";
import {useDebouncedValue, useOnVisible} from "@/hooks";
import type {Paper} from "@/models";
import {MIN_PAPER_SEARCH_LENGTH, useAddWorkspacePaper, usePaperSearch} from "@/queries";
import {formatAuthors, formatPaperMeta} from "@/utils";

interface AddPaperDialogProps {
    workspaceId: string;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    paperIds: Set<string>;
}

const Hint = ({children}: { children: string }) => (
    <p className="px-1 py-10 text-center text-sm text-muted-foreground">{children}</p>
);

export const AddPaperDialog = ({workspaceId, open, onOpenChange, paperIds}: AddPaperDialogProps) => {
    const [search, setSearch] = useState("");
    const [added, setAdded] = useState<Set<string>>(new Set());
    const query = useDebouncedValue(search.trim());
    const results = usePaperSearch(query);
    const addPaper = useAddWorkspacePaper(workspaceId);
    const [confirming, setConfirming] = useState<Paper | null>(null);
    const sentinel = useRef<HTMLDivElement>(null);
    useOnVisible(sentinel, results.fetchNextPage, open && results.hasNextPage && !results.isFetchingNextPage);

    const add = (paper: Paper) => addPaper.mutate(paper.id, {
        onSuccess: () => {
            setAdded((previous) => new Set(previous).add(paper.id));
            setConfirming(null);
            toast.add({title: "Added to workspace", description: paper.title, type: "success"});
        },
        onError: (error: AxiosError) => {
            if ((error.response?.data as { paper_id?: string[] } | undefined)?.paper_id) {
                setAdded((previous) => new Set(previous).add(paper.id));
                setConfirming(null);
                return;
            }
            toast.add({title: "Couldn't add the paper", description: "Please try again.", type: "error"});
        },
    });

    const onOpenChangeAndReset = (next: boolean) => {
        if (!next) {
            setSearch("");
            setAdded(new Set());
        }
        onOpenChange(next);
    };

    const papers = results.data?.pages.flatMap((page) => page.results) ?? [];

    const body = () => {
        if (query.length < MIN_PAPER_SEARCH_LENGTH) return <Hint>Search by title or DOI.</Hint>;
        if (results.isPending) {
            return (
                <div className="space-y-2 p-1">
                    {Array.from({length: 4}, (_, index) => <Skeleton key={index} className="h-16 rounded-xl"/>)}
                </div>
            );
        }
        if (results.isError) return <Hint>Search failed. Please try again.</Hint>;
        if (!papers.length) {
            return <Hint>No matching papers yet. Ask a question about the topic and IndexR will find new ones.</Hint>;
        }
        return (
            <>
            <ul className="space-y-2 p-1">
                {papers.map((paper) => {
                    const inWorkspace = paperIds.has(paper.id) || added.has(paper.id);
                                    const meta = [formatAuthors(paper.authors), formatPaperMeta(paper)].filter(Boolean).join(" · ");
                    return (
                        <li key={paper.id} className="flex items-center gap-3 rounded-xl border p-3">
                            <div className="min-w-0 flex-1">
                                <p className="line-clamp-2 text-sm leading-snug font-medium">{paper.title}</p>
                                {meta && <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">{meta}</p>}
                            </div>
                            <Button
                                size="sm"
                                variant={inWorkspace ? "secondary" : "outline"}
                                disabled={inWorkspace}
                                onClick={() => setConfirming(paper)}
                                className="shrink-0"
                            >
                                {inWorkspace ? <CheckIcon/> : <PlusIcon/>}
                                {inWorkspace ? "Added" : "Add"}
                            </Button>
                        </li>
                    );
                })}
            </ul>
            <div ref={sentinel} className="flex justify-center py-2">
                {results.isFetchingNextPage && <Spinner className="text-muted-foreground"/>}
            </div>
            </>
        );
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChangeAndReset}>
            <DialogContent className="gap-4 sm:max-w-xl">
                <DialogHeader>
                    <DialogTitle>Add papers</DialogTitle>
                    <DialogDescription>Search for papers to add to this workspace.</DialogDescription>
                </DialogHeader>
                <InputGroup>
                    <InputGroupInput
                        autoFocus
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        placeholder="e.g. Attention Is All You Need"
                        aria-label="Search papers"
                    />
                    <InputGroupAddon><SearchIcon/></InputGroupAddon>
                    {results.isFetching && query.length >= MIN_PAPER_SEARCH_LENGTH && (
                        <InputGroupAddon align="inline-end"><Spinner/></InputGroupAddon>
                    )}
                </InputGroup>
                <ScrollArea className="-mx-1 max-h-[min(24rem,60vh)]">{body()}</ScrollArea>
                <ConfirmDialog
                    open={!!confirming}
                    onOpenChange={(next) => !next && setConfirming(null)}
                    title="Add this paper to the workspace?"
                    description={<>“{confirming?.title}” will join this workspace's papers.</>}
                    confirmLabel="Add paper"
                    pending={addPaper.isPending}
                    onConfirm={() => confirming && add(confirming)}
                />
            </DialogContent>
        </Dialog>
    );
};

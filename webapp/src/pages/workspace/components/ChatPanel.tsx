import {useRef} from "react";
import {ArrowRightIcon, MessageSquareTextIcon, RadarIcon} from "lucide-react";
import {ErrorPlaceholder} from "@/components";
import {Button} from "@/components/ui/button";
import {Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle} from "@/components/ui/empty";
import {Skeleton} from "@/components/ui/skeleton";
import {Spinner} from "@/components/ui/spinner";
import {useAsk, useOnVisible} from "@/hooks";
import type {Workspace} from "@/models";
import {useMessages} from "@/queries";
import {Composer} from "./Composer.tsx";
import {MessageItem} from "./MessageItem.tsx";
import {PendingTurn} from "./PendingTurn.tsx";

const suggestionsFor = (topic: string) => [
    `What are the key papers on ${topic}?`,
    `How has ${topic} changed since 2020?`,
    `Which datasets and metrics are used to evaluate ${topic}?`,
];

const MessagesSkeleton = () => (
    <div className="space-y-8">
        <Skeleton className="ml-auto h-10 w-2/3 rounded-2xl"/>
        <div className="flex gap-3">
            <Skeleton className="size-7 rounded-lg"/>
            <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-full"/>
                <Skeleton className="h-4 w-11/12"/>
                <Skeleton className="h-4 w-3/5"/>
            </div>
        </div>
    </div>
);

const sinceFormat = new Intl.DateTimeFormat(undefined, {month: "short", day: "numeric"});

const UpdatesBanner = ({workspace, onShow}: { workspace: Workspace; onShow: () => void }) => {
    const count = workspace.unseen_update_count;
    const label = `${count} ${count === 1 ? "update" : "updates"}`;
    return (
        <div className="pointer-events-none absolute inset-x-0 top-3 z-10 flex justify-center px-14">
            <button
                type="button"
                onClick={onShow}
                className="pointer-events-auto flex max-w-full items-center gap-2 rounded-full border border-primary/20 bg-background/90 py-1.5 pr-2 pl-3 text-sm shadow-sm backdrop-blur transition-colors outline-none animate-in fade-in slide-in-from-top-2 hover:bg-secondary focus-visible:ring-3 focus-visible:ring-ring/50"
            >
                <RadarIcon className="size-4 shrink-0 text-primary"/>
                <span className="truncate">
                    <span className="font-medium">{label}</span>
                    {workspace.updates_seen_at
                        ? ` since ${sinceFormat.format(new Date(workspace.updates_seen_at))}`
                        : " from tracking"}
                </span>
                <span className="flex shrink-0 items-center gap-0.5 font-medium text-primary">
                    View <ArrowRightIcon className="size-3.5"/>
                </span>
            </button>
        </div>
    );
};

export const ChatPanel = ({workspace, onShowUpdates}: { workspace: Workspace; onShowUpdates: () => void }) => {
    const messages = useMessages(workspace.id);
    const {state, ask, stop, dismiss} = useAsk(workspace.id);
    const sentinel = useRef<HTMLDivElement>(null);
    useOnVisible(sentinel, messages.fetchNextPage, messages.hasNextPage && !messages.isFetchingNextPage);

    const items = messages.data?.pages.flatMap((page) => page.results) ?? [];
    const streaming = state.status === "streaming";
    const showEmpty = messages.isSuccess && !items.length && state.status === "idle";

    return (
        <div className="relative flex min-h-0 flex-1 flex-col">
            {workspace.unseen_update_count > 0 && <UpdatesBanner workspace={workspace} onShow={onShowUpdates}/>}
            <div className="flex min-h-0 flex-1 flex-col-reverse overflow-y-auto overscroll-contain">
                <div className="mx-auto flex w-full max-w-3xl flex-col-reverse gap-8 px-4 py-6 md:px-6">
                    {state.status !== "idle" && (
                        <PendingTurn
                            state={state}
                            showQuestion={!items.some((message) => message.id === state.questionId)}
                            onRetry={ask}
                            onDismiss={dismiss}
                        />
                    )}

                    {items.map((message) => <MessageItem key={message.id} message={message}/>)}

                    {messages.isPending && <MessagesSkeleton/>}

                    {messages.isError && (
                        <ErrorPlaceholder className="min-h-[40vh]" description="We couldn't load this conversation."
                                          onRetry={() => messages.refetch()}/>
                    )}

                    {showEmpty && (
                        <Empty className="min-h-[50vh]">
                            <EmptyHeader>
                                <EmptyMedia variant="icon"><MessageSquareTextIcon/></EmptyMedia>
                                <EmptyTitle>Ask your first question</EmptyTitle>
                                <EmptyDescription>
                                    IndexR finds the right papers, looks for new ones when it needs to, and answers
                                    with sources you can trace to the exact section and page.
                                </EmptyDescription>
                            </EmptyHeader>
                            <EmptyContent className="w-full max-w-md">
                                {suggestionsFor(workspace.name).map((suggestion) => (
                                    <Button
                                        key={suggestion}
                                        variant="outline"
                                        className="h-auto w-full justify-start py-2 text-left whitespace-normal"
                                        onClick={() => ask(suggestion)}
                                    >
                                        {suggestion}
                                    </Button>
                                ))}
                            </EmptyContent>
                        </Empty>
                    )}

                    <div ref={sentinel} className="flex justify-center">
                        {messages.isFetchingNextPage && <Spinner className="text-muted-foreground"/>}
                    </div>
                </div>
            </div>

            <div className="shrink-0 bg-gradient-to-t from-background via-background to-background/0 px-4 pt-2 pb-4 md:px-6">
                <Composer streaming={streaming} onSubmit={ask} onStop={stop}/>
                <p className="mt-2 text-center text-[0.7rem] text-muted-foreground">
                    {workspace.papers_only
                        ? "Answering only from the papers in this workspace's list. Change this in the Papers panel."
                        : "Every answer links to its sources. Check them for anything important."}
                </p>
            </div>
        </div>
    );
};

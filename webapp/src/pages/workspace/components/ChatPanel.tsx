import {useRef} from "react";
import {MessageSquareTextIcon} from "lucide-react";
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

export const ChatPanel = ({workspace}: { workspace: Workspace }) => {
    const messages = useMessages(workspace.id);
    const {state, ask, stop, dismiss} = useAsk(workspace.id);
    const sentinel = useRef<HTMLDivElement>(null);
    useOnVisible(sentinel, messages.fetchNextPage, messages.hasNextPage && !messages.isFetchingNextPage);

    const items = messages.data?.pages.flatMap((page) => page.results) ?? [];
    const streaming = state.status === "streaming";
    const showEmpty = messages.isSuccess && !items.length && state.status === "idle";

    return (
        <div className="flex min-h-0 flex-1 flex-col">
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

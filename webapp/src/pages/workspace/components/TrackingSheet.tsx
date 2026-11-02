import {type FormEvent, useRef, useState} from "react";
import {CheckIcon, FileClockIcon, PlusIcon, QuoteIcon, RadarIcon, SparklesIcon, XIcon} from "lucide-react";
import {Badge} from "@/components/ui/badge";
import {Button} from "@/components/ui/button";
import {Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle} from "@/components/ui/empty";
import {Field, FieldError} from "@/components/ui/field";
import {Input} from "@/components/ui/input";
import {ScrollArea} from "@/components/ui/scroll-area";
import {Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle} from "@/components/ui/sheet";
import {Skeleton} from "@/components/ui/skeleton";
import {Spinner} from "@/components/ui/spinner";
import {toast} from "@/components/ui/toast";
import {useOnVisible} from "@/hooks";
import type {TrackingUpdate, Workspace} from "@/models";
import {useAddTopic, useAddWorkspacePaper, useRemoveTopic, useTopics, useUpdates} from "@/queries";
import {formatRelativeTime} from "@/utils";
import {PaperCard} from "./PaperCard.tsx";

const MAX_TOPICS = 10;

const Topics = ({workspace}: { workspace: Workspace }) => {
    const topics = useTopics(workspace.id);
    const addTopic = useAddTopic(workspace.id);
    const removeTopic = useRemoveTopic(workspace.id);
    const [query, setQuery] = useState("");
    const [error, setError] = useState<string | null>(null);
    const items = topics.data ?? [];
    const full = items.length >= MAX_TOPICS;
    const suggestion = items.length ? null : workspace.name;

    const add = (value: string) => {
        if (!value.trim()) return setError("Type a topic to track, like “retrieval augmented generation”.");
        addTopic.mutate(value.trim(), {
            onSuccess: (topic) => {
                setQuery("");
                setError(null);
                toast.add({
                    title: "Tracking started",
                    description: `Looking for new papers on “${topic.query}” now, then every day.`,
                    type: "success",
                });
            },
            onError: (failure) => {
                const data = failure.response?.data as { query?: string[] } | undefined;
                setError(data?.query?.[0] ?? "We couldn't track this topic. Please try again.");
            },
        });
    };

    const submit = (event: FormEvent) => {
        event.preventDefault();
        add(query);
    };

    return (
        <section className="space-y-3">
            <div>
                <h3 className="text-sm font-semibold">Topics</h3>
                <p className="text-xs text-muted-foreground">New papers on these topics show up below.</p>
            </div>

            {topics.isPending && <Skeleton className="h-7 w-2/3 rounded-full"/>}
            {!!items.length && (
                <ul className="flex flex-wrap gap-1.5">
                    {items.map((topic) => (
                        <li key={topic.id}
                            className="flex max-w-full items-center gap-1 rounded-full border bg-secondary py-0.5 pr-0.5 pl-3 text-sm text-secondary-foreground">
                            <span className="truncate">{topic.query}</span>
                            <Button
                                variant="ghost"
                                size="icon-xs"
                                className="rounded-full"
                                aria-label={`Stop tracking ${topic.query}`}
                                disabled={removeTopic.isPending}
                                onClick={() => removeTopic.mutate(topic.id, {
                                    onSuccess: () => toast.add({title: "Stopped tracking", description: topic.query, type: "success"}),
                                    onError: () => toast.add({title: "Couldn't stop tracking", description: "Please try again.", type: "error"}),
                                })}
                            >
                                <XIcon/>
                            </Button>
                        </li>
                    ))}
                </ul>
            )}

            {!full && (
                <form onSubmit={submit}>
                    <Field data-invalid={!!error}>
                        <div className="flex gap-2">
                            <Input
                                value={query}
                                onChange={(event) => setQuery(event.target.value)}
                                placeholder="Add a topic, e.g. sparse attention"
                                maxLength={255}
                                aria-label="Topic to track"
                                aria-invalid={!!error}
                                disabled={addTopic.isPending}
                            />
                            <Button type="submit" variant="outline" disabled={addTopic.isPending}>
                                {addTopic.isPending ? <Spinner/> : <PlusIcon data-icon="inline-start"/>} Track
                            </Button>
                        </div>
                        {error && <FieldError>{error}</FieldError>}
                    </Field>
                </form>
            )}
            {suggestion && topics.isSuccess && (
                <Button size="sm" variant="secondary" className="max-w-full" disabled={addTopic.isPending}
                        onClick={() => add(suggestion)}>
                    <SparklesIcon data-icon="inline-start"/>
                    <span className="truncate">Track “{suggestion}”</span>
                </Button>
            )}
        </section>
    );
};

const reasonFor = (update: TrackingUpdate) => {
    switch (update.kind) {
        case "new_paper":
            return {icon: SparklesIcon, text: <>New paper on <span className="font-medium text-foreground">“{update.topic?.query}”</span></>};
        case "new_citation":
            return {icon: QuoteIcon, text: <>Cites <span className="font-medium text-foreground">{update.cited_paper?.title}</span></>};
        case "new_version":
            return {icon: FileClockIcon, text: "New version on arXiv"};
    }
};

const UpdateItem = ({update, isNew, workspaceId}: { update: TrackingUpdate; isNew: boolean; workspaceId: string }) => {
    const addPaper = useAddWorkspacePaper(workspaceId);
    const {icon: Icon, text} = reasonFor(update);

    return (
        <li className="space-y-1.5">
            <div className="flex items-start gap-1.5 px-1 text-xs text-muted-foreground">
                <Icon className="mt-px size-3.5 shrink-0 text-primary"/>
                <p className="line-clamp-2 min-w-0 flex-1">{text}</p>
                {isNew && <Badge className="h-4 px-1.5 text-[0.65rem]">New</Badge>}
            </div>
            <ul>
                <PaperCard
                    paper={update.paper}
                    detail={`Found ${formatRelativeTime(update.created_at)}`}
                    actions={update.in_workspace ? (
                        <Badge variant="secondary"><CheckIcon/> In workspace</Badge>
                    ) : (
                        <Button
                            size="xs"
                            variant="outline"
                            disabled={addPaper.isPending}
                            onClick={() => addPaper.mutate(update.paper.id, {
                                onSuccess: () => toast.add({title: "Added to workspace", description: update.paper.title, type: "success"}),
                                onError: () => toast.add({title: "Couldn't add the paper", description: "Please try again.", type: "error"}),
                            })}
                        >
                            {addPaper.isPending ? <Spinner/> : <PlusIcon/>} Add
                        </Button>
                    )}
                />
            </ul>
        </li>
    );
};

const Updates = ({workspace, seenBefore}: { workspace: Workspace; seenBefore: string }) => {
    const updates = useUpdates(workspace.id);
    const sentinel = useRef<HTMLDivElement>(null);
    useOnVisible(sentinel, updates.fetchNextPage, updates.hasNextPage && !updates.isFetchingNextPage);
    const items = updates.data?.pages.flatMap((page) => page.results) ?? [];

    return (
        <section className="space-y-3">
            <div>
                <h3 className="text-sm font-semibold">Updates</h3>
                <p className="text-xs text-muted-foreground">
                    New papers on your topics, and new citations and versions of the papers you track.
                </p>
            </div>

            {updates.isPending && Array.from({length: 2}, (_, index) => <Skeleton key={index} className="h-28 rounded-2xl"/>)}

            {updates.isError && (
                <div className="space-y-2 py-6 text-center text-sm text-muted-foreground">
                    <p>Couldn't load the updates.</p>
                    <Button size="sm" variant="outline" onClick={() => updates.refetch()}>Retry</Button>
                </div>
            )}

            {updates.isSuccess && !items.length && (
                <Empty className="py-6">
                    <EmptyHeader>
                        <EmptyMedia variant="icon"><RadarIcon/></EmptyMedia>
                        <EmptyTitle className="text-sm">No updates yet</EmptyTitle>
                        <EmptyDescription className="text-xs">
                            Track a topic above, or track a paper from the Papers panel. IndexR checks right away,
                            then every day.
                        </EmptyDescription>
                    </EmptyHeader>
                </Empty>
            )}

            <ul className="space-y-4">
                {items.map((update) => (
                    <UpdateItem key={update.id} update={update} workspaceId={workspace.id}
                                isNew={new Date(update.created_at) > new Date(seenBefore)}/>
                ))}
            </ul>
            <div ref={sentinel} className="flex justify-center">
                {updates.isFetchingNextPage && <Spinner className="text-muted-foreground"/>}
            </div>
        </section>
    );
};

interface TrackingSheetProps {
    workspace: Workspace;
    open: boolean;
    seenBefore: string;
    onOpenChange: (open: boolean) => void;
}

/** The workspace's tracked topics and what tracking found. */
export const TrackingSheet = ({workspace, open, seenBefore, onOpenChange}: TrackingSheetProps) => (
    <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="right" className="w-full gap-0 p-0 sm:max-w-md">
            <SheetHeader className="border-b pr-12">
                <SheetTitle className="flex items-center gap-2"><RadarIcon className="size-4 text-primary"/> Tracking</SheetTitle>
                <SheetDescription>IndexR checks every day and lists what it finds here.</SheetDescription>
            </SheetHeader>
            <ScrollArea className="min-h-0 flex-1">
                <div className="space-y-8 p-4">
                    <Topics workspace={workspace}/>
                    <Updates workspace={workspace} seenBefore={seenBefore}/>
                </div>
            </ScrollArea>
        </SheetContent>
    </Sheet>
);

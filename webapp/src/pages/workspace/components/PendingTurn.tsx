import {CircleAlertIcon, RotateCcwIcon} from "lucide-react";
import {Alert, AlertAction, AlertDescription, AlertTitle} from "@/components/ui/alert";
import {Button} from "@/components/ui/button";
import {Spinner} from "@/components/ui/spinner";
import type {AskState} from "@/hooks";
import {AnswerMarkdown} from "./AnswerMarkdown.tsx";
import {AssistantAvatar, UserBubble} from "./MessageItem.tsx";

interface PendingTurnProps {
    state: Exclude<AskState, { status: "idle" }>;
    showQuestion: boolean;
    onRetry: (question: string) => void;
    onDismiss: () => void;
}

/** The question being answered, with the answer's progress, partial text or failure. */
export const PendingTurn = ({state, showQuestion, onRetry, onDismiss}: PendingTurnProps) => (
    <div className="space-y-6">
        {showQuestion && <UserBubble content={state.question}/>}

        {state.status === "error" ? (
            <Alert variant="destructive">
                <CircleAlertIcon/>
                <AlertTitle>Couldn't generate a response</AlertTitle>
                <AlertDescription>{state.message}</AlertDescription>
                <AlertAction className="flex gap-1">
                    <Button size="xs" variant="ghost" onClick={onDismiss}>Dismiss</Button>
                    <Button size="xs" variant="outline" onClick={() => onRetry(state.question)}>
                        <RotateCcwIcon data-icon="inline-start"/> Retry
                    </Button>
                </AlertAction>
            </Alert>
        ) : (
            <div className="flex gap-3" aria-live="polite" aria-busy="true">
                <AssistantAvatar/>
                <div className="min-w-0 flex-1">
                    {state.content ? (
                        <AnswerMarkdown content={state.content}/>
                    ) : (
                        <div className="space-y-1.5 pt-1">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Spinner className="size-3.5"/>
                                <span className="animate-pulse">{state.label}…</span>
                            </div>
                            {state.stage === "discovering" && (
                                <p className="text-xs text-muted-foreground">
                                    Looking for new papers on this topic. This can take a moment.
                                </p>
                            )}
                            {state.stage === "ingesting" && (
                                <p className="text-xs text-muted-foreground">
                                    Reading the new papers it found. This can take up to a minute.
                                </p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        )}
    </div>
);

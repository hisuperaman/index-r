import {useCallback, useEffect, useRef, useState} from "react";
import {useQueryClient} from "@tanstack/react-query";
import {AskStreamError, streamAsk} from "@/api";
import type {AskStage} from "@/models";
import {queryKeys} from "@/queries";

export type AskState =
    | { status: "idle" }
    | { status: "streaming"; question: string; questionId?: string; stage: AskStage | null; label: string; content: string }
    | { status: "error"; question: string; questionId?: string; message: string };

const IDLE: AskState = {status: "idle"};
const ANSWER_FAILED = "Something went wrong while generating the answer. Please try again.";

/** Streams answers to questions asked in a workspace, refreshing its messages and papers when each one lands. */
export const useAsk = (workspaceId: string) => {
    const queryClient = useQueryClient();
    const [state, setState] = useState<AskState>(IDLE);
    const controller = useRef<AbortController | null>(null);

    const refresh = useCallback(() => Promise.all([
        queryClient.invalidateQueries({queryKey: queryKeys.messages(workspaceId)}),
        queryClient.invalidateQueries({queryKey: queryKeys.workspacePapers(workspaceId)}),
        queryClient.invalidateQueries({queryKey: queryKeys.mentionedPapers(workspaceId)}),
        queryClient.invalidateQueries({queryKey: queryKeys.workspaces}),
    ]), [queryClient, workspaceId]);

    useEffect(() => () => controller.current?.abort(), [workspaceId]);

    const ask = useCallback(async (question: string) => {
        controller.current?.abort();
        const current = new AbortController();
        controller.current = current;
        setState({status: "streaming", question, stage: null, label: "Sending your question", content: ""});

        let failure: string | null = null;
        let questionId: string | undefined;
        try {
            await streamAsk(workspaceId, question, (event) => {
                switch (event.event) {
                    case "question":
                        questionId = event.data.id;
                        setState((previous) => previous.status === "streaming"
                            ? {...previous, questionId} : previous);
                        break;
                    case "status":
                        setState((previous) => previous.status === "streaming"
                            ? {...previous, stage: event.data.stage, label: event.data.label} : previous);
                        break;
                    case "delta":
                        setState((previous) => previous.status === "streaming"
                            ? {...previous, content: event.data.content} : previous);
                        break;
                    case "error":
                        failure = event.data.detail;
                        break;
                }
            }, current.signal);
        } catch (error) {
            if (current.signal.aborted) {
                await refresh();
                setState(IDLE);
                return;
            }
            failure = (error instanceof AskStreamError && error.fields?.content?.[0]) || ANSWER_FAILED;
        }

        await refresh();
        if (controller.current === current) {
            setState(failure ? {status: "error", question, questionId, message: failure} : IDLE);
        }
    }, [workspaceId, refresh]);

    const stop = useCallback(() => controller.current?.abort(), []);
    const dismiss = useCallback(() => setState(IDLE), []);

    return {state, ask, stop, dismiss};
};

import {getAuthToken} from "@/account";
import {refreshAccessToken} from "@/api/IndexR.ts";
import {Workspaces} from "@/api/Workspaces.ts";
import type {AskStreamEvent} from "@/models";

export class AskStreamError extends Error {
    readonly status?: number;
    readonly fields?: Record<string, string[]>;

    constructor(message: string, status?: number, fields?: Record<string, string[]>) {
        super(message);
        this.status = status;
        this.fields = fields;
    }
}

const post = (url: string, content: string, token: string | undefined, signal: AbortSignal) =>
    fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
            ...(token ? {Authorization: `Bearer ${token}`} : {}),
        },
        body: JSON.stringify({content}),
        signal,
    });

const parseEvent = (block: string): AskStreamEvent | null => {
    let event = "";
    const data: string[] = [];
    for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data.push(line.slice(5).trim());
    }
    if (!event || !data.length) return null;
    return {event, data: JSON.parse(data.join("\n"))} as AskStreamEvent;
};

/** Posts a question and calls `onEvent` for each server-sent event until the stream ends. */
export const streamAsk = async (
    workspaceId: string,
    content: string,
    onEvent: (event: AskStreamEvent) => void,
    signal: AbortSignal,
): Promise<void> => {
    const url = Workspaces.messagesStreamUrl(workspaceId);
    let response = await post(url, content, getAuthToken(), signal);
    if (response.status === 401) {
        response = await post(url, content, await refreshAccessToken(), signal);
    }

    if (!response.ok || !response.body) {
        const body = await response.json().catch(() => ({}));
        throw new AskStreamError("Couldn't send your question.", response.status, body);
    }

    const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = "";
    for (; ;) {
        const {value, done} = await reader.read();
        if (done) break;
        buffer += value;
        let boundary = buffer.indexOf("\n\n");
        while (boundary !== -1) {
            const event = parseEvent(buffer.slice(0, boundary));
            buffer = buffer.slice(boundary + 2);
            if (event) onEvent(event);
            boundary = buffer.indexOf("\n\n");
        }
    }
};

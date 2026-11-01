import type {Chunk} from "./Paper.ts";

export type MessageRole = "user" | "assistant";

export type AskStage = "expanding" | "searching" | "discovering" | "ingesting" | "answering";

export interface MessageCitation {
	number: number;
	chunk: Chunk;
}

export interface Message {
	id: string;
	role: MessageRole;
	content: string;
	created_at: string;
	citations: MessageCitation[];
}

export type AskStreamEvent =
	| { event: "question"; data: Message }
	| { event: "status"; data: { stage: AskStage; label: string } }
	| { event: "delta"; data: { content: string } }
	| { event: "message"; data: Message }
	| { event: "error"; data: { detail: string } };

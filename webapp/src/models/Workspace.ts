import type {PrimaryModel} from "@/models";
import type {Paper, PaperBasic} from "./Paper.ts";

export interface Workspace extends PrimaryModel {
	name: string;
	papers_only: boolean;
	paper_count: number;
	question_count: number;
	last_question: string | null;
	last_activity_at: string;
	unseen_update_count: number;
	updates_seen_at: string | null;
}

export interface WorkspacePaper {
	paper: Paper;
	created_at: string;
	tracked: boolean;
	tracked_at: string | null;
}

export interface TrackedTopic {
	id: string;
	query: string;
	created_at: string;
	checked_at: string | null;
}

export type TrackingUpdateKind = "new_paper" | "new_citation" | "new_version";

export interface TrackingUpdate {
	id: string;
	kind: TrackingUpdateKind;
	created_at: string;
	paper: Paper;
	topic: TrackedTopic | null;
	cited_paper: PaperBasic | null;
	in_workspace: boolean;
}

import type {PrimaryModel} from "@/models";
import type {Paper} from "./Paper.ts";

export interface Workspace extends PrimaryModel {
	name: string;
	papers_only: boolean;
	paper_count: number;
	question_count: number;
	last_question: string | null;
	last_activity_at: string;
}

export interface WorkspacePaper {
	paper: Paper;
	created_at: string;
}

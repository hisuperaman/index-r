export type DatePrecision = "day" | "month" | "year";

export interface PaperBasic {
	id: string;
	title: string;
	doi: string | null;
	venue: string | null;
	citation_count: number | null;
	publication_date: string | null;
	publication_date_precision: DatePrecision | null;
	url: string;
	pdf_url: string | null;
	revised_at: string | null;
	is_private: boolean;
}

export interface Paper extends PaperBasic {
	authors: string[];
}

export interface Chunk {
	id: number;
	paper: PaperBasic;
	heading: string | null;
	text: string;
	start_page: number;
	end_page: number;
	chunk_index: number;
	citation: string;
}

export interface MentionedPaper extends Paper {
	mention_count: number;
	last_mentioned_at: string;
	in_workspace: boolean;
}

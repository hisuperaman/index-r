export interface PageInfo {
	page: number;
	page_size: number;
}

export interface CursorPagination<T> {
	next: string | null;
	previous: string | null;
	results: T[];
}

export interface PagePagination<T> extends CursorPagination<T> {
	count: number;
}

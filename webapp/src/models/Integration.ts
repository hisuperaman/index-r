export interface ApiToken {
	id: string;
	name: string;
	prefix: string;
	created_at: string;
	last_used_at: string | null;
	token?: string;
}

export interface McpServer {
	url: string;
}

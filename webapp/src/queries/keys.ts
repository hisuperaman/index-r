export const queryKeys = {
    socialAccounts: ["user", "social-accounts"] as const,
    workspaces: ["workspaces", "list"] as const,
    workspaceSearch: (search: string) => ["workspaces", "list", search] as const,
    workspace: (id: string) => ["workspaces", "detail", id] as const,
    workspacePapers: (id: string) => ["workspaces", "detail", id, "papers"] as const,
    mentionedPapers: (id: string) => ["workspaces", "detail", id, "mentioned-papers"] as const,
    messages: (id: string) => ["workspaces", "detail", id, "messages"] as const,
    paperSearch: (search: string) => ["papers", "search", search] as const,
};

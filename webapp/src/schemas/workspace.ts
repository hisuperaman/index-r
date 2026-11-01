import {z} from "zod";

export const workspaceSchema = z.object({
    name: z.string().trim().min(1, "Give the workspace a name").max(255, "Keep the name under 255 characters"),
});

export type WorkspaceFormData = z.infer<typeof workspaceSchema>;

export type WorkspaceUpdate = Partial<WorkspaceFormData & { papers_only: boolean }>;

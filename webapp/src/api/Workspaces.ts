import IndexR from "@/api/IndexR.ts";
import type {CursorPagination} from "@/definitions/Pagination.ts";
import type {MentionedPaper, Message, TrackedTopic, TrackingUpdate, Workspace, WorkspacePaper} from "@/models";
import type {WorkspaceFormData, WorkspaceUpdate} from "@/schemas";

export class Workspaces extends IndexR {

    public static readonly url = "/api/workspaces";

    public static list(search = ""): Promise<CursorPagination<Workspace>> {
        return this.get(`${Workspaces.url}/`, search ? {search} : {});
    }

    public static retrieve(id: string): Promise<Workspace> {
        return this.get(`${Workspaces.url}/${id}/`);
    }

    public static create(data: WorkspaceFormData): Promise<Workspace> {
        return this.post(`${Workspaces.url}/`, data);
    }

    public static update(id: string, data: WorkspaceUpdate): Promise<Workspace> {
        return this.patch(`${Workspaces.url}/${id}/`, data);
    }

    public static remove(id: string): Promise<void> {
        return this.delete(`${Workspaces.url}/${id}/`);
    }

    public static listPapers(id: string): Promise<CursorPagination<WorkspacePaper>> {
        return this.get(`${Workspaces.url}/${id}/papers/`);
    }

    public static addPaper(id: string, paperId: string): Promise<WorkspacePaper> {
        return this.post(`${Workspaces.url}/${id}/papers/`, {paper_id: paperId});
    }

    public static trackPaper(id: string, paperId: string, tracked: boolean): Promise<WorkspacePaper> {
        return this.patch(`${Workspaces.url}/${id}/papers/${paperId}/`, {tracked});
    }

    public static listTopics(id: string): Promise<TrackedTopic[]> {
        return this.get(`${Workspaces.url}/${id}/topics/`);
    }

    public static addTopic(id: string, query: string): Promise<TrackedTopic> {
        return this.post(`${Workspaces.url}/${id}/topics/`, {query});
    }

    public static removeTopic(id: string, topicId: string): Promise<void> {
        return this.delete(`${Workspaces.url}/${id}/topics/${topicId}/`);
    }

    public static listUpdates(id: string): Promise<CursorPagination<TrackingUpdate>> {
        return this.get(`${Workspaces.url}/${id}/updates/`);
    }

    public static markUpdatesSeen(id: string): Promise<void> {
        return this.post(`${Workspaces.url}/${id}/updates/seen/`, {});
    }

    public static removePaper(id: string, paperId: string): Promise<void> {
        return this.delete(`${Workspaces.url}/${id}/papers/${paperId}/`);
    }

    public static listMentionedPapers(id: string): Promise<CursorPagination<MentionedPaper>> {
        return this.get(`${Workspaces.url}/${id}/mentioned-papers/`);
    }

    public static listMessages(id: string): Promise<CursorPagination<Message>> {
        return this.get(`${Workspaces.url}/${id}/messages/`);
    }

    public static messagesStreamUrl(id: string): string {
        return `${Workspaces.url}/${id}/messages/stream/`;
    }
}

import {keepPreviousData, useInfiniteQuery, useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import type {AxiosError} from "axios";
import {Workspaces} from "@/api";
import type {Workspace, WorkspacePaper} from "@/models";
import type {WorkspaceFormData, WorkspaceUpdate} from "@/schemas";
import {queryKeys} from "./keys.ts";
import {cursorPages} from "./pagination.ts";

export const useWorkspaces = (search = "") =>
    useInfiniteQuery({
        queryKey: queryKeys.workspaceSearch(search),
        ...cursorPages(() => Workspaces.list(search)),
        placeholderData: keepPreviousData,
    });

export const useWorkspace = (id: string) =>
    useQuery<Workspace, AxiosError>({
        queryKey: queryKeys.workspace(id),
        queryFn: () => Workspaces.retrieve(id),
        retry: (count, error) => error.response?.status !== 404 && count < 2,
    });

export const useCreateWorkspace = () => {
    const queryClient = useQueryClient();
    return useMutation<Workspace, AxiosError, WorkspaceFormData>({
        mutationFn: (data) => Workspaces.create(data),
        onSuccess: (workspace) => {
            queryClient.setQueryData(queryKeys.workspace(workspace.id), workspace);
            return queryClient.invalidateQueries({queryKey: queryKeys.workspaces});
        },
    });
};

export const useUpdateWorkspace = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation<Workspace, AxiosError, WorkspaceUpdate>({
        mutationFn: (data) => Workspaces.update(id, data),
        onSuccess: (workspace) => {
            queryClient.setQueryData(queryKeys.workspace(id), workspace);
            return queryClient.invalidateQueries({queryKey: queryKeys.workspaces});
        },
    });
};

export const useDeleteWorkspace = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation<void, AxiosError>({
        mutationFn: () => Workspaces.remove(id),
        onSuccess: () => {
            queryClient.removeQueries({queryKey: queryKeys.workspace(id)});
            return queryClient.invalidateQueries({queryKey: queryKeys.workspaces});
        },
    });
};

export const useWorkspacePapers = (id: string) =>
    useInfiniteQuery({
        queryKey: queryKeys.workspacePapers(id),
        ...cursorPages(() => Workspaces.listPapers(id)),
    });

export const useAddWorkspacePaper = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation<WorkspacePaper, AxiosError, string>({
        mutationFn: (paperId) => Workspaces.addPaper(id, paperId),
        onSuccess: () => Promise.all([
            queryClient.invalidateQueries({queryKey: queryKeys.workspacePapers(id)}),
            queryClient.invalidateQueries({queryKey: queryKeys.mentionedPapers(id)}),
            queryClient.invalidateQueries({queryKey: queryKeys.workspaces}),
        ]),
    });
};

export const useRemoveWorkspacePaper = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation<void, AxiosError, string>({
        mutationFn: (paperId) => Workspaces.removePaper(id, paperId),
        onSuccess: () => Promise.all([
            queryClient.invalidateQueries({queryKey: queryKeys.workspacePapers(id)}),
            queryClient.invalidateQueries({queryKey: queryKeys.mentionedPapers(id)}),
            queryClient.invalidateQueries({queryKey: queryKeys.workspaces}),
        ]),
    });
};

export const useMessages = (id: string) =>
    useInfiniteQuery({
        queryKey: queryKeys.messages(id),
        ...cursorPages(() => Workspaces.listMessages(id)),
    });

export const useMentionedPapers = (id: string) =>
    useInfiniteQuery({
        queryKey: queryKeys.mentionedPapers(id),
        ...cursorPages(() => Workspaces.listMentionedPapers(id)),
    });

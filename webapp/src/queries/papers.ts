import {keepPreviousData, useInfiniteQuery, useMutation, useQueryClient} from "@tanstack/react-query";
import type {AxiosError} from "axios";
import {Papers, Workspaces} from "@/api";
import type {Paper} from "@/models";
import {queryKeys} from "./keys.ts";
import {cursorPages} from "./pagination.ts";

export const MIN_PAPER_SEARCH_LENGTH = 2;

export const usePaperSearch = (search: string) =>
    useInfiniteQuery({
        queryKey: queryKeys.paperSearch(search),
        ...cursorPages(() => Papers.search(search)),
        enabled: search.length >= MIN_PAPER_SEARCH_LENGTH,
        placeholderData: keepPreviousData,
        staleTime: 30_000,
    });

/** Uploads a private PDF and adds it to the workspace. */
export const useUploadPaper = (workspaceId: string) => {
    const queryClient = useQueryClient();
    return useMutation<Paper, AxiosError, { file: File; title: string }>({
        mutationFn: async ({file, title}) => {
            const paper = await Papers.upload(file, title);
            await Workspaces.addPaper(workspaceId, paper.id).catch((error: AxiosError) => {
                const alreadyAdded = (error.response?.data as { paper_id?: string[] } | undefined)?.paper_id;
                if (!alreadyAdded) throw error;
            });
            return paper;
        },
        onSuccess: () => Promise.all([
            queryClient.invalidateQueries({queryKey: queryKeys.workspacePapers(workspaceId)}),
            queryClient.invalidateQueries({queryKey: queryKeys.workspaces}),
            queryClient.invalidateQueries({queryKey: ["papers", "search"]}),
        ]),
    });
};

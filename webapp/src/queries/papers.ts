import {keepPreviousData, useInfiniteQuery} from "@tanstack/react-query";
import {Papers} from "@/api";
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

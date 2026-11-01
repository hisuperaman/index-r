import IndexR from "@/api/IndexR.ts";
import type {CursorPagination} from "@/definitions/Pagination.ts";

/** Options for a cursor-paginated `useInfiniteQuery` whose first page comes from `fetchFirst`. */
export const cursorPages = <T, >(fetchFirst: () => Promise<CursorPagination<T>>) => ({
    initialPageParam: null as string | null,
    queryFn: ({pageParam}: { pageParam: string | null }): Promise<CursorPagination<T>> =>
        pageParam ? IndexR.getNextPage<T>(pageParam) : fetchFirst(),
    getNextPageParam: (lastPage: CursorPagination<T>) => lastPage.next,
});

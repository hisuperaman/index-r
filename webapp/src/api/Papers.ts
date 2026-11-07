import IndexR from "@/api/IndexR.ts";
import type {CursorPagination} from "@/definitions/Pagination.ts";
import type {Paper} from "@/models";

export class Papers extends IndexR {

    public static readonly url = "/api/papers";

    public static upload(file: File, title: string): Promise<Paper> {
        const data = new FormData();
        data.append("file", file);
        if (title.trim()) data.append("title", title.trim());
        return this.post(`${Papers.url}/`, data);
    }

    public static search(search: string): Promise<CursorPagination<Paper>> {
        return this.get(`${Papers.url}/`, {search, page_size: 20});
    }
}

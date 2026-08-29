import Requests from "@/api/Requests.ts";
import {AxiosError, AxiosHeaders, type AxiosRequestConfig} from "axios";
import cookie from "react-cookies";
import {isLoggedIn, onLogout} from "@/account";
import type {CursorPagination, PageInfo} from "@/definitions/Pagination.ts";

class IndexR extends Requests {

	protected static get config(): AxiosRequestConfig {
		const headers = new AxiosHeaders();
		const token = cookie.load('token');
		const csrfToken = cookie.load('csrftoken');
		if (token) headers.set('Authorization', `Token ${token}`);
        if (csrfToken) headers.set('X-CSRFToken', csrfToken);
        return {headers, paramsSerializer: {indexes: null}};
	}

	public static get(url: string, params: NonNullable<unknown> = {}, signal?: AbortSignal, pageInfo: PageInfo = {} as PageInfo) {
		return super.get(url, Object.assign({}, params, pageInfo), signal);
	}

	public static getNextPage<T>(url: string): Promise<CursorPagination<T>> {
		return this.getAbsolute(url);
	}

	protected static handleError(error: AxiosError) {
		if ((error.response?.status === 401) && isLoggedIn()) {
			onLogout();
		}
		if (error.response?.data) {
			const {data} = error.response;
			if (data instanceof Object) {
				Object.values(data).forEach((messages: string | string[]) =>
					error.message = messages instanceof Array ? messages.join('\n') : messages);
			}
		}
		super.handleError(error);
	}
}

export default IndexR;
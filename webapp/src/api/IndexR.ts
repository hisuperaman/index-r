import Requests from "@/api/Requests.ts";
import axios, {AxiosError, AxiosHeaders, type AxiosRequestConfig, type InternalAxiosRequestConfig} from "axios";
import cookie from "react-cookies";
import {getAuthToken, getRefreshToken, isLoggedIn, onLogout, saveAuthTokens} from "@/account";
import type {CursorPagination, PageInfo} from "@/definitions/Pagination.ts";
import type {AuthTokens} from "@/models";

const REFRESH_URL = "/api/iam/auth/token/refresh/";

let pendingRefresh: Promise<string> | null = null;

export const refreshAccessToken = (): Promise<string> => {
	pendingRefresh ??= axios.post<AuthTokens>(REFRESH_URL, {refresh: getRefreshToken()})
		.then(({data}) => {
			saveAuthTokens(data);
			return data.access;
		})
		.finally(() => {
			pendingRefresh = null;
		});
	return pendingRefresh;
}

axios.interceptors.response.use(undefined, async (error: AxiosError) => {
	const request = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
	if (error.response?.status !== 401 || !request || request._retried || request.url === REFRESH_URL || !getRefreshToken()) {
		throw error;
	}
	request._retried = true;
	request.headers.set('Authorization', `Bearer ${await refreshAccessToken()}`);
	return axios(request);
});

class IndexR extends Requests {

	protected static get config(): AxiosRequestConfig {
		const headers = new AxiosHeaders();
		const token = getAuthToken();
		const csrfToken = cookie.load('csrftoken');
		if (token) headers.set('Authorization', `Bearer ${token}`);
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
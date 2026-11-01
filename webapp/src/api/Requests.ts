import axios, {AxiosError, type AxiosRequestConfig, type AxiosResponse} from "axios";

class Requests {

	protected static baseUrl: string = '';

	protected static get config(): AxiosRequestConfig {
		return {};
	}

	public static get(url: string, params?: NonNullable<unknown>, signal?: AbortSignal) {
		return this.handleResponse(axios.get(this.buildUrl(url), {params, ...this.config, signal}));
	}

	public static getAbsolute(url: string) {
		return this.handleResponse(axios.get(url, this.config));
	}

	public static post(url: string, data?: NonNullable<unknown>) {
		return this.handleResponse(axios.post(this.buildUrl(url), data, this.config));
	}

	public static put(url: string, data?: NonNullable<unknown>) {
		return this.handleResponse(axios.put(this.buildUrl(url), data, this.config));
	}

	public static patch(url: string, data?: NonNullable<unknown>) {
		return this.handleResponse(axios.patch(this.buildUrl(url), data, this.config));
	}

	public static delete(url: string) {
		return this.handleResponse(axios.delete(this.buildUrl(url), this.config));
	}

	protected static buildUrl(url: string) {
		return `${this.baseUrl}/${url}`.replace(/\/{2,}/g, '/');
	}

	private static handleResponse(response: Promise<AxiosResponse>) {
		return response.then(({data}) => data).catch(this.handleError);
	}

	protected static handleError(error: AxiosError) {
		console.error(error);
		throw error;
	}
}

export default Requests;
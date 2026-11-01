import cookie from "react-cookies";
import type {AuthTokens, LoginResponse} from "@/models";

const ACCESS_COOKIE = "access";
const REFRESH_COOKIE = "refresh";
const REFRESH_MAX_AGE_SECONDS = 7 * 24 * 60 * 60;


export const isLoggedIn = () =>
	!!getRefreshToken();

export const onLogout = () => {
	cookie.remove(ACCESS_COOKIE, {path: "/"});
	cookie.remove(REFRESH_COOKIE, {path: "/"});
	window.sessionStorage.clear();
	window.localStorage.clear();
	window.location.reload();
}

export const getAuthToken = (): string | undefined =>
	cookie.load(ACCESS_COOKIE);

export const getRefreshToken = (): string | undefined =>
	cookie.load(REFRESH_COOKIE);

export const saveAuthTokens = ({access, refresh}: AuthTokens) => {
	cookie.save(ACCESS_COOKIE, access, {path: "/", sameSite: "lax"});
	cookie.save(REFRESH_COOKIE, refresh, {path: "/", sameSite: "lax", maxAge: REFRESH_MAX_AGE_SECONDS});
}

export const onLoginSuccess = (tokens: LoginResponse | undefined) => {
	if (!tokens?.access || !tokens.refresh) return console.error("No token received");
	saveAuthTokens(tokens);
	window.open("/", "_self");
}
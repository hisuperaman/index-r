import cookie from "react-cookies";
import type {Token} from "@/models";


export const isLoggedIn = () =>
	!!getAuthToken();

export const onLogout = () => {
	cookie.remove("token", {path: "/"});
	window.sessionStorage.clear();
	window.localStorage.clear();
	window.location.reload();
}

export const getAuthToken = (): string | undefined =>
	cookie.load("token");

export const onLoginSuccess = (token: Token | undefined) => {
	if (!token?.key) return console.error("No token received");
	cookie.save("token", token.key, {path: "/"});
	window.open("/", "_self");
}
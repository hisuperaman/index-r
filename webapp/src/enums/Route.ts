export const RoutePaths = {
	empty: "",
	login: "login",
}

export type RoutePath = (typeof RoutePaths)[keyof typeof RoutePaths];
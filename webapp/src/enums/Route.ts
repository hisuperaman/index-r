export const RoutePaths = {
    empty: "",
    login: "login",
    signup: "signup",
}

export type RoutePath = (typeof RoutePaths)[keyof typeof RoutePaths];
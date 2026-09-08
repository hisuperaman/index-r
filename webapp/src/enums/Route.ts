export const RoutePaths = {
    empty: "",
    login: "login",
    signup: "signup",
    verifyEmail: "verify-email/:key",
}

export type RoutePath = (typeof RoutePaths)[keyof typeof RoutePaths];
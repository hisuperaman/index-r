export const RoutePaths = {
    empty: "",
    login: "login",
    signup: "signup",
    verifyEmail: "verify-email/:key",
    workspace: "w/:workspaceId",
    settings: "settings",
    settingsSection: "settings/:section",
}

export type RoutePath = (typeof RoutePaths)[keyof typeof RoutePaths];

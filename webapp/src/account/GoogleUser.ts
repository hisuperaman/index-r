import {onLoginSuccess} from "./utils.ts";
import {AxiosError} from "axios";
import {IAM} from "@/api";


interface CodeClient {
    requestCode: () => void;
}

interface Google {
    accounts: {
        id: {
            intermediate?: Record<string, unknown>;
            initialize: (config: {
                client_id: string;
                callback: (res: GoogleApiIdResponse) => void;
            }) => void;
            prompt: () => void;
        };
        oauth2: {
            initCodeClient: (config: {
                client_id: string;
                scope: string;
                callback: (res: GoogleApiCodeResponse) => void;
                error_callback?: (error: { type: string }) => void;
            }) => CodeClient;
            CodeClient: CodeClient;
            GoogleIdentityServicesErrorType: {
                Pe: string;
                Ie: string;
                Le: string;
                Ke: string;
            };
        };
    };
}


declare const window: {
    gapi: unknown;
    google?: Google;
};

/** Whether Google's sign-in script has loaded. */
export const isGoogleLoaded = (): boolean => !!window.google?.accounts?.id;

/** Asks the user to pick a Google account and resolves with the one-time code to send to the server. */
export const requestGoogleCode = (): Promise<string> => new Promise((resolve, reject) => {
    if (!window.google) {
        reject(new Error("Google sign-in isn't available right now. Please try again later."));
        return;
    }
    window.google.accounts.oauth2.initCodeClient({
        client_id: import.meta.env.VITE_APP_GOOGLE_CLIENT_ID,
        scope: 'openid profile email',
        callback: (response) => response.code
            ? resolve(response.code)
            : reject(new Error("Google didn't confirm the account. Please try again.")),
        error_callback: () => reject(new Error("The Google window was closed before connecting.")),
    }).requestCode();
});

interface GoogleApiIdResponse {
    credential: string;
}

interface GoogleApiCodeResponse {
    code?: string;
    error?: string;
}

export class GoogleUser {
    codeClient: CodeClient | undefined;

    private readonly showNonFieldError: (message: string) => void;

    constructor(showNonFieldError: (message: string) => void) {
        this.showNonFieldError = showNonFieldError;

        const google = window.google!;

        google.accounts.id.initialize({
            client_id: import.meta.env.VITE_APP_GOOGLE_CLIENT_ID,
            callback: this.onIdAuthSuccess,
        });

        this.codeClient = google.accounts.oauth2.initCodeClient({
            client_id: import.meta.env.VITE_APP_GOOGLE_CLIENT_ID,
            scope: 'openid profile email',
            callback: this.onCodeAuthSuccess,
        });
    }

    onIdAuthSuccess = (response: GoogleApiIdResponse) =>
        IAM.googleTokenLogin(response.credential).then((token) => onLoginSuccess(token))
            .catch((err: AxiosError) => {
                if (err.response?.status === 400 && err.message.includes("already registered")) {
                    this.showNonFieldError("User is already registered with this email address, please login with email and password.")
                }
            })

    onCodeAuthSuccess = (response: GoogleApiCodeResponse) => {
        if (!response.code) return;
        IAM.googleCodeLogin(response.code).then((token) => onLoginSuccess(token))
            .catch((err: AxiosError) => {
                if (err.response?.status === 400 && err.message.includes("already registered")) {
                    this.showNonFieldError("User is already registered with this email address, please login with email and password.")
                }
            })
    }

    prompt = () => window.google?.accounts.id.prompt();

    login = () => {
        this.codeClient?.requestCode();
    }
}
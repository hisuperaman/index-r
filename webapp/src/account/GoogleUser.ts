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
    google: Google;
};

interface GoogleApiIdResponse {
    credential: string;
}

interface GoogleApiCodeResponse {
    code: string;
}

export class GoogleUser {
    codeClient: typeof window.google.accounts.oauth2.CodeClient | undefined;

    prompt = window.google.accounts.id.prompt;
    private readonly showNonFieldError: (message: string) => void;

    constructor(showNonFieldError: (message: string) => void) {
        this.showNonFieldError = showNonFieldError;

        window.google.accounts.id.initialize({
            client_id: import.meta.env.VITE_APP_GOOGLE_CLIENT_ID,
            callback: this.onIdAuthSuccess,
        });

        this.codeClient = window.google.accounts.oauth2.initCodeClient({
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
        IAM.googleCodeLogin(response.code).then((token) => onLoginSuccess(token))
            .catch((err: AxiosError) => {
                if (err.response?.status === 400 && err.message.includes("already registered")) {
                    this.showNonFieldError("User is already registered with this email address, please login with email and password.")
                }
            })
    }

    login = () => {
        this.codeClient?.requestCode();
    }
}
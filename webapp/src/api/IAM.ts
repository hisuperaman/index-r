import IndexR from "@/api/IndexR.ts";
import type {Token, User} from "@/models";
import {onLogout} from "@/account";
import type {UserFormData} from "@/schemas";
import type {RegisterResponse} from "@/definitions/ResponseBody.ts";

type AuthBody = {
    access_token: string,
    id_token: string
} | {
    code: string,
} | {
    email: string,
    password: string
}

export class IAM extends IndexR {

    private static url: string = "/iam";
    private static authUrl: string = `${IAM.url}/auth`;

    public static login(data: AuthBody): Promise<Token> {
        return this.post(`${IAM.authUrl}/login/`, data);
    }

    public static register(data: UserFormData): Promise<RegisterResponse> {
        return this.post(`${IAM.authUrl}/registration/`, data);
    }

    public static verifyEmail(token: Token): Promise<void> {
        return this.post(`${IAM.authUrl}/registration/verify-email/`, token);
    }

    public static async logout(): Promise<void> {
        return this.post(`${IAM.authUrl}/logout/`).finally(onLogout);
    }

    public static googleAuth(data: AuthBody): Promise<Token> {
        return IAM.post(`${IAM.url}/auth/google/`, data);
    }

    public static googleTokenLogin(access_token: string): Promise<Token> {
        return IAM.googleAuth({access_token, id_token: access_token});
    }

    public static googleCodeLogin(code: string): Promise<Token> {
        return IAM.googleAuth({code});
    }

    public static getUser(): Promise<User> {
        return IAM.get(`${IAM.authUrl}/user/`);
    }
}
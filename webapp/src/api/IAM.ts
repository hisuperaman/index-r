import IndexR from "@/api/IndexR.ts";
import type {LoginResponse, SocialAccount, Token, User} from "@/models";
import {getRefreshToken, onLogout} from "@/account";
import type {LoginFormData, PasswordChangeFormData, PasswordSetFormData, ProfileFormData, UserFormData} from "@/schemas";
import type {RegisterResponse} from "@/definitions/ResponseBody.ts";

type GoogleAuthBody = {
    access_token: string,
    id_token: string
} | {
    code: string,
}

export class IAM extends IndexR {

    private static url: string = "/api/iam";
    private static authUrl: string = `${IAM.url}/auth`;

    public static login(data: LoginFormData): Promise<LoginResponse> {
        return this.post(`${IAM.authUrl}/login/`, data);
    }

    public static register(data: UserFormData): Promise<RegisterResponse> {
        return this.post(`${IAM.authUrl}/registration/`, data);
    }

    public static verifyEmail(token: Token): Promise<void> {
        return this.post(`${IAM.authUrl}/registration/verify-email/`, token);
    }

    public static async logout(): Promise<void> {
        return this.post(`${IAM.authUrl}/logout/`, {refresh: getRefreshToken()}).finally(onLogout);
    }

    public static googleAuth(data: GoogleAuthBody): Promise<LoginResponse> {
        return IAM.post(`${IAM.url}/auth/google/`, data);
    }

    public static googleTokenLogin(access_token: string): Promise<LoginResponse> {
        return IAM.googleAuth({access_token, id_token: access_token});
    }

    public static googleCodeLogin(code: string): Promise<LoginResponse> {
        return IAM.googleAuth({code});
    }

    public static getUser(): Promise<User> {
        return IAM.get(`${IAM.authUrl}/user/`);
    }

    public static updateUser(data: ProfileFormData): Promise<User> {
        return IAM.patch(`${IAM.authUrl}/user/`, data);
    }

    public static listSocialAccounts(): Promise<SocialAccount[]> {
        return IAM.get(`${IAM.authUrl}/social-accounts/`);
    }

    public static connectGoogle(code: string): Promise<void> {
        return IAM.post(`${IAM.authUrl}/google/connect/`, {code});
    }

    public static disconnectSocialAccount(id: number): Promise<void> {
        return IAM.post(`${IAM.authUrl}/social-accounts/${id}/disconnect/`);
    }

    public static changePassword(data: PasswordChangeFormData | PasswordSetFormData): Promise<{ detail: string }> {
        return IAM.post(`${IAM.authUrl}/password/change/`, data);
    }
}
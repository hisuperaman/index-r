import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import {IAM} from "@/api";
import type {LoginFormData, PasswordChangeFormData, PasswordSetFormData, ProfileFormData, UserFormData} from "@/schemas";
import type {AxiosError} from "axios";
import type {RegisterResponse} from "@/definitions/ResponseBody.ts";
import type {LoginResponse, SocialAccount, Token, User} from "@/models";
import {onLogout, requestGoogleCode} from "@/account";
import {queryKeys} from "./keys.ts";

export const useRegisterUser = () =>
    useMutation<RegisterResponse, AxiosError, UserFormData>({
        mutationFn: (data: UserFormData) => IAM.register(data),
    })

export const useVerifyEmail = () =>
    useMutation<void, AxiosError, Token>({
        mutationFn: (token: Token) => IAM.verifyEmail(token),
    })

export const useLogin = () =>
    useMutation<LoginResponse, AxiosError, LoginFormData>({
        mutationFn: (data: LoginFormData) => IAM.login(data),
    })

export const useLogout = () => (
    useMutation({
        mutationFn: () => IAM.logout(),
        onSettled: () => {
            onLogout();
        },
    })
)
export const useUpdateProfile = () =>
    useMutation<User, AxiosError, ProfileFormData>({
        mutationFn: (data: ProfileFormData) => IAM.updateUser(data),
    })

export const useChangePassword = () =>
    useMutation<{ detail: string }, AxiosError, PasswordChangeFormData | PasswordSetFormData>({
        mutationFn: (data) => IAM.changePassword(data),
    })

export const useSocialAccounts = () =>
    useQuery<SocialAccount[], AxiosError>({
        queryKey: queryKeys.socialAccounts,
        queryFn: () => IAM.listSocialAccounts(),
    })

export const useConnectGoogle = () => {
    const queryClient = useQueryClient();
    return useMutation<void, AxiosError | Error>({
        mutationFn: async () => IAM.connectGoogle(await requestGoogleCode()),
        onSuccess: () => queryClient.invalidateQueries({queryKey: queryKeys.socialAccounts}),
    });
}

export const useDisconnectSocialAccount = () => {
    const queryClient = useQueryClient();
    return useMutation<void, AxiosError, number>({
        mutationFn: (id) => IAM.disconnectSocialAccount(id),
        onSuccess: () => queryClient.invalidateQueries({queryKey: queryKeys.socialAccounts}),
    });
}

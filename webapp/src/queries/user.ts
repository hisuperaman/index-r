import {useMutation} from "@tanstack/react-query";
import {IAM} from "@/api";
import type {LoginFormData, UserFormData} from "@/schemas";
import type {AxiosError} from "axios";
import type {RegisterResponse} from "@/definitions/ResponseBody.ts";
import type {LoginResponse, Token} from "@/models";
import {onLogout} from "@/account";

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
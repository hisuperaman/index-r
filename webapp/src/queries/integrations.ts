import {useMutation, useQuery, useQueryClient} from "@tanstack/react-query";
import type {AxiosError} from "axios";
import {Integrations} from "@/api";
import type {ApiToken} from "@/models";
import {queryKeys} from "./keys.ts";

export const useMcpServer = () =>
    useQuery({
        queryKey: queryKeys.mcpServer,
        queryFn: () => Integrations.mcpServer(),
        staleTime: Infinity,
    });

export const useApiTokens = () =>
    useQuery<ApiToken[], AxiosError>({
        queryKey: queryKeys.apiTokens,
        queryFn: () => Integrations.listTokens(),
    });

export const useCreateApiToken = () => {
    const queryClient = useQueryClient();
    return useMutation<ApiToken, AxiosError, string>({
        mutationFn: (name) => Integrations.createToken(name),
        onSuccess: () => queryClient.invalidateQueries({queryKey: queryKeys.apiTokens}),
    });
};

export const useRevokeApiToken = () => {
    const queryClient = useQueryClient();
    return useMutation<void, AxiosError, string>({
        mutationFn: (id) => Integrations.revokeToken(id),
        onSuccess: () => queryClient.invalidateQueries({queryKey: queryKeys.apiTokens}),
    });
};

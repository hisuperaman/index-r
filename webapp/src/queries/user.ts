import {useMutation} from "@tanstack/react-query";
import {IAM} from "@/api/IAM";
import type {RegisterBody} from "@/definitions/RequestBody";

export const useRegister = () => {
    return useMutation({
        mutationFn: (data: RegisterBody) => IAM.register(data),
    });
};
import type {AxiosError, AxiosResponse} from "axios";
import {toast} from "@/components/ui/toast";
import type {ErrorResponse} from "@/definitions/ResponseBody.ts";

export const handleApiError = <T extends Record<string, any>>(
    error: AxiosError,
    setFieldError?: (field: keyof T, message: string) => void,
    toastTitle = "An error occurred"
) => {
    const response = error.response as AxiosResponse;
    const data = response?.data as ErrorResponse<T>;

    if (!data) return;

    Object.entries(data).forEach(([key, messages]) => {
        if (key === "non_field_errors") {
            (messages as string[]).forEach((err) => {
                toast.add({title: toastTitle, description: err, type: 'error'});
            });
        } else if (setFieldError && Array.isArray(messages) && messages.length > 0) {
            setFieldError(key as keyof T, messages[0]);
        }
    });
}
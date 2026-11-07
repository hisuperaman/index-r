import {useEffect} from "react";
import {Controller, useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import type {AxiosError} from "axios";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {Button} from "@/components/ui/button";
import {Field, FieldError, FieldLabel} from "@/components/ui/field";
import {Input} from "@/components/ui/input";
import {Spinner} from "@/components/ui/spinner";
import {type WorkspaceFormData, workspaceSchema} from "@/schemas";
import {handleApiError} from "@/utils/errors";

interface WorkspaceFormDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    title: string;
    description: string;
    submitLabel: string;
    defaultName?: string;
    pending: boolean;
    onSubmit: (data: WorkspaceFormData, onError: (error: AxiosError) => void) => void;
}

export const WorkspaceFormDialog = ({
                                        open,
                                        onOpenChange,
                                        title,
                                        description,
                                        submitLabel,
                                        defaultName = "",
                                        pending,
                                        onSubmit,
                                    }: WorkspaceFormDialogProps) => {
    const form = useForm<WorkspaceFormData>({
        resolver: zodResolver(workspaceSchema),
        defaultValues: {name: defaultName},
    });

    useEffect(() => {
        if (open) form.reset({name: defaultName});
    }, [open, defaultName, form]);

    const submit = (data: WorkspaceFormData) =>
        onSubmit(data, (error) => handleApiError<WorkspaceFormData>(
            error,
            (field, message) => form.setError(field, {type: "server", message}),
            "Couldn't save the workspace",
        ));

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <form onSubmit={form.handleSubmit(submit)} className="grid gap-6">
                    <DialogHeader>
                        <DialogTitle>{title}</DialogTitle>
                        <DialogDescription>{description}</DialogDescription>
                    </DialogHeader>

                    <Controller
                        name="name"
                        control={form.control}
                        render={({field, fieldState}) => (
                            <Field data-invalid={fieldState.invalid}>
                                <FieldLabel htmlFor="workspace-name">Name</FieldLabel>
                                <Input
                                    {...field}
                                    id="workspace-name"
                                    autoFocus
                                    autoComplete="off"
                                    aria-invalid={fieldState.invalid}
                                    disabled={pending}
                                    placeholder="e.g. Sparse retrieval for long documents"
                                />
                                {fieldState.invalid && <FieldError errors={[fieldState.error]}/>}
                            </Field>
                        )}
                    />

                    <DialogFooter>
                        <DialogClose render={<Button variant="outline" disabled={pending}/>}>Cancel</DialogClose>
                        <Button type="submit" disabled={pending}>
                            {pending && <Spinner/>}
                            {submitLabel}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};

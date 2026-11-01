import type {ReactNode} from "react";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {Spinner} from "@/components/ui/spinner";

interface ConfirmDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    title: ReactNode;
    description: ReactNode;
    confirmLabel: string;
    destructive?: boolean;
    pending?: boolean;
    onConfirm: () => void;
}

/** Asks the user to confirm an action before it runs. */
export const ConfirmDialog = ({
                                  open,
                                  onOpenChange,
                                  title,
                                  description,
                                  confirmLabel,
                                  destructive = false,
                                  pending = false,
                                  onConfirm,
                              }: ConfirmDialogProps) => (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
        <AlertDialogContent>
            <AlertDialogHeader>
                <AlertDialogTitle>{title}</AlertDialogTitle>
                <AlertDialogDescription>{description}</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
                <AlertDialogCancel disabled={pending}>Cancel</AlertDialogCancel>
                <AlertDialogAction variant={destructive ? "destructive" : "default"} disabled={pending} onClick={onConfirm}>
                    {pending && <Spinner/>}
                    {confirmLabel}
                </AlertDialogAction>
            </AlertDialogFooter>
        </AlertDialogContent>
    </AlertDialog>
);

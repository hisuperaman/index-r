import {type ReactElement, useState} from "react";
import {useMatch, useNavigate} from "react-router";
import {PencilIcon, Trash2Icon} from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import {toast} from "@/components/ui/toast";
import {RoutePaths} from "@/enums";
import type {Workspace} from "@/models";
import {useDeleteWorkspace, useUpdateWorkspace} from "@/queries";
import {Path} from "@/utils";
import {WorkspaceFormDialog} from "./WorkspaceFormDialog.tsx";

interface WorkspaceActionsProps {
    workspace: Workspace;
    trigger: ReactElement;
    align?: "start" | "center" | "end";
}

/** A menu to rename or delete a workspace, opened by `trigger`. */
export const WorkspaceActions = ({workspace, trigger, align = "end"}: WorkspaceActionsProps) => {
    const navigate = useNavigate();
    const viewing = useMatch(Path.getExactRoutePath(RoutePaths.workspace))?.params.workspaceId === workspace.id;
    const [renaming, setRenaming] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const rename = useUpdateWorkspace(workspace.id);
    const remove = useDeleteWorkspace(workspace.id);

    const confirmDelete = () => remove.mutate(undefined, {
        onSuccess: () => {
            setDeleting(false);
            toast.add({title: "Workspace deleted", description: `“${workspace.name}” and its chat are gone.`, type: "success"});
            if (viewing) navigate(Path.getExactRoutePath(RoutePaths.empty));
        },
        onError: () => toast.add({title: "Couldn't delete the workspace", description: "Please try again.", type: "error"}),
    });

    return (
        <>
            <DropdownMenu>
                <DropdownMenuTrigger render={trigger}/>
                <DropdownMenuContent align={align} className="w-44">
                    <DropdownMenuItem onClick={() => setRenaming(true)}>
                        <PencilIcon/> Rename
                    </DropdownMenuItem>
                    <DropdownMenuSeparator/>
                    <DropdownMenuItem variant="destructive" onClick={() => setDeleting(true)}>
                        <Trash2Icon/> Delete
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            <WorkspaceFormDialog
                open={renaming}
                onOpenChange={setRenaming}
                title="Rename workspace"
                description="Choose a name that describes the research topic."
                submitLabel="Save"
                defaultName={workspace.name}
                pending={rename.isPending}
                onSubmit={(data, onError) => rename.mutate(data, {onSuccess: () => setRenaming(false), onError})}
            />

            <AlertDialog open={deleting} onOpenChange={setDeleting}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete “{workspace.name}”?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Its questions, answers and paper list will be deleted. This can't be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={remove.isPending}>Cancel</AlertDialogCancel>
                        <AlertDialogAction variant="destructive" disabled={remove.isPending} onClick={confirmDelete}>
                            {remove.isPending && <Spinner/>}
                            Delete workspace
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
};

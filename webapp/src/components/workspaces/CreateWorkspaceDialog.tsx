import {useNavigate} from "react-router";
import {useCreateWorkspace} from "@/queries";
import {Path} from "@/utils";
import {WorkspaceFormDialog} from "./WorkspaceFormDialog.tsx";

interface CreateWorkspaceDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export const CreateWorkspaceDialog = ({open, onOpenChange}: CreateWorkspaceDialogProps) => {
    const navigate = useNavigate();
    const createWorkspace = useCreateWorkspace();

    return (
        <WorkspaceFormDialog
            open={open}
            onOpenChange={onOpenChange}
            title="New workspace"
            description="A workspace keeps one research topic's questions, answers and papers together."
            submitLabel="Create workspace"
            pending={createWorkspace.isPending}
            onSubmit={(data, onError) => createWorkspace.mutate(data, {
                onSuccess: (workspace) => {
                    onOpenChange(false);
                    navigate(Path.getWorkspacePath(workspace.id));
                },
                onError,
            })}
        />
    );
};

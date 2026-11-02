import {useState} from "react";
import type {Workspace} from "@/models";
import {useMarkUpdatesSeen} from "@/queries";

/** Opens the tracking sheet, marking the workspace's updates seen and remembering what was new before. */
export const useTrackingSheet = (workspace: Workspace | undefined) => {
    const markSeen = useMarkUpdatesSeen(workspace?.id ?? "");
    const [open, setOpen] = useState(false);
    const [seenBefore, setSeenBefore] = useState("");

    const show = () => {
        if (!workspace) return;
        setSeenBefore(workspace.updates_seen_at ?? workspace.created_at);
        setOpen(true);
        if (workspace.unseen_update_count > 0) markSeen.mutate();
    };

    return {open, setOpen, seenBefore, show};
};

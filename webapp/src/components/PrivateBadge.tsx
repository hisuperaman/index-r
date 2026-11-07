import {LockIcon} from "lucide-react";
import {Badge} from "@/components/ui/badge";
import {cn} from "@/lib/utils.ts";

/** Marks a paper only its uploader can see. */
export const PrivateBadge = ({className}: { className?: string }) => (
    <Badge variant="secondary" className={cn("gap-1", className)} title="Only you can see this paper">
        <LockIcon/> Private
    </Badge>
);

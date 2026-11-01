import {PanelLeftCloseIcon, PanelLeftOpenIcon} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Tooltip, TooltipContent, TooltipTrigger} from "@/components/ui/tooltip";

const SHORTCUT = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘B" : "Ctrl+B";

interface PanelToggleProps {
    open: boolean;
    onClick: () => void;
    className?: string;
}

/** Shows or hides the papers panel. */
export const PanelToggle = ({open, onClick, className}: PanelToggleProps) => {
    const label = open ? "Hide papers" : "Show papers";
    return (
        <Tooltip>
            <TooltipTrigger
                render={<Button variant="ghost" size="icon-sm" onClick={onClick} aria-label={label} className={className}/>}
            >
                {open ? <PanelLeftCloseIcon/> : <PanelLeftOpenIcon/>}
            </TooltipTrigger>
            <TooltipContent side="right">
                {label} <span className="ml-1 opacity-60">{SHORTCUT}</span>
            </TooltipContent>
        </Tooltip>
    );
};

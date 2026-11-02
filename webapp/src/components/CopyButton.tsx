import {useState} from "react";
import {CheckIcon, CopyIcon} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Tooltip, TooltipContent, TooltipTrigger} from "@/components/ui/tooltip";

interface CopyButtonProps {
    text: string;
    label?: string;
    size?: "icon-xs" | "icon-sm";
}

/** Copies `text` to the clipboard, confirming with a tick. */
export const CopyButton = ({text, label = "Copy", size = "icon-xs"}: CopyButtonProps) => {
    const [copied, setCopied] = useState(false);

    const copy = async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
    };

    return (
        <Tooltip>
            <TooltipTrigger render={<Button type="button" variant="ghost" size={size} onClick={copy} aria-label={label}/>}>
                {copied ? <CheckIcon/> : <CopyIcon/>}
            </TooltipTrigger>
            <TooltipContent>{copied ? "Copied" : label}</TooltipContent>
        </Tooltip>
    );
};

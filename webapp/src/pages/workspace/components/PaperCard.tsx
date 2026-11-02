import type {ComponentProps, ReactNode} from "react";
import {PrivateBadge} from "@/components";
import {Button} from "@/components/ui/button";
import {Tooltip, TooltipContent, TooltipTrigger} from "@/components/ui/tooltip";
import type {Paper} from "@/models";
import {formatAuthors, formatPaperMeta} from "@/utils";

export const IconAction = ({label, ...props}: { label: string } & ComponentProps<typeof Button>) => (
    <Tooltip>
        <TooltipTrigger render={<Button variant="ghost" size="icon-xs" aria-label={label} {...props}/>}/>
        <TooltipContent>{label}</TooltipContent>
    </Tooltip>
);

interface PaperCardProps {
    paper: Paper;
    detail?: ReactNode;
    actions?: ReactNode;
}

/** A paper's title, authors and metadata, with a row of actions. */
export const PaperCard = ({paper, detail, actions}: PaperCardProps) => {
    const authors = formatAuthors(paper.authors);
    const meta = formatPaperMeta(paper);

    return (
        <li className="group rounded-2xl border bg-card p-3.5 transition-colors hover:bg-muted/40">
            {paper.url ? (
                <a
                    href={paper.url}
                    target="_blank"
                    rel="noreferrer"
                    className="line-clamp-2 text-sm leading-snug font-medium underline-offset-4 hover:underline"
                >
                    {paper.title}
                </a>
            ) : (
                <p className="line-clamp-2 text-sm leading-snug font-medium">{paper.title}</p>
            )}
            {paper.is_private && <PrivateBadge className="mt-1.5"/>}
            {authors && <p className="mt-1 line-clamp-1 text-xs text-muted-foreground">{authors}</p>}
            {meta && <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{meta}</p>}
            <div className="mt-2 flex min-h-7 items-center gap-1">
                {detail && <div className="min-w-0 flex-1 text-xs text-muted-foreground">{detail}</div>}
                <div className="ml-auto flex shrink-0 items-center gap-0.5">{actions}</div>
            </div>
        </li>
    );
};

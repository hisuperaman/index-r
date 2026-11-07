import {ExternalLinkIcon, FileTextIcon} from "lucide-react";
import {Popover, PopoverContent, PopoverTrigger} from "@/components/ui/popover";
import {Button} from "@/components/ui/button";
import {Separator} from "@/components/ui/separator";
import {PrivateBadge} from "@/components";
import type {MessageCitation} from "@/models";
import {formatChunkLocation, formatPaperMeta} from "@/utils";
import {cn} from "@/lib/utils.ts";

const chipClass =
    "mx-0.5 inline-flex h-[1.15rem] min-w-[1.15rem] -translate-y-px items-center justify-center rounded-md px-1 align-middle font-mono text-[0.68rem] font-medium tabular-nums";

interface CitationChipProps {
    number: number;
    citation?: MessageCitation;
}

/** An inline [n] marker that previews the cited passage and links to its paper. */
export const CitationChip = ({number, citation}: CitationChipProps) => {
    if (!citation) {
        return <span className={cn(chipClass, "bg-muted text-muted-foreground")}>{number}</span>;
    }

    const {chunk} = citation;
    const meta = formatPaperMeta(chunk.paper);

    return (
        <Popover>
            <PopoverTrigger
                openOnHover
                delay={150}
                closeDelay={100}
                aria-label={`Source ${number}: ${chunk.citation}`}
                className={cn(
                    chipClass,
                    "cursor-pointer bg-secondary text-secondary-foreground ring-1 ring-border transition-colors outline-none hover:bg-primary hover:text-primary-foreground focus-visible:ring-3 focus-visible:ring-ring/50 data-popup-open:bg-primary data-popup-open:text-primary-foreground",
                )}
            >
                {number}
            </PopoverTrigger>
            <PopoverContent side="top" align="start" className="w-[min(28rem,calc(100vw-2rem))] gap-3 p-0">
                <div className="space-y-1.5 px-4 pt-4">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className={cn(chipClass, "mx-0 translate-y-0 bg-primary text-primary-foreground")}>
                            {number}
                        </span>
                        <span>{formatChunkLocation(chunk)}</span>
                    </div>
                    <p className="text-sm leading-snug font-medium">{chunk.paper.title}</p>
                    {chunk.paper.is_private && <PrivateBadge/>}
                    {meta && <p className="text-xs text-muted-foreground">{meta}</p>}
                </div>
                <blockquote
                    className="mx-4 max-h-64 overflow-y-auto border-l-2 pr-1 pl-3 text-xs leading-relaxed whitespace-pre-line text-muted-foreground">
                    {chunk.text}
                </blockquote>
                {(chunk.paper.url || chunk.paper.pdf_url) && <Separator/>}
                <div className="flex gap-2 px-4 pb-3 empty:hidden">
                    {chunk.paper.url && (
                        <Button
                            size="xs"
                            variant="outline"
                            nativeButton={false}
                            render={<a href={chunk.paper.url} target="_blank" rel="noreferrer"/>}
                        >
                            <ExternalLinkIcon data-icon="inline-start"/> Open paper
                        </Button>
                    )}
                    {chunk.paper.pdf_url && (
                        <Button
                            size="xs"
                            variant="ghost"
                            nativeButton={false}
                            render={<a href={`${chunk.paper.pdf_url}#page=${chunk.start_page}`} target="_blank"
                                       rel="noreferrer"/>}
                        >
                            <FileTextIcon data-icon="inline-start"/> PDF, page {chunk.start_page}
                        </Button>
                    )}
                </div>
            </PopoverContent>
        </Popover>
    );
};

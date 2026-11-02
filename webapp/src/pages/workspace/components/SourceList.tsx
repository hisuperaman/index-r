import {ExternalLinkIcon} from "lucide-react";
import type {Chunk, MessageCitation} from "@/models";
import {formatChunkLocation, formatPaperYear} from "@/utils";

const Source = ({chunk, number, year}: { chunk: Chunk; number: number; year: string | null }) => {
    const body = (
        <>
            <span
                className="mt-0.5 inline-flex size-5 shrink-0 items-center justify-center rounded-md bg-secondary font-mono text-[0.68rem] font-medium">
                {number}
            </span>
            <span className="min-w-0 flex-1">
                <span className="block font-medium">{chunk.paper.title}</span>
                <span className="block text-xs text-muted-foreground">
                    {[year, formatChunkLocation(chunk), chunk.paper.is_private ? "Private" : null].filter(Boolean).join(" · ")}
                </span>
            </span>
        </>
    );
    const className = "group flex items-start gap-2.5 rounded-lg border px-3 py-2 text-sm";

    if (!chunk.paper.url) return <div className={className}>{body}</div>;
    return (
        <a
            href={chunk.paper.url}
            target="_blank"
            rel="noreferrer"
            className={`${className} transition-colors outline-none hover:bg-muted/60 focus-visible:ring-3 focus-visible:ring-ring/50`}
        >
            {body}
            <ExternalLinkIcon
                className="mt-1 size-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"/>
        </a>
    );
};

/** The passages an answer cites, numbered as in the text. */
export const SourceList = ({citations}: { citations: MessageCitation[] }) => {
    if (!citations.length) return null;

    return (
        <div className="mt-4 space-y-2">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Sources</p>
            <ol className="grid gap-1.5">
                {citations.map(({number, chunk}) => {
                    const year = formatPaperYear(chunk.paper);
                    return (
                        <li key={number}>
                            <Source chunk={chunk} number={number} year={year}/>
                        </li>
                    );
                })}
            </ol>
        </div>
    );
};

import {memo} from "react";
import Markdown, {type Components} from "react-markdown";
import remarkGfm from "remark-gfm";
import type {MessageCitation} from "@/models";
import {CitationChip} from "./CitationChip.tsx";

const CITE_PREFIX = "#cite-";
const MARKER_RE = /\[(\d+)](?!\()/g;

/** Turns each [n] marker into a link the renderer replaces with a citation chip. */
const linkMarkers = (content: string) => content.replace(MARKER_RE, `[$1](${CITE_PREFIX}$1)`);

const baseComponents: Components = {
    p: ({children}) => <p className="leading-7 [&:not(:first-child)]:mt-3">{children}</p>,
    ul: ({children}) => <ul className="my-3 ml-5 list-disc space-y-1.5 marker:text-muted-foreground">{children}</ul>,
    ol: ({children}) => <ol className="my-3 ml-5 list-decimal space-y-1.5 marker:text-muted-foreground">{children}</ol>,
    li: ({children}) => <li className="pl-1 leading-7">{children}</li>,
    h1: ({children}) => <h3 className="mt-5 mb-2 text-base font-semibold first:mt-0">{children}</h3>,
    h2: ({children}) => <h3 className="mt-5 mb-2 text-base font-semibold first:mt-0">{children}</h3>,
    h3: ({children}) => <h4 className="mt-4 mb-1.5 font-semibold first:mt-0">{children}</h4>,
    h4: ({children}) => <h4 className="mt-4 mb-1.5 font-semibold first:mt-0">{children}</h4>,
    strong: ({children}) => <strong className="font-semibold">{children}</strong>,
    blockquote: ({children}) => <blockquote className="my-3 border-l-2 pl-4 text-muted-foreground">{children}</blockquote>,
    hr: () => <hr className="my-4 border-border"/>,
    code: ({children}) => <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">{children}</code>,
    pre: ({children}) => <pre className="my-3 overflow-x-auto rounded-lg bg-muted p-3 text-xs [&_code]:bg-transparent [&_code]:p-0">{children}</pre>,
    table: ({children}) => (
        <div className="my-3 w-full overflow-x-auto rounded-lg border">
            <table className="w-full text-sm">{children}</table>
        </div>
    ),
    th: ({children}) => <th className="border-b bg-muted/50 px-3 py-2 text-left font-medium">{children}</th>,
    td: ({children}) => <td className="border-b px-3 py-2 align-top last:border-r-0">{children}</td>,
};

interface AnswerMarkdownProps {
    content: string;
    citations?: MessageCitation[];
}

/** Renders an answer's markdown with its [n] markers as citation chips. */
export const AnswerMarkdown = memo(({content, citations = []}: AnswerMarkdownProps) => {
    const byNumber = new Map(citations.map((citation) => [citation.number, citation]));

    const components: Components = {
        ...baseComponents,
        a: ({href, children}) => {
            if (href?.startsWith(CITE_PREFIX)) {
                const number = Number(href.slice(CITE_PREFIX.length));
                return <CitationChip number={number} citation={byNumber.get(number)}/>;
            }
            return (
                <a href={href} target="_blank" rel="noreferrer"
                   className="font-medium underline underline-offset-4 hover:text-muted-foreground">
                    {children}
                </a>
            );
        },
    };

    return (
        <div className="text-[0.95rem] break-words text-foreground">
            <Markdown remarkPlugins={[remarkGfm]} components={components}>{linkMarkers(content)}</Markdown>
        </div>
    );
});

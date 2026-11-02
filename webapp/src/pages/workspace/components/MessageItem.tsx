import {memo} from "react";
import {CopyButton, LogoMark} from "@/components";
import type {Message} from "@/models";
import {formatRelativeTime} from "@/utils";
import {AnswerMarkdown} from "./AnswerMarkdown.tsx";
import {SourceList} from "./SourceList.tsx";

export const UserBubble = ({content}: { content: string }) => (
    <div className="flex justify-end">
        <div
            className="max-w-[85%] rounded-2xl rounded-br-md bg-secondary px-4 py-2.5 text-[0.95rem] leading-relaxed whitespace-pre-wrap text-secondary-foreground">
            {content}
        </div>
    </div>
);

export const AssistantAvatar = () => <LogoMark className="mt-0.5 size-7 text-xs"/>;

export const MessageItem = memo(({message}: { message: Message }) => {
    if (message.role === "user") return <UserBubble content={message.content}/>;

    return (
        <div className="group flex gap-3">
            <AssistantAvatar/>
            <div className="min-w-0 flex-1">
                <AnswerMarkdown content={message.content} citations={message.citations}/>
                <SourceList citations={message.citations}/>
                <div
                    className="mt-2 flex items-center gap-1 text-xs text-muted-foreground opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100 md:focus-within:opacity-100">
                    <CopyButton text={message.content} label="Copy answer"/>
                    <span>{formatRelativeTime(message.created_at)}</span>
                </div>
            </div>
        </div>
    );
});

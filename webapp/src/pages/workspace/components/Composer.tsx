import {type FormEvent, type KeyboardEvent, useEffect, useRef, useState} from "react";
import {ArrowUpIcon, SquareIcon} from "lucide-react";
import {InputGroup, InputGroupAddon, InputGroupButton, InputGroupTextarea} from "@/components/ui/input-group";
import {Kbd} from "./Kbd.tsx";

interface ComposerProps {
    streaming: boolean;
    onSubmit: (question: string) => void;
    onStop: () => void;
}

export const Composer = ({streaming, onSubmit, onStop}: ComposerProps) => {
    const [question, setQuestion] = useState("");
    const textarea = useRef<HTMLTextAreaElement>(null);
    const canSend = !streaming && question.trim().length > 0;

    useEffect(() => {
        if (!streaming && window.matchMedia("(pointer: fine)").matches) textarea.current?.focus();
    }, [streaming]);

    const submit = (event?: FormEvent) => {
        event?.preventDefault();
        if (!canSend) return;
        onSubmit(question.trim());
        setQuestion("");
    };

    const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            submit();
        }
    };

    return (
        <form onSubmit={submit} className="mx-auto w-full max-w-3xl">
            <InputGroup className="rounded-2xl bg-background shadow-sm">
                <InputGroupTextarea
                    ref={textarea}
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    onKeyDown={onKeyDown}
                    placeholder="Ask a research question…"
                    aria-label="Your question"
                    rows={1}
                    className="max-h-48 min-h-12 px-4 pt-3.5 text-[0.95rem]"
                />
                <InputGroupAddon align="block-end" className="justify-between px-3 pb-2.5">
                    <span className="hidden text-xs text-muted-foreground sm:inline">
                        <Kbd>Enter</Kbd> to send · <Kbd>Shift</Kbd> + <Kbd>Enter</Kbd> for a new line
                    </span>
                    {streaming ? (
                        <InputGroupButton
                            type="button"
                            variant="outline"
                            size="icon-sm"
                            className="ml-auto rounded-full"
                            onClick={onStop}
                            aria-label="Stop answering"
                        >
                            <SquareIcon className="fill-current"/>
                        </InputGroupButton>
                    ) : (
                        <InputGroupButton
                            type="submit"
                            variant="default"
                            size="icon-sm"
                            className="ml-auto rounded-full"
                            disabled={!canSend}
                            aria-label="Send question"
                        >
                            <ArrowUpIcon/>
                        </InputGroupButton>
                    )}
                </InputGroupAddon>
            </InputGroup>
        </form>
    );
};

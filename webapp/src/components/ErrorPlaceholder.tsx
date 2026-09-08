import {CircleAlert} from "lucide-react";

import {
    Empty,
    EmptyContent,
    EmptyDescription,
    EmptyHeader,
    EmptyMedia,
    EmptyTitle,
} from "@/components/ui/empty";
import {Button} from "@/components/ui/button";
import {cn} from "@/lib/utils.ts";

interface ErrorPlaceholderProps {
    title?: string;
    description?: string;
    onRetry?: () => void;
    compact?: boolean;
    className?: string;
}

export const ErrorPlaceholder = ({
                                     title = "Something went wrong",
                                     description = "We couldn't load this information. Please try again.",
                                     onRetry,
                                     compact = false,
                                     className
                                 }: ErrorPlaceholderProps) => {
    if (compact) {
        return onRetry ? (
            <Button variant="secondary" onClick={onRetry} className={cn(className)}>
                <CircleAlert/> Retry
            </Button>
        ) : null;
    }

    return (
        <Empty className={cn("min-h-[75vh]", className)}>
            <EmptyHeader>
                <EmptyMedia variant="icon">
                    <CircleAlert/>
                </EmptyMedia>

                <EmptyTitle>{title}</EmptyTitle>

                <EmptyDescription>{description}</EmptyDescription>
            </EmptyHeader>

            {onRetry && (
                <EmptyContent>
                    <Button onClick={onRetry}>Try again</Button>
                </EmptyContent>
            )}
        </Empty>
    );
}
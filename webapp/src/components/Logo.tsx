import {cn} from "@/lib/utils.ts";

/** The IndexR monogram: the wordmark's R on the brand colour. */
export const LogoMark = ({className}: { className?: string }) => (
    <span
        aria-hidden="true"
        className={cn(
            "flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground select-none",
            className,
        )}
    >
        R
    </span>
);

/** The IndexR wordmark. */
export const Logo = ({className}: { className?: string }) => (
    <span className={cn("text-lg font-semibold tracking-tight select-none", className)}>
        Index<span className="text-primary">R</span>
    </span>
);

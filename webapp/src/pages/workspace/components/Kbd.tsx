import type {PropsWithChildren} from "react";

export const Kbd = ({children}: PropsWithChildren) => (
    <kbd className="rounded border bg-muted px-1 py-px font-sans text-[0.68rem] font-medium">{children}</kbd>
);

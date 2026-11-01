import type {ReactNode} from "react";
import {AppLogo} from "./AppLogo.tsx";
import {UserMenu} from "./UserMenu.tsx";

interface AppHeaderProps {
    breadcrumb?: ReactNode;
    actions?: ReactNode;
}

export const BreadcrumbSlash = () => (
    <span aria-hidden className="text-lg font-light text-muted-foreground/40 select-none">/</span>
);

export const AppHeader = ({breadcrumb, actions}: AppHeaderProps) => (
    <header className="sticky top-0 z-20 shrink-0 border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/80">
        <div className="flex h-14 items-center gap-2 px-4 md:gap-3 md:px-6">
            <AppLogo/>
            {breadcrumb && (
                <nav aria-label="Breadcrumb" className="flex min-w-0 flex-1 items-center gap-1.5 md:gap-2">
                    <BreadcrumbSlash/>
                    {breadcrumb}
                </nav>
            )}
            <div className="ml-auto flex shrink-0 items-center gap-1.5">
                {actions}
                <UserMenu/>
            </div>
        </div>
    </header>
);

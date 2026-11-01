import {Link} from "react-router";
import {LayoutGridIcon, LogOutIcon, SettingsIcon, SunIcon} from "lucide-react";
import {Avatar, AvatarFallback} from "@/components/ui/avatar";
import {Button} from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuGroup,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
    DropdownMenuSeparator,
    DropdownMenuSub,
    DropdownMenuSubContent,
    DropdownMenuSubTrigger,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {Skeleton} from "@/components/ui/skeleton";
import {THEMES, type Theme} from "@/definitions/theme.ts";
import {RoutePaths} from "@/enums";
import {useTheme, useUser} from "@/hooks";
import {useLogout} from "@/queries";
import {Path, getInitials} from "@/utils";

export const UserMenu = () => {
    const {user} = useUser();
    const {theme, setTheme} = useTheme();
    const logout = useLogout();

    if (!user) return <Skeleton className="size-8 rounded-full"/>;

    const name = `${user.first_name} ${user.last_name}`.trim();
    const initials = getInitials(name, user.email);

    return (
        <DropdownMenu>
            <DropdownMenuTrigger
                render={<Button variant="ghost" size="icon" className="rounded-full" aria-label="Account menu"/>}
            >
                <Avatar className="size-8">
                    <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                </Avatar>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60">
                <DropdownMenuGroup>
                    <DropdownMenuLabel className="flex items-center gap-2.5 py-2 font-normal">
                        <Avatar className="size-9">
                            <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                        </Avatar>
                        <div className="grid min-w-0 leading-tight">
                            <span className="truncate text-sm font-medium text-foreground">{name || user.email}</span>
                            <span className="truncate text-xs text-muted-foreground">{user.email}</span>
                        </div>
                    </DropdownMenuLabel>
                </DropdownMenuGroup>
                <DropdownMenuSeparator/>
                <DropdownMenuItem render={<Link to={Path.getExactRoutePath(RoutePaths.empty)}/>}>
                    <LayoutGridIcon/> Workspaces
                </DropdownMenuItem>
                <DropdownMenuItem render={<Link to={Path.getSettingsPath("profile")}/>}>
                    <SettingsIcon/> Settings
                </DropdownMenuItem>
                <DropdownMenuSub>
                    <DropdownMenuSubTrigger>
                        <SunIcon/> Theme
                    </DropdownMenuSubTrigger>
                    <DropdownMenuSubContent>
                        <DropdownMenuRadioGroup value={theme} onValueChange={(value) => setTheme(value as Theme)}>
                            {THEMES.map(({value, label, icon: Icon}) => (
                                <DropdownMenuRadioItem key={value} value={value}>
                                    <Icon/> {label}
                                </DropdownMenuRadioItem>
                            ))}
                        </DropdownMenuRadioGroup>
                    </DropdownMenuSubContent>
                </DropdownMenuSub>
                <DropdownMenuSeparator/>
                <DropdownMenuItem onClick={() => logout.mutate()}>
                    <LogOutIcon/> Log out
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
};

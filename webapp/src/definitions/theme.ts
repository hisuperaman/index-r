import {MonitorIcon, MoonIcon, SunIcon} from "lucide-react";

export type Theme = "dark" | "light" | "system";

export const THEMES: { value: Theme; label: string; icon: typeof SunIcon }[] = [
	{value: "light", label: "Light", icon: SunIcon},
	{value: "dark", label: "Dark", icon: MoonIcon},
	{value: "system", label: "System", icon: MonitorIcon},
];

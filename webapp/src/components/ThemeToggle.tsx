import {Monitor, Moon, Sun} from "lucide-react"

import {Button} from "@/components/ui/button"
import {useTheme} from "@/hooks";

export const ThemeToggle = () => {
	const {theme, setTheme} = useTheme();

	const nextTheme = () => {
		switch (theme) {
			case "light":
				setTheme("dark");
				break;
			case "dark":
				setTheme("system");
				break;
			default:
				setTheme("light");
		}
	};

	const Icon =
		theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;

	return (
		<Button
			variant="outline"
			size="icon"
			onClick={nextTheme}
			aria-label={`Current theme: ${theme}`}
		>
			<Icon className="h-[1.2rem] w-[1.2rem]"/>
		</Button>
	)
}
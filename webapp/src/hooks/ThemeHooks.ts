import {useContext} from "react";
import {type ThemeContextType, ThemeProviderContext} from "@/contexts";

export const useTheme = (): ThemeContextType => {
	const context = useContext(ThemeProviderContext)
	if (!context) {
		throw new Error("useTheme must be used within a ThemeProvider")
	}
	return context;
}
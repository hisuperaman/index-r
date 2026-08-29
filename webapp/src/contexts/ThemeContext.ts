import {createContext} from "react"
import type {Theme} from "@/definitions/theme.ts";

export interface ThemeContextType {
	theme: Theme
	setTheme: (theme: Theme) => void
}

export const ThemeProviderContext = createContext<ThemeContextType | undefined>(undefined);
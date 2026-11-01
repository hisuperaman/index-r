import {type ReactNode, useEffect, useState} from "react";
import {ThemeProviderContext} from "./ThemeContext.ts";
import type {Theme} from "@/definitions/theme.ts";

type ThemeProviderProps = {
	children: ReactNode
	defaultTheme?: Theme
	storageKey: string
}

export const ThemeProvider = ({
								  children,
								  defaultTheme = "system",
								  storageKey,
								  ...props
							  }: ThemeProviderProps) => {
	const [theme, setTheme] = useState<Theme>(
		() => (localStorage.getItem(storageKey) as Theme) || defaultTheme
	)

	useEffect(() => {
		const root = window.document.documentElement

		root.classList.remove("light", "dark")

		if (theme === "system") {
			const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
				.matches
				? "dark"
				: "light"

			root.classList.add(systemTheme)
			return
		}

		root.classList.add(theme)
	}, [theme])

	return (
		<ThemeProviderContext.Provider {...props} value={{
			theme,
			setTheme: (theme: Theme) => {
				localStorage.setItem(storageKey, theme)
				setTheme(theme)
			},
		}}>
			{children}
		</ThemeProviderContext.Provider>
	)
}
import tailwindcss from "@tailwindcss/vite"
import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'
import {fileURLToPath} from "node:url";

// https://vite.dev/config/
export default defineConfig({
	plugins: [react(), tailwindcss()],
	resolve: {
		alias: {
			"@": fileURLToPath(new URL("./src", import.meta.url)),
		},
	},
	server: {
		proxy: ['admin', 'iam', 'server', 'media', 'static'].reduce((acc, path) =>
			({
				...acc, [`/${path}`]: {
					target: 'http://localhost:8000',
					ws: true,
				}
			}), {})
	},
})

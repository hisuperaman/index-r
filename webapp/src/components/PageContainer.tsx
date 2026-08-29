import type {PropsWithChildren} from "react";

export const PageContainer = ({children}: PropsWithChildren) => {
	return (
		<main className="mx-auto w-full max-w-7xl px-4 py-6">
			{children}
		</main>
	);
}
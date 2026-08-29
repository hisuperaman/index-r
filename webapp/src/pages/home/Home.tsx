import {Button} from "@/components/ui/button.tsx";
import {PageContainer, ThemeToggle} from "@/components";


export const Home = () => {
	return (
		<PageContainer>
			<ThemeToggle/>
			<Button>Just a button</Button>
		</PageContainer>
	)
}
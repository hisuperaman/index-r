import {PageContainer, ThemeToggle} from "@/components";
import {Button} from "@/components/ui/button.tsx";
import {useLogout} from "@/queries";

export const Home = () => {
    const logoutMutation = useLogout();

    return (
        <PageContainer>
            <ThemeToggle/>
            <Button variant={'destructive'} onClick={() => logoutMutation.mutate()}>
                Logout
            </Button>
        </PageContainer>
    )
}
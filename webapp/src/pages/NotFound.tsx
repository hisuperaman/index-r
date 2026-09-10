import {Button} from "@/components/ui/button";
import {Link} from "react-router";
import {useLogout} from "@/queries";
import {isLoggedIn} from "@/account";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";


interface NotFoundProps {
    homeUrl?: string;
}

export const NotFound = ({homeUrl = Path.getExactRoutePath(RoutePaths.empty)}: NotFoundProps) => {
    const logoutMutation = useLogout();

    return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-6">
            <div className="text-center">
                <h1 className="text-6xl font-bold tracking-tight">404</h1>
                <p className="mt-2 text-muted-foreground">
                    The page you're looking for doesn't exist.
                </p>
            </div>

            <div className={'flex gap-2 flex-wrap justify-center'}>
                <Button render={<Link to={homeUrl}/>} nativeButton={false}>
                    Go back home
                </Button>

                {isLoggedIn() && (
                    <Button variant={'destructive'} onClick={() => logoutMutation.mutate()}>
                        Logout
                    </Button>
                )}
            </div>
        </div>
    )
}
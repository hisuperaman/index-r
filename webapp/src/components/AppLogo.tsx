import {Button} from "@/components/ui/button.tsx";
import {Link} from "react-router";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";

export const AppLogo = () => (
    <Button
        render={<Link to={Path.getExactRoutePath(RoutePaths.empty)}/>}
        nativeButton={false}
        variant="ghost"
        className="text-xl p-2"
    >
        Index<span className="text-muted-foreground">R</span>
    </Button>
)
import {Link} from "react-router";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {Logo} from "./Logo.tsx";

/** The wordmark, linking home. */
export const AppLogo = () => (
    <Link
        to={Path.getExactRoutePath(RoutePaths.empty)}
        aria-label="IndexR home"
        className="shrink-0 rounded-md px-0.5 outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
    >
        <Logo/>
    </Link>
);

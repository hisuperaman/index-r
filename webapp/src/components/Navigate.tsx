import {RoutePaths} from "@/enums";
import {Navigate as RouterNavigate} from "react-router";
import {Path} from "@/utils";


export class Navigate {

    public static toLogin() {
        return <RouterNavigate to={Path.getExactRoutePath(RoutePaths.login)}/>
    }

    public static toDashboard() {
        return <RouterNavigate to={Path.getExactRoutePath(RoutePaths.empty)}/>
    }
}
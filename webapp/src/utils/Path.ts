import SystemPath from "path-browserify";
import {type RoutePath} from "@/enums";

export class Path {

	public static join = SystemPath.join;
	public static sep = SystemPath.sep;

	public static getExactRoutePath(...path: RoutePath[]) {
		return SystemPath.join(Path.sep, ...path);
	}

	public static getRoutePath(...path: RoutePath[]) {
		return SystemPath.join(Path.sep, ...path, '*');
	}

	public static getSegments() {
		return window.location.pathname.split(Path.sep).filter(Boolean);
	}
}
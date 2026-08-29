import IndexR from "@/api/IndexR.ts";
import type {User} from "@/models";

export class IAM extends IndexR {

	private static url: string = "/iam";

	public static getUser(): Promise<User> {
		return this.get(`${IAM.url}/user/`);
	}
}

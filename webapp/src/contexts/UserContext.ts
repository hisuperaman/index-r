import type {User} from "@/models";
import {createContext} from "react";

export interface UserContextType {
	user: User | undefined;
	revalidateUser: (u?: User) => Promise<User>;
	loading: boolean;
}

export const UserContext = createContext<UserContextType | undefined>(undefined);
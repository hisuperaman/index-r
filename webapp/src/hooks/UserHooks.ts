import {useContext} from "react";
import {type UserContextType, UserContext} from "@/contexts";

export const useUser = (): UserContextType => {
	const context = useContext(UserContext);
	if (!context) {
		throw new Error("useUser must be used within a UserProvider");
	}
	return context;
};
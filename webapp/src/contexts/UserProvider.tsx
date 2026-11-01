import {type PropsWithChildren, useEffect, useState} from "react";
import type {User} from "@/models";
import {IAM} from "@/api";
import {isLoggedIn} from "@/account";
import {UserContext} from "./UserContext";

export const UserProvider = ({children}: PropsWithChildren) => {
	const [user, setUser] = useState<User>();
	const [loading, setLoading] = useState(false);

	const revalidateUser = async (u?: User): Promise<User> => {
		setLoading(true);
		try {
			if (u) {
				setUser(u);
				return u;
			}
			const fetched = await IAM.getUser();
			setUser(fetched);
			return fetched;
		} finally {
			setLoading(false);
		}
	}

	useEffect(() => {
		if (isLoggedIn()) {
			revalidateUser();
		}
	}, []);

	return (
		<UserContext.Provider value={{user, revalidateUser, loading}}>
			{children}
		</UserContext.Provider>
	);
}
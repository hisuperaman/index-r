export interface Token {
	key: string;
}

export interface RegisterUser {
	username: string;
	email: string;
	first_name: string;
	last_name: string;
}

export interface User extends RegisterUser {
	id: number;
}
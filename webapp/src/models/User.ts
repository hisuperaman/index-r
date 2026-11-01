export interface Token {
	key: string;
}

export interface AuthTokens {
	access: string;
	refresh: string;
}

export interface RegisterUser {
	email: string;
	first_name: string;
	last_name: string;
}

export interface User extends RegisterUser {
	id: number;
}

export interface LoginResponse extends AuthTokens {
	user: User;
}
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
	has_password: boolean;
}

export interface LoginResponse extends AuthTokens {
	user: User;
}

export interface SocialAccount {
	id: number;
	provider: string;
	email: string | null;
	date_joined: string;
}

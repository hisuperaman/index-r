import type {RegisterUser} from "@/models";

export interface RegisterBody extends RegisterUser {
	password1: string;
	password2: string;
}

export interface LoginBody {
	username: string;
	password: string;
}
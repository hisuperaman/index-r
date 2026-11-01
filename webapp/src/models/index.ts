export * from "./User.ts";


export interface BaseModel {
	id: number;
}

export interface PrimaryModel {
	id: string;
	created_at: string;
	updated_at: string;
}
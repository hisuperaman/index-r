export * from "./User.ts";
export * from "./Paper.ts";
export * from "./Workspace.ts";
export * from "./Message.ts";


export interface BaseModel {
	id: number;
}

export interface PrimaryModel {
	id: string;
	created_at: string;
	updated_at: string;
}

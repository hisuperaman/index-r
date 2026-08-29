export type ErrorResponse<T> = T & {
	non_field_errors: string[];
};
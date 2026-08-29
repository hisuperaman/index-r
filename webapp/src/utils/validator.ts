export const isValid = (value: string | boolean | null | undefined): boolean =>
	value !== "" && value !== null && value !== undefined;

export const isValidPassword = (password: string): boolean =>
	/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$/.test(password);

export const isValidEmail = (email: string): boolean =>
	/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

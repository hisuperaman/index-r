import {z} from "zod";

const passwordSchema = z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Za-z]/, "Password must include a letter")
    .regex(/[0-9]/, "Password must include a number");

export const userSchema = z
    .object({
        first_name: z.string().min(3, "First Name must be at least 3 characters"),
        last_name: z.string().optional().or(z.literal("")),
        email: z.email("Enter a valid email"),
        password1: passwordSchema,
        password2: z.string().min(1, "Please confirm your password."),
    })
    .refine((data) => data.password1 === data.password2, {
        message: "Passwords do not match",
        path: ["password2"],
    });

export const loginSchema = z.object({
    email: z.email("Enter a valid email"),
    password: z.string().min(1, "Password is required"),
});

export type UserFormData = z.infer<typeof userSchema>;
export type LoginFormData = z.infer<typeof loginSchema>;
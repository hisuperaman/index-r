import {z} from "zod";

export const profileSchema = z.object({
    first_name: z.string().trim().min(1, "First name is required").max(150),
    last_name: z.string().trim().max(150),
});

const newPassword = z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Za-z]/, "Password must include a letter")
    .regex(/[0-9]/, "Password must include a number");

export const passwordSetSchema = z
    .object({
        new_password1: newPassword,
        new_password2: z.string().min(1, "Confirm your new password"),
    })
    .refine((data) => data.new_password1 === data.new_password2, {
        message: "Passwords do not match",
        path: ["new_password2"],
    });

export const passwordChangeSchema = z
    .object({
        old_password: z.string().min(1, "Enter your current password"),
        new_password1: newPassword,
        new_password2: z.string().min(1, "Confirm your new password"),
    })
    .refine((data) => data.new_password1 === data.new_password2, {
        message: "Passwords do not match",
        path: ["new_password2"],
    });

export type ProfileFormData = z.infer<typeof profileSchema>;
export type PasswordChangeFormData = z.infer<typeof passwordChangeSchema>;
export type PasswordSetFormData = z.infer<typeof passwordSetSchema>;

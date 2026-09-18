import {useNavigate} from "react-router";
import {Controller, useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {Input} from "@/components/ui/input";
import {Button} from "@/components/ui/button";
import {Field, FieldError, FieldGroup, FieldLabel} from "@/components/ui/field";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {type UserFormData, userSchema} from "@/schemas";
import {Spinner} from "@/components/ui/spinner.tsx";
import {Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle} from "@/components/ui/card.tsx";
import {toast} from "@/components/ui/toast.tsx";
import type {AxiosError} from "axios";
import {handleApiError} from "@/utils/errors.ts";
import {useRegisterUser} from "@/queries";


export const Signup = () => {
    const navigate = useNavigate();
    const registerUser = useRegisterUser();

    const form = useForm<UserFormData>({
        resolver: zodResolver(userSchema),
        defaultValues: {
            first_name: "",
            last_name: "",
            email: "",
            password1: "",
            password2: "",
        },
    });

    const handleSubmit = (formData: UserFormData) => {
        registerUser.mutate(formData, {
            onSuccess: () => {
                toast.add({
                    title: "Account created",
                    description: "You have successfully signed up.",
                    type: "success"
                });
                navigate(Path.getExactRoutePath(RoutePaths.empty));
            },
            onError: (error: AxiosError) => {
                handleApiError<UserFormData>(
                    error,
                    (field, message) => form.setError(field, {type: "server", message}),
                    "Unable to create an account"
                );
            }
        });
    };

    const isBusy = registerUser.isPending;

    return (
        <Card className="bg-transparent border-0 shadow-none ring-0">
            <CardHeader>
                <CardTitle>Create your account</CardTitle>
                <CardDescription>
                    Start tracking your research in under two minutes.
                </CardDescription>
            </CardHeader>

            <form onSubmit={form.handleSubmit(handleSubmit)} className="mt-6 space-y-6">
                <CardContent>
                    <FieldGroup>
                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                            <Controller
                                name="first_name"
                                control={form.control}
                                render={({field, fieldState}) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor={field.name}>
                                            First Name
                                        </FieldLabel>
                                        <Input
                                            {...field}
                                            id={field.name}
                                            type="text"
                                            aria-invalid={fieldState.invalid}
                                            disabled={isBusy}
                                            placeholder="Your first name"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]}/>
                                        )}
                                    </Field>
                                )}
                            />

                            <Controller
                                name="last_name"
                                control={form.control}
                                render={({field, fieldState}) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor={field.name}>
                                            Last Name
                                        </FieldLabel>
                                        <Input
                                            {...field}
                                            id={field.name}
                                            type="text"
                                            aria-invalid={fieldState.invalid}
                                            disabled={isBusy}
                                            placeholder="Your last name"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]}/>
                                        )}
                                    </Field>
                                )}
                            />

                            <div className="col-span-1 sm:col-span-2">
                                <Controller
                                    name="email"
                                    control={form.control}
                                    render={({field, fieldState}) => (
                                        <Field data-invalid={fieldState.invalid}>
                                            <FieldLabel htmlFor={field.name}>
                                                Email
                                            </FieldLabel>
                                            <Input
                                                {...field}
                                                id={field.name}
                                                type="email"
                                                aria-invalid={fieldState.invalid}
                                                disabled={isBusy}
                                                placeholder="Your email here"
                                            />
                                            {fieldState.invalid && (
                                                <FieldError errors={[fieldState.error]}/>
                                            )}
                                        </Field>
                                    )}
                                />
                            </div>

                            <div className="col-span-1 sm:col-span-2">
                                <Controller
                                    name="password1"
                                    control={form.control}
                                    render={({field, fieldState}) => (
                                        <Field data-invalid={fieldState.invalid}>
                                            <FieldLabel htmlFor={field.name}>
                                                Password
                                            </FieldLabel>
                                            <Input
                                                {...field}
                                                id={field.name}
                                                type="password"
                                                aria-invalid={fieldState.invalid}
                                                disabled={isBusy}
                                                placeholder="Enter your password"
                                            />
                                            {fieldState.invalid && (
                                                <FieldError errors={[fieldState.error]}/>
                                            )}
                                        </Field>
                                    )}
                                />
                            </div>

                            <div className="col-span-1 sm:col-span-2">
                                <Controller
                                    name="password2"
                                    control={form.control}
                                    render={({field, fieldState}) => (
                                        <Field data-invalid={fieldState.invalid}>
                                            <FieldLabel htmlFor={field.name}>
                                                Confirm Password
                                            </FieldLabel>
                                            <Input
                                                {...field}
                                                id={field.name}
                                                type="password"
                                                aria-invalid={fieldState.invalid}
                                                disabled={isBusy}
                                                placeholder="Confirm your password"
                                            />
                                            {fieldState.invalid && (
                                                <FieldError errors={[fieldState.error]}/>
                                            )}
                                        </Field>
                                    )}
                                />
                            </div>
                        </div>
                    </FieldGroup>
                </CardContent>

                <CardFooter className="justify-end p-6">
                    <Button
                        type="submit"
                        disabled={isBusy}
                        className="w-full"
                    >
                        {isBusy && <Spinner/>}
                        Create account
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
}
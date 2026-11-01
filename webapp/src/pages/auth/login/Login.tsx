import {useNavigate, Link} from "react-router";
import {Controller, useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {Input} from "@/components/ui/input";
import {Button} from "@/components/ui/button";
import {Field, FieldError, FieldGroup, FieldLabel} from "@/components/ui/field";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {type LoginFormData, loginSchema} from "@/schemas";
import {Spinner} from "@/components/ui/spinner";
import {Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle} from "@/components/ui/card";
import {toast} from "@/components/ui/toast";
import type {AxiosError} from "axios";
import {handleApiError} from "@/utils/errors";
import {useLogin} from "@/queries";
import {onLoginSuccess} from "@/account";
import {SocialAuth} from "@/pages/auth/components";

export const Login = () => {
    const navigate = useNavigate();
    const loginUser = useLogin();

    const form = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            email: "",
            password: "",
        },
    });

    const handleSubmit = (formData: LoginFormData) => {
        loginUser.mutate(formData, {
            onSuccess: (token) => {
                onLoginSuccess(token);
                toast.add({
                    title: "Welcome back!",
                    description: "You have successfully signed in.",
                    type: "success"
                });
                navigate(Path.getExactRoutePath(RoutePaths.empty));
            },
            onError: (error: AxiosError) => {
                form.setValue("password", "");
                handleApiError<LoginFormData>(
                    error,
                    (field, message) => form.setError(field, {type: "server", message}),
                    "Unable to sign in"
                );
            }
        });
    };

    const isBusy = loginUser.isPending;

    return (
        <Card className="mx-auto w-full max-w-md bg-background">
            <CardHeader className="text-center">
                <CardTitle className="text-2xl">Welcome back</CardTitle>
                <CardDescription>Sign in to continue to your account.</CardDescription>
            </CardHeader>

            <CardContent>
                <SocialAuth/>
            </CardContent>

            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
                <CardContent className="pt-0">
                    <FieldGroup>
                        <div className="grid grid-cols-1 gap-4">
                            <Controller
                                name="email"
                                control={form.control}
                                render={({field, fieldState}) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor={field.name}>Email address</FieldLabel>
                                        <Input
                                            {...field}
                                            id={field.name}
                                            type="email"
                                            aria-invalid={fieldState.invalid}
                                            disabled={isBusy}
                                            placeholder="Enter your email address"
                                        />
                                        {fieldState.invalid && <FieldError errors={[fieldState.error]}/>}
                                    </Field>
                                )}
                            />

                            <Controller
                                name="password"
                                control={form.control}
                                render={({field, fieldState}) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor={field.name}>Password</FieldLabel>
                                        <Input
                                            {...field}
                                            id={field.name}
                                            type="password"
                                            aria-invalid={fieldState.invalid}
                                            disabled={isBusy}
                                            placeholder="Enter your password"
                                        />
                                        {fieldState.invalid && <FieldError errors={[fieldState.error]}/>}
                                    </Field>
                                )}
                            />
                        </div>
                    </FieldGroup>
                </CardContent>

                <CardFooter className="flex flex-col gap-4 p-6 pt-0">
                    <Button type="submit" disabled={isBusy} className="w-full">
                        {isBusy && <Spinner/>}
                        Continue
                    </Button>

                    <div className="text-center text-sm text-muted-foreground">
                        Don't have an account?{" "}
                        <Link
                            to={Path.getExactRoutePath(RoutePaths.signup)}
                            className="underline underline-offset-4 hover:text-primary"
                        >
                            Sign up
                        </Link>
                    </div>
                </CardFooter>
            </form>
        </Card>
    );
}
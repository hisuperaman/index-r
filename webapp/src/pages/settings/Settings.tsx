import {useEffect, useState} from "react";
import {Controller, type FieldPath, useForm, type UseFormReturn} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import type {AxiosError} from "axios";
import {Link, Navigate, useParams} from "react-router";
import {CheckIcon, KeyRoundIcon, LogOutIcon, PaletteIcon, PlugIcon, ShieldCheckIcon, UserRoundIcon} from "lucide-react";
import {FcGoogle} from "react-icons/fc";
import {AppHeader, ConfirmDialog} from "@/components";
import {Avatar, AvatarFallback} from "@/components/ui/avatar";
import {Button} from "@/components/ui/button";
import {Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle} from "@/components/ui/card";
import {Field, FieldDescription, FieldError, FieldGroup, FieldLabel} from "@/components/ui/field";
import {Input} from "@/components/ui/input";
import {Skeleton} from "@/components/ui/skeleton";
import {Spinner} from "@/components/ui/spinner";
import {toast} from "@/components/ui/toast";
import {THEMES, type Theme} from "@/definitions/theme.ts";
import {useTheme, useUser} from "@/hooks";
import type {User} from "@/models";
import {
    useChangePassword,
    useConnectGoogle,
    useDisconnectSocialAccount,
    useLogout,
    useSocialAccounts,
    useUpdateProfile,
} from "@/queries";
import {
    type PasswordChangeFormData,
    passwordChangeSchema,
    type PasswordSetFormData,
    passwordSetSchema,
    type ProfileFormData,
    profileSchema,
} from "@/schemas";
import {Path, getInitials} from "@/utils";
import {handleApiError} from "@/utils/errors";
import {IntegrationsSection} from "./Integrations.tsx";
import {cn} from "@/lib/utils.ts";

interface TextFieldProps<T extends Record<string, string>> {
    form: UseFormReturn<T>;
    name: FieldPath<T>;
    label: string;
    type?: string;
    autoComplete?: string;
    placeholder?: string;
    disabled: boolean;
}

const TextField = <T extends Record<string, string>, >({form, name, label, type = "text", autoComplete, placeholder, disabled}: TextFieldProps<T>) => (
    <Controller
        name={name}
        control={form.control}
        render={({field, fieldState}) => (
            <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor={name}>{label}</FieldLabel>
                <Input
                    {...field}
                    id={name}
                    type={type}
                    autoComplete={autoComplete}
                    placeholder={placeholder}
                    aria-invalid={fieldState.invalid}
                    disabled={disabled}
                />
                {fieldState.invalid && <FieldError errors={[fieldState.error]}/>}
            </Field>
        )}
    />
);

const showFieldErrors = <T extends Record<string, string>, >(form: UseFormReturn<T>, title: string) =>
    (error: AxiosError) => handleApiError<T>(
        error,
        (field, message) => form.setError(field as FieldPath<T>, {type: "server", message}),
        title,
    );

const ProfileCard = ({user}: { user: User }) => {
    const {revalidateUser} = useUser();
    const updateProfile = useUpdateProfile();
    const form = useForm<ProfileFormData>({
        resolver: zodResolver(profileSchema),
        defaultValues: {first_name: user.first_name, last_name: user.last_name},
    });

    useEffect(() => {
        form.reset({first_name: user.first_name, last_name: user.last_name});
    }, [user.first_name, user.last_name, form]);

    const submit = (data: ProfileFormData) => updateProfile.mutate(data, {
        onSuccess: (updated) => {
            revalidateUser(updated);
            toast.add({title: "Profile updated", type: "success"});
        },
        onError: showFieldErrors(form, "Couldn't update your profile"),
    });

    const pending = updateProfile.isPending;
    const name = `${user.first_name} ${user.last_name}`.trim();

    return (
        <Card>
            <form onSubmit={form.handleSubmit(submit)} className="contents">
                <CardContent>
                    <FieldGroup>
                        <div className="flex items-center gap-3">
                            <Avatar className="size-12">
                                <AvatarFallback>{getInitials(name, user.email)}</AvatarFallback>
                            </Avatar>
                            <div className="min-w-0">
                                <p className="truncate font-medium">{name || "No name yet"}</p>
                                <p className="truncate text-sm text-muted-foreground">{user.email}</p>
                            </div>
                        </div>
                        <div className="grid gap-4 sm:grid-cols-2">
                            <TextField form={form} name="first_name" label="First name" autoComplete="given-name" placeholder="Enter your first name" disabled={pending}/>
                            <TextField form={form} name="last_name" label="Last name" autoComplete="family-name" placeholder="Enter your last name" disabled={pending}/>
                        </div>
                        <Field>
                            <FieldLabel htmlFor="email">Email address</FieldLabel>
                            <Input id="email" value={user.email} disabled readOnly/>
                            <FieldDescription>Your email is your sign-in and can't be changed.</FieldDescription>
                        </Field>
                    </FieldGroup>
                </CardContent>
                <CardFooter className="justify-end gap-2 border-t">
                    <Button type="button" variant="ghost" disabled={pending || !form.formState.isDirty}
                            onClick={() => form.reset()}>
                        Cancel
                    </Button>
                    <Button type="submit" disabled={pending || !form.formState.isDirty}>
                        {pending && <Spinner/>}
                        Save changes
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
};

const ChangePasswordForm = () => {
    const changePassword = useChangePassword();
    const form = useForm<PasswordChangeFormData>({
        resolver: zodResolver(passwordChangeSchema),
        defaultValues: {old_password: "", new_password1: "", new_password2: ""},
    });

    const submit = (data: PasswordChangeFormData) => changePassword.mutate(data, {
        onSuccess: () => {
            form.reset();
            toast.add({title: "Password changed", description: "Use your new password next time you sign in.", type: "success"});
        },
        onError: showFieldErrors(form, "Couldn't change your password"),
    });

    const pending = changePassword.isPending;

    return (
        <Card>
            <form onSubmit={form.handleSubmit(submit)} className="contents">
                <CardHeader>
                    <CardTitle>Change password</CardTitle>
                    <CardDescription>Use at least 8 characters, with a letter and a number.</CardDescription>
                </CardHeader>
                <CardContent>
                    <FieldGroup>
                        <TextField form={form} name="old_password" label="Current password" type="password"
                                   autoComplete="current-password" placeholder="Enter your current password" disabled={pending}/>
                        <div className="grid gap-4 sm:grid-cols-2">
                            <TextField form={form} name="new_password1" label="New password" type="password"
                                       autoComplete="new-password" placeholder="At least 8 characters" disabled={pending}/>
                            <TextField form={form} name="new_password2" label="Confirm new password" type="password"
                                       autoComplete="new-password" placeholder="Re-enter your new password" disabled={pending}/>
                        </div>
                    </FieldGroup>
                </CardContent>
                <CardFooter className="justify-end border-t">
                    <Button type="submit" disabled={pending || !form.formState.isDirty}>
                        {pending && <Spinner/>}
                        Update password
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
};

const SetPasswordForm = () => {
    const {revalidateUser} = useUser();
    const setPassword = useChangePassword();
    const form = useForm<PasswordSetFormData>({
        resolver: zodResolver(passwordSetSchema),
        defaultValues: {new_password1: "", new_password2: ""},
    });

    const submit = (data: PasswordSetFormData) => setPassword.mutate(data, {
        onSuccess: async () => {
            form.reset();
            await revalidateUser();
            toast.add({title: "Password set", description: "You can now also sign in with your email.", type: "success"});
        },
        onError: showFieldErrors(form, "Couldn't set your password"),
    });

    const pending = setPassword.isPending;

    return (
        <Card>
            <form onSubmit={form.handleSubmit(submit)} className="contents">
                <CardHeader>
                    <CardTitle>Set a password</CardTitle>
                    <CardDescription>
                        You sign in with Google. Add a password so you can also sign in with your email.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 sm:grid-cols-2">
                        <TextField form={form} name="new_password1" label="Password" type="password"
                                   autoComplete="new-password" placeholder="At least 8 characters" disabled={pending}/>
                        <TextField form={form} name="new_password2" label="Confirm password" type="password"
                                   autoComplete="new-password" placeholder="Re-enter your password" disabled={pending}/>
                    </div>
                </CardContent>
                <CardFooter className="justify-end border-t">
                    <Button type="submit" disabled={pending || !form.formState.isDirty}>
                        {pending && <Spinner/>}
                        Set password
                    </Button>
                </CardFooter>
            </form>
        </Card>
    );
};

const errorMessage = (error: unknown, fallback: string): string => {
    const data = (error as AxiosError)?.response?.data as { non_field_errors?: string[] } | undefined;
    return data?.non_field_errors?.[0] ?? (error instanceof Error && !(error as AxiosError).isAxiosError ? error.message : fallback);
};

const ConnectedAccountsCard = ({user}: { user: User }) => {
    const accounts = useSocialAccounts();
    const connect = useConnectGoogle();
    const disconnect = useDisconnectSocialAccount();
    const [confirming, setConfirming] = useState(false);

    const google = accounts.data?.find(({provider}) => provider === "google");
    const onlyWayToSignIn = !!google && !user.has_password && accounts.data?.length === 1;

    const connectGoogle = () => connect.mutate(undefined, {
        onSuccess: () => toast.add({title: "Google connected", description: "You can now sign in with Google.", type: "success"}),
        onError: (error) => toast.add({
            title: "Couldn't connect Google",
            description: errorMessage(error, "Please try again."),
            type: "error",
        }),
    });

    const confirmDisconnect = () => google && disconnect.mutate(google.id, {
        onSuccess: () => {
            setConfirming(false);
            toast.add({title: "Google disconnected", type: "success"});
        },
        onError: (error) => {
            setConfirming(false);
            toast.add({title: "Couldn't disconnect Google", description: errorMessage(error, "Please try again."), type: "error"});
        },
    });

    return (
        <Card>
            <CardHeader>
                <CardTitle>Connected accounts</CardTitle>
                <CardDescription>Accounts you can use to sign in to IndexR.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
                {accounts.isPending ? <Skeleton className="h-16 rounded-2xl"/> : accounts.isError ? (
                    <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
                        Couldn't load your connected accounts.
                        <Button size="sm" variant="outline" onClick={() => accounts.refetch()}>Retry</Button>
                    </div>
                ) : (
                    <div className="flex items-center gap-3 rounded-2xl border p-3">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl border bg-background">
                            <FcGoogle className="size-5"/>
                        </div>
                        <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium">Google</p>
                            <p className="truncate text-xs text-muted-foreground">
                                {google ? `Connected${google.email ? ` as ${google.email}` : ""}` : "Not connected"}
                            </p>
                        </div>
                        {google ? (
                            <Button size="sm" variant="outline" disabled={onlyWayToSignIn || disconnect.isPending}
                                    onClick={() => setConfirming(true)}>
                                Disconnect
                            </Button>
                        ) : (
                            <Button size="sm" disabled={connect.isPending} onClick={connectGoogle}>
                                {connect.isPending && <Spinner/>}
                                Connect
                            </Button>
                        )}
                    </div>
                )}
                {onlyWayToSignIn && (
                    <p className="flex items-start gap-2 text-xs text-muted-foreground">
                        <KeyRoundIcon className="mt-0.5 size-3.5 shrink-0"/>
                        Google is the only way you sign in. Set a password above before disconnecting it.
                    </p>
                )}
            </CardContent>

            <ConfirmDialog
                open={confirming}
                onOpenChange={setConfirming}
                title="Disconnect Google?"
                description="You won't be able to sign in with Google any more. You'll sign in with your email and password."
                confirmLabel="Disconnect"
                destructive
                pending={disconnect.isPending}
                onConfirm={confirmDisconnect}
            />
        </Card>
    );
};

const SecuritySection = ({user}: { user: User }) => (
    <div className="space-y-6">
        {user.has_password ? <ChangePasswordForm/> : <SetPasswordForm/>}
        <ConnectedAccountsCard user={user}/>
    </div>
);

const ThemePreview = ({theme}: { theme: Theme }) => {
    const pane = (dark: boolean) => (
        <div className={cn("flex h-full flex-1 flex-col gap-1.5 p-2.5", dark ? "bg-zinc-900" : "bg-white")}>
            <div className={cn("h-1.5 w-2/3 rounded-full", dark ? "bg-zinc-600" : "bg-zinc-300")}/>
            <div className={cn("h-1.5 w-full rounded-full", dark ? "bg-zinc-700" : "bg-zinc-200")}/>
            <div className={cn("h-1.5 w-4/5 rounded-full", dark ? "bg-zinc-700" : "bg-zinc-200")}/>
            <div className={cn("mt-auto h-3 w-1/2 self-end rounded", dark ? "bg-zinc-200" : "bg-zinc-800")}/>
        </div>
    );
    return (
        <div className="flex h-20 overflow-hidden rounded-md border">
            {theme === "system" ? <>{pane(false)}{pane(true)}</> : pane(theme === "dark")}
        </div>
    );
};

const AppearanceCard = () => {
    const {theme, setTheme} = useTheme();

    return (
        <Card>
            <CardContent>
                <div role="radiogroup" aria-label="Theme" className="grid gap-3 sm:grid-cols-3">
                    {THEMES.map(({value, label, icon: Icon}) => {
                        const selected = theme === value;
                        return (
                            <button
                                key={value}
                                type="button"
                                role="radio"
                                aria-checked={selected}
                                onClick={() => setTheme(value)}
                                className={cn(
                                    "rounded-lg border p-2 text-left transition-colors outline-none hover:bg-muted/50 focus-visible:ring-3 focus-visible:ring-ring/50",
                                    selected && "border-primary ring-1 ring-primary",
                                )}
                            >
                                <ThemePreview theme={value}/>
                                <span className="mt-2 flex items-center gap-1.5 px-1 text-sm font-medium">
                                    <Icon className="size-3.5 text-muted-foreground"/> {label}
                                    {selected && <CheckIcon className="ml-auto size-3.5"/>}
                                </span>
                            </button>
                        );
                    })}
                </div>
            </CardContent>
        </Card>
    );
};

const SECTIONS = [
    {
        id: "profile",
        label: "Profile",
        icon: UserRoundIcon,
        description: "Your name as it appears in IndexR.",
        render: (user: User) => <ProfileCard user={user}/>,
    },
    {
        id: "security",
        label: "Security",
        icon: ShieldCheckIcon,
        description: "Your password and the accounts you sign in with.",
        render: (user: User) => <SecuritySection user={user}/>,
    },
    {
        id: "integrations",
        label: "Integrations",
        icon: PlugIcon,
        description: "Connect AI assistants to your research.",
        render: () => <IntegrationsSection/>,
    },
    {
        id: "appearance",
        label: "Appearance",
        icon: PaletteIcon,
        description: "Choose a theme, or follow your system's light or dark setting.",
        render: () => <AppearanceCard/>,
    },
];

const navItemClass =
    "flex shrink-0 items-center gap-2.5 whitespace-nowrap px-3 text-sm font-medium transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50 " +
    "h-11 border-b-2 border-transparent text-muted-foreground hover:text-foreground " +
    "md:h-10 md:rounded-lg md:border-b-0 md:hover:bg-muted";

const SettingsNav = ({active}: { active: string }) => {
    const logout = useLogout();

    return (
        <nav aria-label="Settings"
             className="scrollbar-none -mx-4 flex overflow-x-auto border-b px-4 md:mx-0 md:w-56 md:shrink-0 md:flex-col md:gap-1 md:overflow-visible md:border-b-0 md:px-0">
            {SECTIONS.map(({id, label, icon: Icon}) => (
                <Link
                    key={id}
                    to={Path.getSettingsPath(id)}
                    aria-current={id === active ? "page" : undefined}
                    className={cn(
                        navItemClass,
                        id === active && "border-primary text-foreground md:bg-secondary md:text-secondary-foreground md:hover:bg-secondary",
                    )}
                >
                    <Icon className="hidden size-4 md:block"/> {label}
                </Link>
            ))}
            <div className="hidden md:my-2 md:block md:border-t"/>
            <button
                type="button"
                onClick={() => logout.mutate()}
                disabled={logout.isPending}
                className={cn(navItemClass, "text-destructive hover:text-destructive md:hover:bg-destructive/10")}
            >
                {logout.isPending ? <Spinner className="size-4"/> : <LogOutIcon className="hidden size-4 md:block"/>} Log out
            </button>
        </nav>
    );
};

export const Settings = () => {
    const {user} = useUser();
    const {section = SECTIONS[0].id} = useParams();
    const current = SECTIONS.find(({id}) => id === section);

    if (!current) return <Navigate to={Path.getSettingsPath(SECTIONS[0].id)} replace/>;

    return (
        <>
            <AppHeader breadcrumb={<span className="truncate text-sm font-medium">Settings</span>}/>
            <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 md:px-8 md:py-10">
                <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
                <p className="mt-1 text-sm text-muted-foreground">Manage your account and how IndexR looks.</p>

                <div className="mt-6 flex flex-col gap-8 md:mt-10 md:flex-row md:gap-12">
                    <SettingsNav active={current.id}/>
                    <section className="min-w-0 flex-1" aria-labelledby="settings-section-title">
                        <div className="mb-5 space-y-1">
                            <h2 id="settings-section-title" className="text-lg font-semibold">{current.label}</h2>
                            <p className="text-sm text-muted-foreground">{current.description}</p>
                        </div>
                        <div className="max-w-3xl">
                            {user ? current.render(user) : <Skeleton className="h-72 rounded-2xl"/>}
                        </div>
                    </section>
                </div>
            </main>
        </>
    );
};

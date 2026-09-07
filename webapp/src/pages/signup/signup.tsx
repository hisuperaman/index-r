import {useEffect, useState} from "react";
import {useNavigate} from "react-router";
import {useForm} from "react-hook-form";
import {z} from "zod";
import {zodResolver} from "@hookform/resolvers/zod";

import type {RegisterBody} from "@/definitions/RequestBody";
import {useRegister} from "@/queries/user";
import {Input} from "@/components/ui/input";
import {Button} from "@/components/ui/button";
import {AuthLayout} from "@/layouts/AuthLayout";
import {Path} from "@/utils";
import {RoutePaths} from "@/enums";

const signupSchema = z
    .object({
        name: z
            .string()
            .trim()
            .min(1, "Please enter your full name."),

        email: z
            .string()
            .trim()
            .min(1, "Please enter your email.")
            .email("Please enter a valid email address."),

        pass: z
            .string()
            .min(1, "Please enter a password."),

        pass2: z
            .string()
            .min(1, "Please confirm your password."),
    })
    .refine(
        (values) => values.pass === values.pass2,
        {
            message: "Passwords do not match.",
            path: ["pass2"],
        }
    );

type SignupFormValues = z.infer<typeof signupSchema>;

export function Signup() {
    const navigate = useNavigate();
    const register = useRegister();

    const [filesCount, setFilesCount] =
        useState(1042817);

    const form = useForm<SignupFormValues>({
        resolver: zodResolver(signupSchema),

        defaultValues: {
            name: "",
            email: "",
            pass: "",
            pass2: "",
        },
    });

    const {
        register: registerField,
        handleSubmit,
        formState: {errors},
    } = form;

    // Live sources counter
    useEffect(() => {
        const id = setInterval(() => {
            setFilesCount(
                (count) =>
                    count +
                    Math.floor(Math.random() * 9) +
                    1
            );
        }, 850);

        return () => clearInterval(id);
    }, []);

    const onSubmit = (values: SignupFormValues) => {
        const nameParts =
            values.name.trim().split(/\s+/);

        const data: RegisterBody = {
            email: values.email.trim(),

            first_name:
                nameParts[0] || "",

            last_name:
                nameParts.slice(1).join(" "),

            password1: values.pass,

            password2: values.pass2,
        };

        register.mutate(data, {
          onSuccess: () => {
            navigate(
              Path.getExactRoutePath(RoutePaths.empty)
            );
          },
        });
    };

    const goToLogin = () => {
        navigate(
            Path.getExactRoutePath(RoutePaths.login)
        );
    };

    return (
        <AuthLayout>
            <div
                className="
                    mx-auto grid w-full max-w-[1280px]
                    grid-cols-1 items-center gap-16
                    px-7 pb-12 pt-4
                    sm:px-12
                    lg:grid-cols-[1.15fr_0.85fr]
                    lg:gap-10
                    xl:px-16
                "
            >
                {/* LEFT SIDE */}
                <section
                    className="
                        max-w-[680px]
                        lg:pb-4
                    "
                >
                    {/* Eyebrow */}
                    <div
                        className="
                            mb-6 flex items-center gap-2
                            font-[JetBrains_Mono,monospace]
                            text-[10px]
                            uppercase
                            tracking-[0.14em]
                            text-[#9a9b98]
                        "
                    >
                        <span className="relative flex h-[6px] w-[6px]">
                            <span
                                className="
                                    absolute inline-flex
                                    h-full w-full rounded-full
                                    bg-[#f4f4f2]
                                    opacity-60
                                    motion-safe:animate-ping
                                    motion-reduce:hidden
                                "
                            />

                            <span
                                className="
                                    relative inline-flex
                                    h-[6px] w-[6px]
                                    rounded-full
                                    bg-[#f4f4f2]
                                "
                            />
                        </span>

                        watching your research topics — live
                    </div>

                    {/* Heading */}
                    <h1
                        className="
                            max-w-[700px]
                            font-[Space_Grotesk,sans-serif]
                            text-[clamp(44px,5.4vw,78px)]
                            font-medium
                            leading-[0.97]
                            tracking-[-0.055em]
                            text-[#f4f4f2]
                        "
                    >
                        Find the right paper.
                        <br />
                        Never miss the{" "}
                        <em
                            className="
                                font-normal
                                text-[#9a9b98]
                            "
                        >
                            next
                        </em>{" "}
                        one.
                    </h1>

                    {/* Description */}
                    <p
                        className="
                            mt-7 max-w-[590px]
                            font-[Inter,sans-serif]
                            text-[14px]
                            leading-[1.75]
                            text-[#9a9b98]
                        "
                    >
                        IndexR searches only confirmed sources —
                        published papers, verified datasets,
                        peer-reviewed work — and surfaces what's
                        actually relevant to your research. When
                        something new lands on a topic you're tracking,
                        it tells you first.
                    </p>

                    {/* Stats */}
                    <div
                        className="
                            mt-9 flex flex-wrap
                            items-center gap-x-8 gap-y-4
                            border-t border-[#2a2b2c]
                            pt-5
                        "
                    >
                        <div>
                            <div
                                className="
                                    font-[JetBrains_Mono,monospace]
                                    text-[18px]
                                    font-medium
                                    tracking-[-0.03em]
                                    text-[#f4f4f2]
                                "
                            >
                                {filesCount.toLocaleString()}
                            </div>

                            <div
                                className="
                                    mt-1
                                    font-[JetBrains_Mono,monospace]
                                    text-[9px]
                                    uppercase
                                    tracking-[0.12em]
                                    text-[#606160]
                                "
                            >
                                sources indexed
                            </div>
                        </div>

                        <div
                            className="
                                h-8 w-px
                                bg-[#2a2b2c]
                            "
                        />

                        <div>
                            <div
                                className="
                                    font-[JetBrains_Mono,monospace]
                                    text-[18px]
                                    font-medium
                                    tracking-[-0.03em]
                                    text-[#f4f4f2]
                                "
                            >
                                2.4M+
                            </div>

                            <div
                                className="
                                    mt-1
                                    font-[JetBrains_Mono,monospace]
                                    text-[9px]
                                    uppercase
                                    tracking-[0.12em]
                                    text-[#606160]
                                "
                            >
                                papers tracked
                            </div>
                        </div>

                        <div
                            className="
                                h-8 w-px
                                bg-[#2a2b2c]
                            "
                        />

                        <div>
                            <div
                                className="
                                    font-[JetBrains_Mono,monospace]
                                    text-[18px]
                                    font-medium
                                    tracking-[-0.03em]
                                    text-[#f4f4f2]
                                "
                            >
                                12k+
                            </div>

                            <div
                                className="
                                    mt-1
                                    font-[JetBrains_Mono,monospace]
                                    text-[9px]
                                    uppercase
                                    tracking-[0.12em]
                                    text-[#606160]
                                "
                            >
                                researchers
                            </div>
                        </div>
                    </div>
                </section>

                {/* SIGNUP CARD */}
                <section
                    className="
                        relative w-full max-w-[392px]
                        justify-self-center
                        lg:justify-self-end
                    "
                >
                    <div
                        className="
                            relative
                            border border-[#2a2b2c]
                            bg-[#111213]/95
                            px-7 py-8
                            shadow-[0_25px_80px_rgba(0,0,0,0.3)]
                            before:absolute before:left-[-1px]
                            before:top-[-1px]
                            before:h-4 before:w-4
                            before:border-l before:border-t
                            before:border-[#f4f4f2]/60
                            after:absolute after:bottom-[-1px]
                            after:right-[-1px]
                            after:h-4 after:w-4
                            after:border-b after:border-r
                            after:border-[#f4f4f2]/60
                            sm:px-8
                        "
                    >
                        {/* Card heading */}
                        <h2
                            className="
                                font-[Space_Grotesk,sans-serif]
                                text-[25px]
                                font-medium
                                tracking-[-0.04em]
                                text-[#f4f4f2]
                            "
                        >
                            Create your account
                        </h2>

                        <div
                            className="
                                mt-2
                                font-[Inter,sans-serif]
                                text-[12px]
                                leading-5
                                text-[#606160]
                            "
                        >
                            Start tracking your research
                            in under two minutes.
                        </div>

                        <form
                            onSubmit={handleSubmit(onSubmit)}
                            className="mt-7"
                        >
                            {/* Full name */}
                            <div className="mb-5">
                                <label
                                    htmlFor="name"
                                    className="
                                        mb-2 block
                                        font-[JetBrains_Mono,monospace]
                                        text-[9px]
                                        uppercase
                                        tracking-[0.12em]
                                        text-[#9a9b98]
                                    "
                                >
                                    Full name
                                </label>

                                <Input
                                    id="name"
                                    type="text"
                                    autoComplete="name"
                                    placeholder="Jane Smith"
                                    {...registerField("name")}
                                    className="
                                        h-11 rounded-none
                                        border-[#2a2b2c]
                                        bg-[#0d0e0f]
                                        px-3
                                        font-[Inter,sans-serif]
                                        text-[13px]
                                        text-[#f4f4f2]
                                        placeholder:text-[#606160]
                                        focus-visible:border-[#9a9b98]
                                        focus-visible:ring-0
                                    "
                                />

                                {errors.name && (
                                    <p
                                        className="
                                            mt-1.5
                                            font-[Inter,sans-serif]
                                            text-[10px]
                                            text-[#9a9b98]
                                        "
                                    >
                                        {errors.name.message}
                                    </p>
                                )}
                            </div>

                            {/* Email */}
                            <div className="mb-5">
                                <label
                                    htmlFor="email"
                                    className="
                                        mb-2 block
                                        font-[JetBrains_Mono,monospace]
                                        text-[9px]
                                        uppercase
                                        tracking-[0.12em]
                                        text-[#9a9b98]
                                    "
                                >
                                    Email
                                </label>

                                <Input
                                    id="email"
                                    type="email"
                                    autoComplete="email"
                                    placeholder="jane@example.com"
                                    {...registerField("email")}
                                    className="
                                        h-11 rounded-none
                                        border-[#2a2b2c]
                                        bg-[#0d0e0f]
                                        px-3
                                        font-[Inter,sans-serif]
                                        text-[13px]
                                        text-[#f4f4f2]
                                        placeholder:text-[#606160]
                                        focus-visible:border-[#9a9b98]
                                        focus-visible:ring-0
                                    "
                                />

                                {errors.email && (
                                    <p
                                        className="
                                            mt-1.5
                                            font-[Inter,sans-serif]
                                            text-[10px]
                                            text-[#9a9b98]
                                        "
                                    >
                                        {errors.email.message}
                                    </p>
                                )}
                            </div>

                            {/* Password */}
                            <div className="mb-5">
                                <label
                                    htmlFor="password"
                                    className="
                                        mb-2 block
                                        font-[JetBrains_Mono,monospace]
                                        text-[9px]
                                        uppercase
                                        tracking-[0.12em]
                                        text-[#9a9b98]
                                    "
                                >
                                    Password
                                </label>

                                <Input
                                    id="password"
                                    type="password"
                                    autoComplete="new-password"
                                    placeholder="••••••••"
                                    {...registerField("pass")}
                                    className="
                                        h-11 rounded-none
                                        border-[#2a2b2c]
                                        bg-[#0d0e0f]
                                        px-3
                                        font-[Inter,sans-serif]
                                        text-[13px]
                                        text-[#f4f4f2]
                                        placeholder:text-[#606160]
                                        focus-visible:border-[#9a9b98]
                                        focus-visible:ring-0
                                    "
                                />

                                {errors.pass && (
                                    <p
                                        className="
                                            mt-1.5
                                            font-[Inter,sans-serif]
                                            text-[10px]
                                            text-[#9a9b98]
                                        "
                                    >
                                        {errors.pass.message}
                                    </p>
                                )}
                            </div>

                            {/* Confirm password */}
                            <div className="mb-6">
                                <label
                                    htmlFor="password-confirm"
                                    className="
                                        mb-2 block
                                        font-[JetBrains_Mono,monospace]
                                        text-[9px]
                                        uppercase
                                        tracking-[0.12em]
                                        text-[#9a9b98]
                                    "
                                >
                                    Confirm password
                                </label>

                                <Input
                                    id="password-confirm"
                                    type="password"
                                    autoComplete="new-password"
                                    placeholder="••••••••"
                                    {...registerField("pass2")}
                                    className="
                                        h-11 rounded-none
                                        border-[#2a2b2c]
                                        bg-[#0d0e0f]
                                        px-3
                                        font-[Inter,sans-serif]
                                        text-[13px]
                                        text-[#f4f4f2]
                                        placeholder:text-[#606160]
                                        focus-visible:border-[#9a9b98]
                                        focus-visible:ring-0
                                    "
                                />

                                {errors.pass2 && (
                                    <p
                                        className="
                                            mt-1.5
                                            font-[Inter,sans-serif]
                                            text-[10px]
                                            text-[#9a9b98]
                                        "
                                    >
                                        {errors.pass2.message}
                                    </p>
                                )}
                            </div>

                            {/* Submit */}
                            <Button
                                type="submit"
                                disabled={register.isPending}
                                className="
                                    h-11 w-full rounded-none
                                    bg-[#f4f4f2]
                                    font-[Inter,sans-serif]
                                    text-[12px]
                                    font-semibold
                                    text-[#08090a]
                                    transition-opacity
                                    hover:bg-[#f4f4f2]
                                    hover:opacity-90
                                    disabled:cursor-not-allowed
                                    disabled:opacity-50
                                "
                            >
                                {register.isPending
                                    ? "Creating account..."
                                    : "Create account"}
                            </Button>

                            {/* Terms */}
                            <div
                                className="
                                    mt-4
                                    text-center
                                    font-[Inter,sans-serif]
                                    text-[9px]
                                    leading-4
                                    text-[#606160]
                                "
                            >
                                By creating an account, you agree to
                                our{" "}
                                <Button
                                    type="button"
                                    variant="ghost"
                                    className="
                                        h-auto rounded-none
                                        p-0
                                        font-[Inter,sans-serif]
                                        text-[9px]
                                        text-[#9a9b98]
                                        underline
                                        underline-offset-2
                                        hover:bg-transparent
                                        hover:text-[#f4f4f2]
                                    "
                                >
                                    Terms
                                </Button>{" "}
                                and{" "}
                                <Button
                                    type="button"
                                    variant="ghost"
                                    className="
                                        h-auto rounded-none
                                        p-0
                                        font-[Inter,sans-serif]
                                        text-[9px]
                                        text-[#9a9b98]
                                        underline
                                        underline-offset-2
                                        hover:bg-transparent
                                        hover:text-[#f4f4f2]
                                    "
                                >
                                    Privacy Policy
                                </Button>
                                .
                            </div>
                        </form>

                        {/* Divider */}
                        <div
                            className="
                                my-6 flex items-center gap-3
                            "
                        >
                            <div
                                className="
                                    h-px flex-1
                                    bg-[#2a2b2c]
                                "
                            />

                            <span
                                className="
                                    font-[JetBrains_Mono,monospace]
                                    text-[8px]
                                    uppercase
                                    tracking-[0.12em]
                                    text-[#606160]
                                "
                            >
                                or
                            </span>

                            <div
                                className="
                                    h-px flex-1
                                    bg-[#2a2b2c]
                                "
                            />
                        </div>

                        {/* Login switch */}
                        <div
                            className="
                                text-center
                                font-[Inter,sans-serif]
                                text-[11px]
                                text-[#606160]
                            "
                        >
                            Already have an account?

                            <Button
                                type="button"
                                variant="ghost"
                                onClick={goToLogin}
                                className="
                                    ml-1 h-auto rounded-none
                                    p-0
                                    font-[Inter,sans-serif]
                                    text-[11px]
                                    text-[#f4f4f2]
                                    hover:bg-transparent
                                    hover:text-[#f4f4f2]
                                    hover:underline
                                    hover:underline-offset-2
                                "
                            >
                                Log in
                            </Button>
                        </div>
                    </div>
                </section>
            </div>
        </AuthLayout>
    );
}
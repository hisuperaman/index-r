import { FormEvent, useState } from "react";
import { IAM } from "@/api";
import { onLoginSuccess } from "@/account";
import { GoogleLogin } from "@react-oauth/google";

export const Login = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            const token = await IAM.login({
                email,
                password,
            });

            onLoginSuccess(token);
        } catch (error) {
            console.error(error);
            setError("Invalid email or password.");
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSuccess = async (response: {
        code?: string;
    }) => {
        setError("");

        try {
            if (!response.code) {
                setError("Google login did not return an authorization code.");
                return;
            }

            const token = await IAM.googleCodeLogin(response.code);

            onLoginSuccess(token);
        } catch (error) {
            console.error("Google login error:", error);
            setError("Google login failed.");
        }
    };

    const handleGoogleError = () => {
        setError("Google login failed.");
    };

    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className="w-full max-w-md p-6">
                <h1 className="mb-6 text-3xl font-bold">
                    Login
                </h1>

                <form
                    onSubmit={handleSubmit}
                    className="space-y-4"
                >
                    <div>
                        <label
                            htmlFor="email"
                            className="mb-1 block"
                        >
                            Email
                        </label>

                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(event) =>
                                setEmail(event.target.value)
                            }
                            placeholder="Enter your email"
                            className="w-full rounded border p-2"
                            required
                        />
                    </div>

                    <div>
                        <label
                            htmlFor="password"
                            className="mb-1 block"
                        >
                            Password
                        </label>

                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(event.target.value)
                            }
                            placeholder="Enter your password"
                            className="w-full rounded border p-2"
                            required
                        />
                    </div>

                    {error && (
                        <p className="text-red-500">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full rounded bg-blue-600 p-2 text-white"
                    >
                        {loading
                            ? "Logging in..."
                            : "Login"}
                    </button>
                </form>

                <div className="my-4 text-center text-gray-500">
                    OR
                </div>

                <div className="flex justify-center">
                    <GoogleLogin
                        flow="auth-code"
                        onSuccess={handleGoogleSuccess}
                        onError={handleGoogleError}
                    />
                </div>
            </div>
        </div>
    );
};
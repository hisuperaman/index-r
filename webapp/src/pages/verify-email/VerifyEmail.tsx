import {useEffect, useRef, useState} from "react";
import {useNavigate, useParams} from "react-router";
import {CheckCircle2} from "lucide-react";

import {Button} from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import {Path} from "@/utils";
import {RoutePaths} from "@/enums";
import {toast} from "@/components/ui/toast";
import {useVerifyEmail} from "@/queries/user";
import {Spinner} from "@/components/ui/spinner";

export const VerifyEmail = () => {
    const navigate = useNavigate();
    const {key} = useParams();

    const [loading, setLoading] = useState(true);
    const calledRef = useRef(false);
    const verifyEmail = useVerifyEmail();

    useEffect(() => {
        if (calledRef.current) return;
        calledRef.current = true;

        if (!key) {
            toast.add({
                title: "Verification failed",
                description: "Invalid or expired link.",
                type: "error",
            });

            navigate(Path.getExactRoutePath(RoutePaths.empty));
            return;
        }

        verifyEmail.mutate(
            {key},
            {
                onSuccess: () => {
                    setLoading(false);
                },
                onError: () => {
                    toast.add({
                        title: "Verification failed",
                        description: "Invalid or expired link.",
                        type: "error",
                    });
                    navigate(Path.getExactRoutePath(RoutePaths.empty));
                },
            }
        );
    }, [key, navigate, verifyEmail]);

    return (
        <div className="flex min-h-[50vh] w-full items-center justify-center p-4">
            <Card className="w-full max-w-sm shadow-sm">
                {loading ? (
                    <CardContent className="flex flex-col items-center justify-center gap-4 py-12">
                        <Spinner/>
                        <p className="text-sm text-muted-foreground">
                            Verifying your email...
                        </p>
                    </CardContent>
                ) : (
                    <>
                        <CardHeader className="flex flex-col items-center gap-2 pb-6 text-center">
                            <div
                                className="mb-2 flex h-12 w-12 items-center justify-center rounded-full">
                                <CheckCircle2 size={48}/>
                            </div>
                            <CardTitle className="text-xl">
                                Email Verified
                            </CardTitle>
                            <CardDescription>
                                Your email address has been confirmed. You can now
                                sign in to your account.
                            </CardDescription>
                        </CardHeader>

                        <CardFooter>
                            <Button
                                className="w-full"
                                onClick={() =>
                                    navigate(Path.getExactRoutePath(RoutePaths.login))
                                }
                            >
                                Continue to sign in
                            </Button>
                        </CardFooter>
                    </>
                )}
            </Card>
        </div>
    );
}